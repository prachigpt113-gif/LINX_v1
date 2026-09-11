"""
Step 1: build semantic embeddings for the LINX course catalog, once, offline.
Run this locally (not inside Streamlit). It produces two files:
  - course_embeddings.npy   (one vector per course)
  - linx_catalog_merged.csv is read as-is; no changes made to it.

Why fastembed: no torch/CUDA dependency, much lighter than sentence-transformers,
fits comfortably inside Streamlit Community Cloud's free-tier resource limits.
First run downloads the model (~130MB) from HuggingFace and caches it locally.
"""

import numpy as np
import pandas as pd
from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"  # small, fast, strong for short technical phrases
CATALOG_PATH = "linx_catalog_merged.csv"
OUTPUT_EMBEDDINGS = "course_embeddings.npy"


def build_course_text(row):
    """
    What we embed matters as much as which model we use.
    Title carries the "what this course is called" signal; Skills carries
    the dense keyword surface. Difficulty/Duration are metadata, not meaning —
    leave them out of the embedded text so they don't dilute the vector.
    """
    title = str(row["Title"]).strip()
    skills = str(row["Skills"]).strip()
    return f"{title}. Skills: {skills}"


def main():
    df = pd.read_csv(CATALOG_PATH)
    print(f"Loaded {len(df)} courses.")

    texts = df.apply(build_course_text, axis=1).tolist()
    print("Example embedded text for row 0:")
    print(" ", texts[0][:200])

    print(f"\nLoading model {MODEL_NAME} (downloads on first run)...")
    model = TextEmbedding(model_name=MODEL_NAME)

    print("Embedding all courses...")
    embeddings = np.array(list(model.embed(texts)))
    print(f"Embeddings shape: {embeddings.shape}")

    np.save(OUTPUT_EMBEDDINGS, embeddings)
    print(f"Saved to {OUTPUT_EMBEDDINGS}")

    # ---- sanity check: does this actually beat keyword matching? ----
    print("\n--- Sanity check: 'UX Design' query ---")
    query_vec = np.array(list(model.embed(["UX Design"])))[0]

    sims = embeddings @ query_vec / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vec)
    )
    top5 = np.argsort(sims)[::-1][:5]
    for i in top5:
        print(f"  {sims[i]:.3f}  {df.iloc[i]['Title']}  |  {df.iloc[i]['Skills'][:80]}")


if __name__ == "__main__":
    main()