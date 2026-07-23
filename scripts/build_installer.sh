#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VERSION="$(tr -d '\r\n' < "$ROOT_DIR/VERSION")"
INSTALLER="$DIST_DIR/AnomalyMatrix-installer-v${VERSION}.run"
LEGACY_INSTALLER="$DIST_DIR/AnomalyMatrix-installer.run"
PAYLOAD="$ROOT_DIR/scripts/install.sh"

mkdir -p "$DIST_DIR"

cat > "$INSTALLER" <<'EOF'
#!/usr/bin/env bash
# AnomalyMatrix self-extracting installer
# Empfohlenes Host-OS: Ubuntu Server 24.04 LTS
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "[AnomalyMatrix] Bitte als root ausführen: sudo $0 ..." >&2
  exit 1
fi

MARKER="__ANOMALYMATRIX_PAYLOAD_BELOW__"
line_no=$(awk "/$MARKER/{print NR + 1; exit 0;}" "$0")
TMP_SCRIPT="$(mktemp)"
tail -n +"$line_no" "$0" > "$TMP_SCRIPT"
chmod +x "$TMP_SCRIPT"
exec "$TMP_SCRIPT" "$@"

__ANOMALYMATRIX_PAYLOAD_BELOW__
EOF

cat "$PAYLOAD" >> "$INSTALLER"
chmod +x "$INSTALLER"
cp -f "$INSTALLER" "$LEGACY_INSTALLER"

echo "Built installer: $INSTALLER"
echo "Legacy link:     $LEGACY_INSTALLER"
echo "Version:         $VERSION"
echo
echo "Run on a fresh Ubuntu Server 24.04 LTS:"
echo "  sudo $INSTALLER --host <SERVER-IP>"
