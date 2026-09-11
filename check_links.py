import pandas as pd, requests

df = pd.read_csv("linx_catalog_v1.csv")

def is_alive(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        return r.status_code < 400          # 200-ish = alive, 404/410 = dead
    except:
        return False

df["alive"] = df["url"].apply(is_alive)      # checks all 400 for you
dead = df[~df["alive"]]
print(f"{len(dead)} broken links")
df[df["alive"]].to_csv("linx_catalog_clean.csv", index=False)   # keep only working ones