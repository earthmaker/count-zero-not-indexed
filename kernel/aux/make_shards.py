# Auxiliary arm (pre-registration section 4-1) shard builder: cuts the permutation part2_order.tsv into 9-task slices and writes benchmark task files.
# Usage: python3 make_shards.py <output folder>  ->  gemma4paper_aux_s1.py ... s9.py
# push: kaggle benchmarks tasks push gemma4paper-aux-sN -f <output>/gemma4paper_aux_sN.py \
#         -d metric/gemma-4-developer-agent-wheelhouse -d earthmaker/gemma4paper-bundles --wait 600
#   -> after confirming that the generation log prints `skipped_non_gemma`
#   kaggle benchmarks tasks run gemma4paper-aux-sN -m gemma-4-31b-it --wait 43200
import os
import csv
import json
import sys
from pathlib import Path

ORDER = Path(os.environ.get("G4P_DERIVED", "derived")) / "part2_order.tsv"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
ids = [r["instance_id"] for r in csv.DictReader(open(ORDER), delimiter="\t")]
assert len(ids) == 81 and ids[0] == "fastapi_13786", "permutation file differs from the pre-registered version"
tpl = (Path(__file__).parent / "aux_template.py").read_text()
for k in range(9):
    sh = f"s{k + 1}"
    part = ids[9 * k: 9 * k + 9]
    (out / f"gemma4paper_aux_{sh}.py").write_text(tpl.replace("__SHARD__", sh).replace("__IDS__", json.dumps(part)))
    print(sh, part[0], part[-1])
