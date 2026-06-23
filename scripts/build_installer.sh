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
set -euo pipefail

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
cp "$INSTALLER" "$LEGACY_INSTALLER"

echo "Built installer: $INSTALLER"
echo "Version: $VERSION"
