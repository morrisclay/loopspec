import os, json, urllib.request, concurrent.futures as cf
D=os.path.dirname(os.path.abspath(__file__))
SPEC=open("/Users/morrisclay/Dev/uras/examples/customer_acquisition.v1.loop.yaml").read()
API=open(f"{D}/flue_api.md").read()
KEY=os.environ["OPENROUTER_API_KEY"]
PROMPT="""Here is a loop spec. Emit a working implementation for Flue (TypeScript).

Report anything the target cannot express rather than dropping it: end your output with a
section `## did not survive` listing each part of the spec you could not represent, and why.

Here is the Flue API you must use:

{api}

The spec:

```yaml
{spec}
```"""
MODELS=[("openai/gpt-5.6-sol","strong"),("anthropic/claude-opus-5","strong"),
        ("x-ai/grok-4.5","strong"),("google/gemini-2.5-pro","strong"),
        ("deepseek/deepseek-v3.2-exp","mid"),
        ("mistralai/mistral-small-3.2-24b-instruct","weak"),
        ("qwen/qwen3-8b","very weak"),("meta-llama/llama-3.1-8b-instruct","very weak")]
def call(m):
    b=json.dumps({"model":m,"max_tokens":16000,"messages":[{"role":"user",
        "content":PROMPT.format(api=API,spec=SPEC)}]}).encode()
    r=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=b,
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r,timeout=900) as f:
            j=json.load(f)["choices"][0]; return j["message"]["content"] or "", j.get("finish_reason")
    except Exception as e: return f"ERROR {e}","error"
with cf.ThreadPoolExecutor(8) as ex:
    for (m,tier),(t,fin) in zip(MODELS, ex.map(lambda x: call(x[0]), MODELS)):
        json.dump({"model":m,"tier":tier,"target":"flue","finish":fin,"text":t},
                  open(f"{D}/{m.split('/')[-1]}__flue.json","w"))
        print(f"{tier:10} {m:42} {fin:10} {len(t):6}")
