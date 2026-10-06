#!/usr/bin/env bash
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
APP_DIR="$HOME/.local/share/nebula-clock"

mkdir -p "$PREFIX/bin" "$APP_DIR"
rm -rf "$APP_DIR/nebula_clock"
cp -r nebula_clock "$APP_DIR/"

cat > "$PREFIX/bin/nebula-clock" <<EOF2
#!/usr/bin/env bash
exec python3 "$APP_DIR/nebula_clock/main.py" "\$@"
EOF2
chmod +x "$PREFIX/bin/nebula-clock"

echo "Installed to $PREFIX/bin/nebula-clock"

case ":$PATH:" in
  *":$PREFIX/bin:"*) ;;
  *)
    echo ""
    echo "Add this once if the command is not found:"
    echo "export PATH=\"$PREFIX/bin:\$PATH\""
    ;;
esac
