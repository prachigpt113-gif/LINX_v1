import streamlit as st
import pandas as pd

import requests

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScm5vJ8ZSAsLLyQE49dsAyAFjSDINvTSco8w1mPeijjMa2ezg/formResponse"

def log_event(event, email=""):
    """Fire-and-forget log to Google Form -> Sheet."""
    try:
        requests.post(FORM_URL, data={
            "entry.1040702399": event,                                    # event
            "entry.1408930542": str(st.session_state.get("current_field") or ""),   # field
            "entry.370929055":  str(st.session_state.get("current_level", "")),   # level
            "entry.194776135":  str(st.session_state.get("intent", "")),          # archetype
            "entry.198758842":  email,                                    # email
        }, timeout=3)
    except Exception:
        pass   # never let logging break the app


# ============================================================
# SECTION 1: SETUP
# ============================================================
# st.title("Let's ship LINX!")

df = pd.read_csv('linx_catalog_merged.csv')   # <-- use your cleaned (dead-links-removed) file

st.markdown("""
<style>
    /* dark canvas */
    .stApp { background-color: #0b0e14; color: #eef2f6; }

    /* chat bubbles */
    [data-testid="stChatMessage"] {
        background-color: #1f2a36;
        border-radius: 1.2rem;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }

    /* pill buttons */
    .stButton > button {
        background-color: #1e2b3b;
        color: #d6e3f5;
        border: 1px solid #33445a;
        border-radius: 60px;
        padding: 0.5rem 1.4rem;
        font-weight: 450;
        transition: 0.15s;
    }
    .stButton > button:hover {
        background-color: #2d4059;
        border-color: #5a74a0;
        color: white;
    }

    /* course card look on the recommendation blocks */
    h3 { color: #eaf1fc !important; }

    /* the coursera link button */
    .stLinkButton > a {
        background-color: #2f405b !important;
        border-radius: 60px !important;
        color: white !important;
        border: none !important;
    }
        /* user messages right-aligned */
    .stChatMessage:has(img[alt="user avatar"]) {
        flex-direction: row-reverse;
        background-color: #2b3b52 !important;
    }
</style>
""", unsafe_allow_html=True)


def clean_number(value):
    """'18K' -> 18000, '258,931' -> 258931, '910' -> 910"""
    text = str(value).replace(",", "")
    if "K" in text:
        return float(text.replace("K", "")) * 1000
    return float(text)


df["reviews"] = df["reviews"].apply(clean_number)
df["enrolled"] = df["enrolled"].apply(clean_number)

# level ladders
next_level = {"Beginner": "Intermediate", "Intermediate": "Advanced", "Advanced": "Advanced"}
beyond_level = {"Beginner": "Advanced", "Intermediate": "Advanced", "Advanced": "Advanced"}

AVATAR_LINX = "Linx_logo.png"   # your logo file in the same folder
AVATAR_USER = "user.png"


# ---------- keyword extraction ----------
def extract_keywords(field):
    """'I'm in data analytics field' -> ['data', 'analytics']"""
    stopwords = ['i', "i'm", 'im', 'am', 'in', 'the', 'a', 'an', 'of', 'for', 'on', 'at',
                 'to', 'from', 'by', 'with', 'field', 'role', 'work', 'job', 'currently',
                 'working', 'want', 'become', 'get', 'better']
    words = field.lower().replace(",", " ").split()
    return [w for w in words if w not in stopwords and len(w) >= 2]


# ---------- does a course match the field? (word-level, not sloppy substring) ----------
def field_matches(skills_text, keywords):
    skills = [s.strip().lower() for s in str(skills_text).split(",")][:8]   # ← only primary skills
    return any(
        kw in skill.split() or skill.startswith(kw)
        for skill in skills
        for kw in keywords
    )


# ---------- the recommender engine (honest: never fakes a match) ----------
def recommend(field, level):
    keywords = extract_keywords(field)
    if not keywords:
        st.warning("Tell me a field in a word or two — like 'finance' or 'design'.")
        return

    target  = level                    # courses AT their level
    stretch = next_level[level]        # one above

    # every course that genuinely matches the field, ANY level
    mask = df["Skills"].apply(lambda s: field_matches(s, keywords))
    field_pool = df[mask]

    # HONEST GUARD: field not in catalog -> say so, do NOT substitute random courses
    if len(field_pool) == 0:
        st.info(
            f"I don't have strong **{field}** courses in my catalog yet — "
            f"try a broader term like the general area (e.g. 'finance', 'data', 'design')."
        )
        return

    # ideal mix: 2 at target level + 1 at stretch level
    two_at = field_pool[field_pool["Difficulty"] == target].sort_values("enrolled", ascending=False).head(2)
    one_up = field_pool[field_pool["Difficulty"] == stretch].sort_values("enrolled", ascending=False).head(1)
    final3 = pd.concat([two_at, one_up]).drop_duplicates(subset=["url"])

    # widen ONLY within the field if short (keep the field, relax the level)
    if len(final3) < 3:
        already = final3["url"].tolist()
        extra = field_pool[~field_pool["url"].isin(already)].sort_values("enrolled", ascending=False).head(3 - len(final3))
        final3 = pd.concat([final3, extra])

    # render cards
    for _, course in final3.iterrows():
        st.subheader(course["Title"])
        st.caption(f"{course['Organization']} · {course['Difficulty']} · {course['Duration']}")
        skills_list = [s.strip() for s in course["Skills"].split(",")]
        matching = [s for s in skills_list if any(kw in s.lower() for kw in keywords)]
        specific_skill = matching[0] if matching else skills_list[0]
        if course["Difficulty"] == target:
            why = f"Because you're growing in **{field}**, this builds your **{specific_skill}** — a level up from where you are."
        else:
            why = f"And this one's a reach — it stretches your **{specific_skill}** further, for when you're ready."
        st.write(why)
        st.link_button("Open on Coursera ↗", course["url"])
        st.divider()


# ============================================================
# SECTION 2: STATE
# ============================================================
def init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

init("step", "welcome")
init("messages", [])
init("current_field", None)
init("current_level", None)
init("intent", None)
init("target_role", None)
init("target_level", None)
init("pivot_field", None)
init("urgency", None)


def add(role, text):
    avatar = AVATAR_LINX if role == "assistant" else AVATAR_USER
    st.session_state.messages.append({"role": role, "text": text, "avatar": avatar})


# ============================================================
# SECTION 3: RENDER CHAT HISTORY (every rerun)
# ============================================================
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=m["avatar"]):
        st.write(m["text"])


# ============================================================
# SECTION 4: THE FLOW (one step at a time)
# ============================================================

# --- welcome: greet + ask current field ---
if st.session_state.step == "welcome":
    c1, c2 = st.columns([1, 4])
    with c1:
        st.image("Linx_logo.png", width=100)
    with c2:
        st.title("WELCOME TO LINX")

    st.markdown("### Most learning platforms ask *what skill do you want?*")
    st.markdown("#### LINX asks a better question: *'Who are you becoming?'*")
    
    st.write("")  # spacer
    
    st.markdown(
        "Research on why people abandon courses found something interesting: "
        "the top reason to abandon wasn't losing motivation towards it, rather it was **never being clear, "
        "why that course mattered to them in the first place.**"
    )
    st.markdown(
    "So LINX starts with you ~ what you do now, where you're headed, and how urgently. "
    "Then it recommends courses that fit **where you're actually going**, and tells you why each one earns your time."
    )
    
    st.write("")
    st.caption("Three questions · About a minute · No sign-up")
    st.write("")

    if st.button("Let's begin"):
        log_event("started")
        add("assistant", "Hi — I'm LINX. Before we find your courses, tell me where you're starting from.")
        st.session_state.step = "field"
        st.rerun()



# if st.session_state.step == "welcome":
#     add("assistant", "Hi — I'm LINX. Before we find your courses, tell me where you're starting from.")
#     st.session_state.step = "field"
#     st.rerun()

# --- current field (text) ---
if st.session_state.step == "field":
    cf = st.chat_input("What field or role are you in right now?")
    if cf:
        st.session_state.current_field = cf
        add("user", cf)
        add("assistant", f"Got it — {cf}. And how would you rate your level there?")
        st.session_state.step = "current_level"
        st.rerun()

# --- current level (buttons) ---
if st.session_state.step == "current_level":
    c1, c2, c3 = st.columns(3)
    for col, lvl in [(c1, "Beginner"), (c2, "Intermediate"), (c3, "Advanced")]:
        if col.button(lvl, key=f"cl_{lvl}"):
            st.session_state.current_level = lvl
            add("user", lvl)
            add("assistant", "Which of these describes you the best?")
            st.session_state.step = "intent"
            st.rerun()

# --- intent (buttons) ---
if st.session_state.step == "intent":
    st.caption("Your answer helps me recommend learning that fits where you're headed.")
    if st.button("Moving toward a specific role", key="i_decided"):
        st.session_state.intent = "decided"; add("user", "Moving toward a specific role")
        log_event("intent_chosen")
        add("assistant", "Love it — what role are you moving toward?")
        st.session_state.step = "target_role"; st.rerun()
    if st.button("Get better at what I do", key="i_moving"):
        st.session_state.intent = "moving"; add("user", "Get better at what I do")
        log_event("intent_chosen")
        st.session_state.step = "show"; st.rerun()
    if st.button("Still figuring out my direction", key="i_figuring"):
        st.session_state.intent = "figuring"; add("user", "Still figuring out my direction")
        log_event("intent_chosen")
        add("assistant", "Do you want to grow in the field you're already in?")
        st.session_state.step = "figuring_fork"; st.rerun()

# --- figuring fork ---
if st.session_state.step == "figuring_fork":
    if st.button("Yes, same field", key="f_yes"):
        st.session_state.intent = "moving"; add("user", "Yes, same field")
        st.session_state.step = "show"; st.rerun()
    if st.button("No, I want to pivot", key="f_no"):
        st.session_state.intent = "pivot"; add("user", "No, I want to pivot")
        add("assistant", "What field or role are you interested in moving toward?")
        st.session_state.step = "pivot_field"; st.rerun()

# --- decided: target role (text) ---
if st.session_state.step == "target_role":
    tr = st.chat_input("What role are you moving toward?")
    if tr:
        st.session_state.target_role = tr
        add("user", tr)
        add("assistant", f"Great — what's your current level in {tr}?")
        st.session_state.step = "target_level"
        st.rerun()

# --- decided: target level (buttons) — gates the recommendation ---
if st.session_state.step == "target_level":
    c1, c2, c3 = st.columns(3)
    for col, lvl in [(c1, "Beginner"), (c2, "Intermediate"), (c3, "Advanced")]:
        if col.button(lvl, key=f"tl_{lvl}"):
            st.session_state.target_level = lvl
            add("user", lvl)
            st.session_state.step = "show"
            st.rerun()

# --- pivot: target field (text) ---
if st.session_state.step == "pivot_field":
    pf = st.chat_input("What field or role are you interested in moving toward?")
    if pf:
        st.session_state.pivot_field = pf
        add("user", pf)
        add("assistant", "What happens if you don't pursue this right now?")
        st.session_state.step = "pivot_urgency"
        st.rerun()

# --- pivot: urgency (buttons) ---
if st.session_state.step == "pivot_urgency":
    if st.button("I'd miss a real opportunity", key="u_search"):
        st.session_state.urgency = "searching"; add("user", "I'd miss a real opportunity")
        st.session_state.step = "show"; st.rerun()
    if st.button("Honestly, not much", key="u_drift1"):
        st.session_state.urgency = "drifting"; add("user", "Honestly, not much")
        st.session_state.step = "show"; st.rerun()
    if st.button("I'm not sure", key="u_drift2"):
        st.session_state.urgency = "drifting"; add("user", "I'm not sure")
        st.session_state.step = "show"; st.rerun()



# ============================================================
# SECTION 5: RECOMMENDATIONS
# ============================================================
if st.session_state.step == "show":
    if not st.session_state.get("logged_recs"):
        log_event("recommendations_shown")
        st.session_state.logged_recs = True

    # --- the recommendations FIRST ---
    if st.session_state.intent == "moving":
        st.write(f"Nice — let's deepen your **{st.session_state.current_field}**.")
        recommend(st.session_state.current_field, st.session_state.current_level)

    elif st.session_state.intent == "decided":
        st.write(f"Love it — here's what moves you toward **{st.session_state.target_role}**.")
        recommend(st.session_state.target_role, st.session_state.target_level)

    elif st.session_state.intent == "pivot" and st.session_state.urgency == "searching":
        st.write(f"That pull toward **{st.session_state.pivot_field}** is worth following. Here's where to start.")
        recommend(st.session_state.pivot_field, "Beginner")

    elif st.session_state.intent == "pivot" and st.session_state.urgency == "drifting":
        st.write(
            f"Going from **{st.session_state.current_field}** to **{st.session_state.pivot_field}** "
            f"is a real leap — no rush to commit the whole way today. A jump like this is easiest with a "
            f"guide, so it's worth talking to a few people already in {st.session_state.pivot_field} first. "
            f"In the meantime, here's momentum in **{st.session_state.current_field}**:"
        )
        recommend(st.session_state.current_field, st.session_state.current_level)

    # --- THEN the email ask (after the courses) ---
    st.divider()
    st.write("Want to hear when LINX gets smarter? Drop your email — I'm building this in the open.")
    email = st.text_input("your@email.com", key="email_capture", label_visibility="collapsed")
    if st.button("Keep me in the loop", key="email_btn"):
        if email:
            log_event("email_captured", email=email)
            st.success("Got it — thanks!")

    st.write("")
    st.divider()
    st.write("")
    if st.button("🔄 Start over", key="restart"):
        st.session_state.clear()
        st.rerun()

# ============================================================
# FOOTER (always visible)
# ============================================================

st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption(
        "Built by [Prachi Gupta](https://www.linkedin.com/in/prachi-gupta3/) · "
        "[The research behind it](https://medium.com/@prachigpt113/lost-in-the-learning-loop-91669eed5cb3) · "
        "[Code](https://github.com/prachigpt113-gif/linx_v1)")

