import os, json, urllib.request, concurrent.futures as cf
D = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(D, "..", ".."))
SPEC = open(os.path.join(R, "examples", "customer_acquisition.loop.yaml")).read()
KEY = os.environ["OPENROUTER_API_KEY"]

# THE ENTIRE COMPILE CONTRACT. No format document, no primitive catalog, no examples.
PROMPT = """Here is a loop spec. Emit a working implementation for {target}.

Report anything the target cannot express rather than dropping it: end your output with a
section `## did not survive` listing each part of the spec you could not represent, and why.

```yaml
{spec}
```"""

MODELS = [("openai/gpt-5.6-sol","strong"), ("anthropic/claude-opus-5","strong"),
          ("x-ai/grok-4.5","strong"), ("google/gemini-2.5-pro","strong"),
          ("deepseek/deepseek-v3.2-exp","mid"),
          ("mistralai/mistral-small-3.2-24b-instruct","weak"),
          ("qwen/qwen3-8b","very weak"),
          ("meta-llama/llama-3.1-8b-instruct","very weak")]
TARGETS = [("LangGraph (Python)","langgraph"), ("a Goose recipe (YAML)","goose"),
           ("Flue (TypeScript)","flue")]

def call(model, target):
    body = json.dumps({"model": model, "max_tokens": 16000, "messages":
        [{"role":"user","content":PROMPT.format(target=target, spec=SPEC)}]}).encode()
    r = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r, timeout=600) as f:
            j = json.load(f)["choices"][0]
            return j["message"]["content"] or "", j.get("finish_reason","?")
    except Exception as e:
        return f"ERROR {e}", "error"

jobs=[(m,tier,t,ts) for m,tier in MODELS for t,ts in TARGETS]
with cf.ThreadPoolExecutor(24) as ex:
    futs={ex.submit(call,m,t):(m,tier,t,ts) for m,tier,t,ts in jobs}
    for fu in cf.as_completed(futs):
        m,tier,t,ts=futs[fu]; out,fin=fu.result()
        meta={"model":m,"tier":tier,"target":ts,"finish":fin,"text":out}
        json.dump(meta, open(f"{D}/{m.split('/')[-1]}__{ts}.json","w"))
        print(f"{tier:10} {m:42} {ts:10} {fin:12} {len(out):6}")
