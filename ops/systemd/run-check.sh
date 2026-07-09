#!/usr/bin/env bash
# ops/systemd/run-check.sh — run the publish check and, on failure, raise a
# desktop notification. Invoked by publish-check.service; safe to run by hand.
#
# Deliberately no `set -e`: a non-zero exit from check-publish.ts is the signal
# we exist to handle, not a crash.
set -uo pipefail

REPO="${1:?usage: run-check.sh <repo-root> <node-bin>}"
NODE="${2:?usage: run-check.sh <repo-root> <node-bin>}"

cd "$REPO" || exit 1

out="$("$NODE" --experimental-strip-types web/scripts/check-publish.ts 2>&1)"
code=$?

printf '%s\n' "$out"
[ "$code" -eq 0 ] && exit 0

if command -v notify-send >/dev/null 2>&1; then
  notify-send --urgency=critical --app-name=bessavagner-page \
    'A post is due but not pushed' "$(printf '%s' "$out" | tail -n 6)"
fi

exit "$code"
