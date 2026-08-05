import os, json, urllib.request, concurrent.futures as cf, re
D=os.path.dirname(os.path.abspath(__file__)); R=os.path.abspath(os.path.join(D, "..", ".."))
REF=open(f"{R}/REFERENCE.md").read()
KEY=os.environ["OPENROUTER_API_KEY"]
HELD=[("lg_reflection","research/published_study/sources/lg_reflection.ipynb"),
      ("lg_self_rag","research/published_study/sources/lg_self_rag.ipynb"),
      ("oai_llm_as_a_judge","research/published_study/sources/oai_llm_as_a_judge.py"),
      ("lg_rewoo","research/published_study/sources/lg_rewoo.ipynb"),
      ("crew_self_eval","research/published_study/sources/crew_self_eval.py")]

def src(p):
    t=open(f"{R}/{p}").read()
    if p.endswith(".ipynb"):
        nb=json.loads(t)
        t="\n".join("".join(c["source"]) for c in nb["cells"])[:30000]
    return t[:30000]

PROMPT = """You are encoding an existing agent implementation into a loop specification format.

Here is the complete format reference:

{ref}

Rules:
- Encode ONLY what the source actually contains. If the code has no scoring of past
  predictions, omit `checked_by` — do not invent one. If no human appears in the code,
  leave `people` empty.
- `origin: ourselves` means this system's own action produced the data. `origin: outside`
  means something outside caused it to exist.
- Output ONLY the YAML, in a single ```yaml block. No commentary.

Here is the source:

```
{src}
```"""

def go(item):
    name,p = item
    b=json.dumps({"model":"openai/gpt-5.6-sol","max_tokens":6000,
        "messages":[{"role":"user","content":PROMPT.format(ref=REF, src=src(p))}]}).encode()
    r=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=b,
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r,timeout=900) as f:
            t=json.load(f)["choices"][0]["message"]["content"] or ""
    except Exception as e: t=f"ERROR {e}"
    m=re.search(r"```ya?ml\n(.*?)```", t, re.S)
    open(f"{D}/{name}.loop.yaml","w").write(m.group(1) if m else t)
    print(f"{name:24} {len(t):6}")
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(go, HELD))
