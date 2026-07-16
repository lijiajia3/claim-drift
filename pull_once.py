# -*- coding: utf-8 -*-
"""pull_once.py — 解耦的网络拉取:对种子论文只打【一个】limit=1000 的引用调用,
极耐心退避(60s),把 {year, ctx} 存到 contexts.json。与本地模型无关。"""
import json, time, urllib.request, urllib.error, sys
API = "https://api.semanticscholar.org/graph/v1"
PID = sys.argv[1] if len(sys.argv) > 1 else "38b041816f106d574ea5c34733c056a0687249f4"

def one_call(url, tries=8, wait=60):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-probe/0.2"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  [429] wait {wait}s ({t+1}/{tries})", flush=True); time.sleep(wait); continue
            raise
        except Exception as e:
            print(f"  [err] {e}; wait 20s", flush=True); time.sleep(20)
    raise RuntimeError("failed")

url = (f"{API}/paper/{PID}/citations?fields=contexts,citingPaper.year&limit=1000&offset=0")
print("[pull] single big call ...", flush=True)
d = one_call(url)
out = []
for it in d.get("data", []):
    yr = (it.get("citingPaper") or {}).get("year")
    for ctx in (it.get("contexts") or []):
        if yr and len(ctx) > 40:
            out.append({"year": yr, "ctx": ctx.strip()})
json.dump(out, open("contexts.json", "w"), ensure_ascii=False, indent=2)
print(f"[done] saved {len(out)} dated contexts to contexts.json", flush=True)
if out:
    ys = [c["year"] for c in out]
    print(f"  year range {min(ys)}-{max(ys)}", flush=True)
