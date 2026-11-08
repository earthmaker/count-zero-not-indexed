#!/bin/bash
# Gemma4Paper P1-P5 confirmatory + descriptive/exploratory analyses: the exact commands run on 2026-10-24. No GPU or network needed.
# Args: $1 = frozen script folder (confirm_p1p5.py, MANIFEST.txt, selftest.log), $2 = output folder
set -euo pipefail
FZ=${1:?frozen dir}; OUT=${2:?out dir}; HERE=$(cd "$(dirname "$0")" && pwd)
C=${G4P_CODER:-$(dirname "$0")/..}
D=${G4P_DERIVED:-derived}
R=${G4P_RUNS:-runs}
RUNS="$R/v6_confirm1/out $R/v8_confirm2/out $R/v9_confirm3/out $R/v10_confirm4/out $R/v11_confirm5/out"
mkdir -p "$OUT"
grep -q ae726b5fe004281ccbf083878ff33c723a29d321096a7ab2e6f1459dc8d08071 <(shasum -a 256 "$FZ/confirm_p1p5.py") || { echo "frozen script hash mismatch"; exit 2; }
python3 -I "$HERE/assemble_check.py" > "$OUT/assemble_check.out"
python3 -I "$FZ/confirm_p1p5.py" selftest --coder "$C" $RUNS > "$OUT/selftest_1024.log"
python3 -I "$FZ/confirm_p1p5.py" build --coder "$C" --derived "$D" --out "$OUT/rows.jsonl" $RUNS
python3 -I "$FZ/confirm_p1p5.py" analyze --derived "$D" --out "$OUT" "$OUT/rows.jsonl"
python3 -I "$HERE/descriptive_exploratory.py" "$FZ/confirm_p1p5.py" "$C" "$D" "$OUT/rows.jsonl" "$OUT/descriptive_exploratory.json" $RUNS > /dev/null
python3 -I "$HERE/exploratory_p3_window.py" "$FZ/confirm_p1p5.py" "$C" "$D" "$OUT/exploratory_p3_window.json" $RUNS > /dev/null
echo OK
