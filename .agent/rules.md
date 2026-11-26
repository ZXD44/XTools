# XTools — Project Rules (`.agent/rules.md`)

## 1. Naming & Identity
- Project name: **XTools** (always capital `X` and `T`).
- GitHub repository: `ZXD44/XTools`.
- Git author: `ZXD44`.

## 2. Directory Structure
- `bin/` — Executable entrypoints (`.bat`, compiled Rust `.exe`).
- `scripts/` — Automation scripts (Python, PowerShell, Bash).
- `assets/` — Icons (`xtools.ico`) and visual assets.
- `docs/` — Documentation, build prompts, and guides (`.md`).
- `.github/workflows/` — CI/CD and automated release pipelines.
- `.agent/` — Agent rules and project conventions.

## 3. Security & Installer Standards
- **No hardcoded secrets**: Never commit tokens, API keys, `.env`, or `agentx.md`.
- **Idempotency**: Installers (`install.ps1`, `install.sh`) must safely handle re-runs (prompt before overwrite/update).
- **Transparency**: Always print the download URL before fetching.
- **Integrity**: Always verify `SHA256` checksums before extracting archives.
- **No remote pipe execution**: Download release archives to a temp file and verify before extracting.

## 4. Deploy & Release Workflow
- Commit and push changes to `main`.
- Tag a semantic version (`git tag vX.Y.Z && git push origin vX.Y.Z`).
- `.github/workflows/release.yml` automatically packages `bin/`, `scripts/`, `assets/` into `xtools.zip` + `xtools.zip.sha256` and publishes a GitHub Release.
