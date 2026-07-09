# Publish check timer

A `--user` systemd timer that runs `web/scripts/check-publish.ts` every morning at
09:00 local and raises a desktop notification when a post whose `pubDate` has
passed is not on `origin/main` — untracked, or committed but never pushed.

This check cannot live in CI. A GitHub Action runs against a fresh checkout of the
remote, which by definition does not contain an uncommitted file. A `pre-push` hook
is no better: the failure mode is never pushing at all.

## Install

    ./ops/systemd/install.sh

The units are templates. `install.sh` substitutes this checkout's absolute path and
your `node` binary, then writes the result to `~/.config/systemd/user/`. Re-run it
after moving the repo or switching node versions.

## Status

    systemctl --user list-timers publish-check.timer --all
    systemctl --user start publish-check.service   # run it now
    journalctl --user -u publish-check.service -n 20

`Persistent=true` means a run missed while the machine was off fires at next login.

## Uninstall

    systemctl --user disable --now publish-check.timer
    rm ~/.config/systemd/user/publish-check.{service,timer}
    systemctl --user daemon-reload

## Run the check without systemd

    node --experimental-strip-types web/scripts/check-publish.ts
