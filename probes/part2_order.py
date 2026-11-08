# Part 2 run order: a random permutation of the 81 exposed+covered tasks (seed 20261005). Pre-registration section 4.
import os
import csv, random, hashlib
D = os.environ.get("G4P_DERIVED", "derived")
rows = [r for r in csv.DictReader(open(D + '/part2_strata.tsv'), delimiter='\t') if r['stratum'] in ('exposed', 'covered')]
rows.sort(key=lambda r: r['instance_id'])
random.Random(20261005).shuffle(rows)
with open(D + '/part2_order.tsv', 'w') as f:
    f.write('order\tinstance_id\trepo\tstratum\n')
    for i, r in enumerate(rows, 1):
        f.write(f"{i}\t{r['instance_id']}\t{r['repo']}\t{r['stratum']}\n")
print(len(rows), hashlib.sha256(open(D + '/part2_order.tsv', 'rb').read()).hexdigest()[:16])
print([r['instance_id'] for r in rows[:5]])
