import os, re, glob, json
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
CHECKS = {
  "cadence_weekly":   r"weekly|604800|\bweek\b",
  "sig_stripe":       r"stripe",
  "sig_ad_platform":  r"ad[_ ]?platform",
  "sig_interviews":   r"customer[_ ]?interview",
  "sig_board":        r"board[_ ]?sentiment",
  "act_budget":       r"increase[_ ]?budget",
  "act_pricing":      r"change[_ ]?pricing",
  "act_exit":         r"exit[_ ]?channel",
  "est_pmf":          r"product[_ ]?market[_ ]?fit|\bpmf\b",
  "est_saturation":   r"channel[_ ]?saturation",
  "target_cac_400":   r"400",
  "target_payback":   r"payback",
  "party_founder":    r"founder",
  "party_investor":   r"investor",
  "constraint_runway":r"runway",
  "APPROVAL_GATE":    r"approv|human[_ ]?in[_ ]?the[_ ]?loop|interrupt|escalat",
  "reversibility":    r"irreversib|reversib|costly",
  "reports_gaps":     r"did not survive",
}
rows=[]
for f in sorted(glob.glob(f"{D}/*.md")):
    raw = open(f).read()
    head, _, t = raw.partition("-->")
    m = dict(kv.split(": ", 1) for kv in
             head.replace("<!--", "").strip().split("  ") if ": " in kv)
    m["text"] = t
    if m["finish"]!="stop" or len(t)<400:            # truncated / errored: EXCLUDED, not scored
        rows.append((m,None,None)); continue
    h={k:bool(re.search(v,t,re.I)) for k,v in CHECKS.items()}
    rows.append((m,sum(h.values())/len(h),h))

print(f"{'tier':10} {'model':40} {'tgt':10} {'fidelity':>8}  gate  gaps")
print("-"*84)
for m,s,h in sorted(rows,key=lambda r:(["very weak","weak","mid","strong"].index(r[0]["tier"]),r[0]["model"])):
    if s is None:
        print(f"{m['tier']:10} {m['model'].split('/')[-1]:40} {m['target']:10} {'EXCLUDED':>8}  ({m['finish']})")
    else:
        print(f"{m['tier']:10} {m['model'].split('/')[-1]:40} {m['target']:10} {s:8.2f}  "
              f"{'YES' if h['APPROVAL_GATE'] else ' no':4}  {'yes' if h['reports_gaps'] else ' no'}")
agg={}
for m,s,h in rows:
    if s is not None: agg.setdefault(m["tier"],[]).append(s)
print("\nMEAN FIDELITY BY CAPABILITY TIER — the SLOPE is the result")
for k in ["very weak","weak","mid","strong"]:
    if k in agg: print(f"  {k:10} {sum(agg[k])/len(agg[k]):.3f}  (n={len(agg[k])})")
miss={}
scored=[r for r in rows if r[1] is not None]
for m,s,h in scored:
    for k,v in h.items():
        if not v: miss[k]=miss.get(k,0)+1
print(f"\nMOST-DROPPED, out of {len(scored)} scored compilations")
for k,v in sorted(miss.items(),key=lambda x:-x[1])[:8]: print(f"  {v:2}  {k}")
gate=[h['APPROVAL_GATE'] for m,s,h in scored]
print(f"\napproval gate preserved: {sum(gate)}/{len(gate)}")
