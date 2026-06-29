"""app/api/routes/vouchers.py"""

import os
import json
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.dependencies.current_user import get_current_user
from app.models.user import User

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])

PROMPTS = {
    "yape": """You are extracting transaction data from a Yape (Peruvian mobile payment app) voucher screenshot.
The voucher typically shows: '¡Yapeaste!' header, amount as 'S/ X', recipient name, date/time, a concept/description in a highlighted box, and a transaction number.

Extract these fields:
- amount: the numeric amount only (e.g., 6, 25.50) — no currency symbol
- description: the concept or purpose shown in the highlighted/shaded box (e.g., "Arbitraje", "Almuerzo")
- date: the transaction date in YYYY-MM-DD format
- recipient: the recipient name as shown (may be partially masked with *)
- currency_code: always "PEN" for Yape

Return ONLY a valid JSON object with these exact keys: amount, description, date, recipient, currency_code.
Use null for any field you cannot find. Do not include any explanation or markdown.""",

    "plin": """You are extracting transaction data from a Plin (Peruvian mobile payment app) voucher screenshot.

Extract these fields:
- amount: the numeric amount only (decimal number, no currency symbol)
- description: the description or concept of the payment
- date: the transaction date in YYYY-MM-DD format
- recipient: the recipient name shown on the voucher
- currency_code: "PEN"

Return ONLY a valid JSON object with these exact keys: amount, description, date, recipient, currency_code.
Use null for any field you cannot find. Do not include any explanation or markdown.""",

    "generic": """You are extracting transaction data from a payment voucher or receipt screenshot.

Extract these fields:
- amount: the numeric amount paid (decimal number, no currency symbol)
- description: the description, concept, or purpose of the payment
- date: the transaction date in YYYY-MM-DD format
- recipient: the recipient or merchant name
- currency_code: the ISO 4217 currency code (e.g., "PEN", "USD")

Return ONLY a valid JSON object with these exact keys: amount, description, date, recipient, currency_code.
Use null for any field you cannot find. Do not include any explanation or markdown.""",
}


class VoucherParseRequest(BaseModel):
    image_base64: str
    image_mime_type: str = "image/jpeg"
    service_type: str = "generic"


class VoucherParseResponse(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[str] = None
    recipient: Optional[str] = None
    currency_code: Optional[str] = None


@router.post("/parse", response_model=VoucherParseResponse)
def parse_voucher(
    request: VoucherParseRequest,
    current_user: User = Depends(get_current_user),
):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    prompt = PROMPTS.get(request.service_type, PROMPTS["generic"])

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": request.image_mime_type,
                            "data": request.image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    # Claude might wrap JSON in markdown code fences; strip them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Could not parse AI response: {raw}")

    return VoucherParseResponse(
        amount=float(data["amount"]) if data.get("amount") is not None else None,
        description=data.get("description"),
        date=data.get("date"),
        recipient=data.get("recipient"),
        currency_code=data.get("currency_code"),
    )
