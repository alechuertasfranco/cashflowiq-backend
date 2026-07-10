# releases/

Holds the published APK files and `version.json` that `GET /app/version`
reads. This directory is a Docker volume mount (`docker-compose.yml`), so its
contents live on the NAS filesystem and are **not** part of the git repo or
the deploy sync (see `.claude/commands/deploy-backend.md`, which excludes
`releases/` from the rsync so a deploy never wipes a published release).

`version.json` shape (see `version.json.example`):

```json
{
  "latest_version": "1.2.0",
  "latest_build_number": 12,
  "min_build_number": 1,
  "apk_url": "https://35-188-52-241.sslip.io/releases/cashflowiq-1.2.0.apk",
  "release_notes": "Texto corto que se muestra en el diálogo de actualización.",
  "force_update": false
}
```

- `latest_build_number` is compared against the installed app's
  `pubspec.yaml` build number (the `+N` after the version).
- `min_build_number`: if the installed build is older than this, the update
  dialog is shown as non-dismissible (`force_update` computed client-side
  from this, independent of the `force_update` field).
- `force_update`: explicit override to force the update regardless of
  `min_build_number` (e.g. a critical hotfix).

Publish a new release with `scripts/release-apk.sh` — it builds the APK,
uploads it here, and writes `version.json` in one step.
