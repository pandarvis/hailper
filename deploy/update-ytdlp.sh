#!/usr/bin/env bash
# Keep yt-dlp fresh (YouTube breaks old versions).
set -e
"$HOME/hailper/.venv/bin/pip" install --upgrade yt-dlp
