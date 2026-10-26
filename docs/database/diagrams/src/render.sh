#!/bin/zsh
# Рендер SVG → PNG через headless Edge.
# Использование: W H берутся из вывода python3 fig13.py
#   ./render.sh fig13 W H 1.25
EDGE="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
d=$(pwd)
"$EDGE" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$(mktemp -d)" --force-device-scale-factor=$4 --window-size=$2,$3 --screenshot="$d/$1.png" "file://$d/$1.svg" >/dev/null 2>&1
