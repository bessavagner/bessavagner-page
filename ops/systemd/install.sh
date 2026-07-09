#!/usr/bin/env bash
# ops/systemd/install.sh — install and enable the daily publish check as a
# --user timer. Templates this checkout's path and node binary into the units,
# so nothing machine-specific is committed. Re-run after moving the repo or
# switching node versions.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NODE="$(command -v node)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

echo "repo: $REPO"
echo "node: $NODE"

mkdir -p "$UNIT_DIR"
for unit in publish-check.service publish-check.timer; do
  sed -e "s|@REPO@|$REPO|g" -e "s|@NODE@|$NODE|g" \
    "$REPO/ops/systemd/$unit.in" > "$UNIT_DIR/$unit"
  echo "wrote $UNIT_DIR/$unit"
done

chmod +x "$REPO/ops/systemd/run-check.sh"

systemctl --user daemon-reload
systemctl --user enable --now publish-check.timer
systemctl --user list-timers publish-check.timer --all
