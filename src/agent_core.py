import requests, json, yaml, os, re
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

with open("config/settings.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

def search_web(query, max_results=3):
    with DDGS() as ddgs:
        hits = ddgs.text(query, max_results=max_results)
        out = []
        for r in hits:
            body = r.get("body") or r.get("snippet") or r.get("title") or ""
            out.append(body)
        return out

def local_llm(prompt):
    url = cfg["llm"]["base_url"]
    data = {"model": cfg["llm"]["model"], "prompt": prompt, "stream": False}
    resp = requests.post(url, json=data)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("response", "")

def summarize(topic):
    results = search_web(topic)
    context = "\n".join(results)
    with open("config/prompt_researcher.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    full_prompt = (
        f"{system_prompt}\n\n"
        f"Topic: {topic}\n\n"
        f"Context sources (bullets, may contain noise):\n{context}\n\n"
        f"Remember to return a single JSON object per the schema."
    )

    print("=== Generating summary... ===")
    summary = local_llm(full_prompt)
    print(summary)

    # --- Save output as JSON file ---
    os.makedirs("results", exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    with open(f"results/{safe_name}.json", "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"\n✅ Saved to results/{safe_name}.json")

    return summary

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    summarize(topic)
