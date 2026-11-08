# Part 2 power: simulation based on exact tests. Results were copied into the pre-registration.
import numpy as np
from scipy.stats import fisher_exact, binomtest
rng = np.random.default_rng(20261005); R = 2000

def mdd_two(n1, n0, p0, alpha=.05, pw=.8):
    # exposed n1 vs covered n0, binary task-level outcome, one-sided Fisher. Smallest p1-p0 reaching power pw
    for d in np.arange(.05, .80, .01):
        p1 = min(p0 + d, .99)
        x1 = rng.binomial(n1, p1, R); x0 = rng.binomial(n0, p0, R)
        hit = np.mean([fisher_exact([[a, n1 - a], [b, n0 - b]], alternative='greater')[1] < alpha for a, b in zip(x1, x0)])
        if hit >= pw:
            return round(float(d), 2)
    return None

def mcnemar_power(n, pb, pc, alpha=.05):
    # n paired tasks, discordance probabilities pb (only B resolves) and pc (only A resolves), two-sided exact McNemar
    out = []
    for _ in range(R):
        b, c, _r = rng.multinomial(n, [pb, pc, 1 - pb - pc])
        out.append(b + c > 0 and binomtest(int(b), int(b + c), .5).pvalue < alpha)
    return float(np.mean(out))

print("## exposed vs covered, 1 run per task, one-sided Fisher a=.05, smallest detectable difference at power .8")
for n1, n0 in ((47, 34), (20, 27), (23, 5)):
    print(f" n={n1}/{n0}:", {p0: mdd_two(n1, n0, p0) for p0 in (.1, .2, .3, .5)})
print("## A vs B paired McNemar (resolved or not)")
for n in (40, 81, 109):
    for pb, pc in ((.10, .03), (.08, .04), (.06, .03), (.15, .05)):
        print(f" n={n:3d} b={pb:.2f} c={pc:.2f}: power={mcnemar_power(n, pb, pc):.2f}")
