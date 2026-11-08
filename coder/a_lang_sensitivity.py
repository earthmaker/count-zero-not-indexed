"""A_lang exploratory sensitivity: broadens the ABSENCE lexicon of the frozen judge 0.2 and recounts A_lang after E_empty (the main analysis keeps 0.2 unchanged).
Decided 2026-10-11: "0.2 main analysis + broadened-lexicon sensitivity". The auxiliary v3 traces gave the positive control: 0.2 missed "`X` didn't return anything".
Usage: python3 coder/a_lang_sensitivity.py <trace.json> ...   (run from the release root)"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import trace_events as T
files=sys.argv[1:]
def run():
    tot=[0,0]
    for f in files:
        seq=T.load_steps(json.load(open(f)))
        for e in T.code_events(seq,None,3):
            if e['event']=='E_empty': tot[0]+=1; tot[1]+=e['A_lang']
    return tot
print('0.2  E_empty, A_lang =',run())
T.ABSENCE=re.compile(T.ABSENCE.pattern+r"|(did ?n[o']t|did not) (return|find|yield|show) (anything|any|results?)|still nothing|returned (an )?empty|(came|comes) back empty",re.I)
print('alt  E_empty, A_lang =',run())
