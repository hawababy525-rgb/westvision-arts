#!/usr/bin/env bash
# WESTVISION ARTS - kuanza (Mac / Linux)
cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "        WESTVISION ARTS - Kuanza"
echo "========================================"

# Tafuta python
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "[KOSA] Python haijapatikana. Sakinisha Python 3 kwanza."
  exit 1
fi

# Sakinisha mahitaji mara ya kwanza
if [ ! -f ".deps_done" ]; then
  echo "Inasakinisha mahitaji... subiri kidogo."
  "$PY" -m pip install -q -r requirements.txt && touch .deps_done
fi

echo
echo "App inaanza... Fungua browser: http://127.0.0.1:5000"
echo "Usifunge dirisha hili. Kuzima app: bonyeza CTRL + C."
echo

# Jaribu kufungua browser yenyewe (ikipatikana)
( sleep 4
  if command -v xdg-open >/dev/null 2>&1; then xdg-open http://127.0.0.1:5000
  elif command -v open >/dev/null 2>&1; then open http://127.0.0.1:5000
  fi ) &

"$PY" app.py
