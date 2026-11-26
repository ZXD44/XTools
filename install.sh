#!/usr/bin/env bash
# ==============================================================================
# XTools macOS/Linux Bootstrapper (install.sh)
# Downloads the latest XTools release, verifies SHA256, extracts to
# ~/.local/share/Xtools, and adds ~/.local/share/Xtools/bin to shell PATH.
# ==============================================================================

set -euo pipefail

# ==============================================================================
# 1. Configuration & Colors
# ==============================================================================
REPO="${XTOOLS_REPO:-ZXD44/XTools}"
INSTALL_DIR="${HOME}/.local/share/XTools"
BIN_DIR="${INSTALL_DIR}/bin"
if [ "${XTOOLS_CHANNEL:-stable}" = "dev" ]; then
    API_URL="https://api.github.com/repos/${REPO}/releases/tags/dev"
else
    API_URL="https://api.github.com/repos/${REPO}/releases/latest"
fi
TMP_DIR="$(mktemp -d)"

CYAN='\033[0;96m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
RED='\033[0;91m'
DIM='\033[0;90m'
RESET='\033[0m'

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# ==============================================================================
# 2. Banner
# ==============================================================================
printf "${CYAN}"
cat << 'EOF'
 __  _______ ___   ___  _     ____  
 \ \/ /_   _/ _ \ / _ \| |   / ___| 
  \  /  | || | | | | | | |   \___ \ 
  /  \  | || |_| | |_| | |___ ___) |
 /_/\_\ |_| \___/ \___/|_____|____/ 
EOF
printf "${RESET}${DIM}  Unix Installer | Repo: ${REPO}${RESET}\n\n"

# ==============================================================================
# 3. Idempotency Check
# ==============================================================================
if [ -d "$INSTALL_DIR" ]; then
    printf "${YELLOW}[!] XTools is already installed at: ${INSTALL_DIR}${RESET}\n"
    read -r -p "    Overwrite/Update existing installation? [y/N] " choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        printf "${DIM}Installation cancelled by user.${RESET}\n"
        exit 0
    fi
fi

# ==============================================================================
# 4. Dependency Check
# ==============================================================================
for cmd in curl unzip; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        printf "${RED}[ERROR] Required command '${cmd}' not found. Please install it first.${RESET}\n"
        exit 1
    fi
done

if command -v python3 >/dev/null 2>&1; then
    printf "${GREEN}[OK]${RESET} Detected $(python3 --version)\n"
else
    printf "${YELLOW}[!] python3 not found. Python scripts require Python 3: https://www.python.org/downloads/${RESET}\n"
fi

# ==============================================================================
# 5. Fetch Release & Download
# ==============================================================================
printf "${CYAN}[1/4]${RESET} Fetching release metadata from: ${API_URL}\n"
RELEASE_JSON="$(curl -fsSL "$API_URL")"

ZIP_URL="$(printf '%s' "$RELEASE_JSON" | grep -oE '"browser_download_url":\s*"[^"]*xtools\.zip"' | head -n1 | cut -d'"' -f4)"
SHA_URL="$(printf '%s' "$RELEASE_JSON" | grep -oE '"browser_download_url":\s*"[^"]*xtools\.zip\.sha256"' | head -n1 | cut -d'"' -f4 || true)"

if [ -z "$ZIP_URL" ]; then
    printf "${RED}[ERROR] Asset 'xtools.zip' not found in latest release for ${REPO}.${RESET}\n"
    exit 1
fi

ZIP_PATH="${TMP_DIR}/xtools.zip"
printf "${CYAN}[2/4]${RESET} Downloading from: ${ZIP_URL}\n"
curl -fL --progress-bar "$ZIP_URL" -o "$ZIP_PATH"

# ==============================================================================
# 6. SHA256 Checksum Verification
# ==============================================================================
if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL_HASH="$(sha256sum "$ZIP_PATH" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
    ACTUAL_HASH="$(shasum -a 256 "$ZIP_PATH" | awk '{print $1}')"
else
    ACTUAL_HASH=""
fi

if [ -n "$SHA_URL" ] && [ -n "$ACTUAL_HASH" ]; then
    printf "${DIM}    Verifying against ${SHA_URL}...${RESET}\n"
    EXPECTED_HASH="$(curl -fsSL "$SHA_URL" | awk '{print $1}')"
    if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
        printf "${RED}[ERROR] SHA256 mismatch! Expected: ${EXPECTED_HASH}, Got: ${ACTUAL_HASH}${RESET}\n"
        exit 1
    fi
    printf "${GREEN}[OK]${RESET} SHA256 verified (${ACTUAL_HASH})\n"
fi

# ==============================================================================
# 7. Extract to ~/.local/share/Xtools
# ==============================================================================
printf "${CYAN}[3/4]${RESET} Extracting to: ${INSTALL_DIR}\n"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
unzip -q "$ZIP_PATH" -d "$INSTALL_DIR"

# ==============================================================================
# 8. Add ~/.local/share/Xtools/bin to Shell PATH
# ==============================================================================
printf "${CYAN}[4/4]${RESET} Updating shell PATH...\n"
SHELL_NAME="$(basename "${SHELL:-bash}")"
case "$SHELL_NAME" in
    zsh)  RC_FILE="${HOME}/.zshrc" ;;
    bash) RC_FILE="${HOME}/.bashrc" ;;
    *)    RC_FILE="${HOME}/.profile" ;;
esac

PATH_LINE="export PATH=\"${BIN_DIR}:\$PATH\""
if [ -f "$RC_FILE" ] && grep -Fq "$BIN_DIR" "$RC_FILE"; then
    printf "${DIM}    ${BIN_DIR} is already in ${RC_FILE}.${RESET}\n"
else
    printf "\n# XTools\n%s\n" "$PATH_LINE" >> "$RC_FILE"
    printf "${GREEN}[OK]${RESET} Added ${BIN_DIR} to ${RC_FILE}\n"
fi

printf "\n${GREEN}========================================${RESET}\n"
printf "${GREEN}  XTools installed successfully!${RESET}\n"
printf "${GREEN}  Location: ${INSTALL_DIR}${RESET}\n"
printf "${GREEN}  Run: source ${RC_FILE}${RESET}\n"
printf "${GREEN}========================================${RESET}\n\n"
