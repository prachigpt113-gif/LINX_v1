# LINX_v1

# LINX — an identity-first course recommender

Most learning platforms ask *"what skill do you want?"* — a question that assumes you already know who you're becoming. LINX asks a better one first.

**[Try it live →](YOUR_STREAMLIT_URL_HERE)**

---

## Why it exists

I ran a mixed-methods study (n=20 survey, n=4 interviews) on why people abandon online courses. The finding that surprised me: the top reason wasn't losing motivation. It was **never being clear why that course mattered to them in the first place.**

Four learner archetypes emerged — *Decided, Moving, Searching, Drifting* — and what separated finishers from quitters wasn't discipline. It was whether they'd already answered a quieter question: **who am I becoming by choosing this?**

LINX puts that question before the course catalog.

[Read the full research →](https://medium.com/@prachigpt113/lost-in-the-learning-loop-91669eed5cb3)  
[Read the design case study →](https://medium.com/@prachigpt113/what-if-linkedin-learning-asked-a-better-question-299691e74a0b)

## How it works

1. **Benchmark** — what field are you in, and at what level?
2. **Intent** — where's your head at? (moving toward a role / getting better / still figuring it out)
3. **Diagnose** — the unsettled path gets a short conversation to sort *Searching* from *Drifting*
4. **Recommend** — 2 courses at your level + 1 stretch, each with a grounded reason for *why this one*

## The engine

- **Catalog:** 1,088 courses (Coursera + edX), cleaned, deduped, with every outbound link programmatically validated
- **Matching:** keyword extraction → word-level skill matching against the course's primary skills
- **Ranking:** enrolment-weighted, level-aware (2 at-level + 1 stretch)
- **Honesty guard:** if a field genuinely isn't in the catalog, LINX says so rather than padding with irrelevant courses

## Known limitations (and what's next)

Keyword matching struggles on narrow fields — searching *"Quant Finance"* surfaces general finance courses because the catalog is thin there, and prose-derived skills occasionally produce false positives.

**Next:** embedding-based semantic retrieval (RAG) + LLM-generated explanations, so LINX matches on *meaning* rather than keyword overlap.

## Stack

Python · pandas · Streamlit

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

Built by [Prachi Gupta](https://www.linkedin.com/in/prachi-gupta3/)
