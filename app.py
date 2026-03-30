import os
import re
import requests
import streamlit as st
from datetime import datetime
from urllib.parse import urlparse

st.set_page_config(page_title="Empleos Remotos AR", page_icon="💼", layout="wide")

# ================= CONFIG =================
GOOGLE_API_KEY = "AIzaSyDswZxrBOdaz6jZnByoEjwOcvzU7hJ6bQw"
GOOGLE_CX = "d48625c20c6824976"
DATE_RESTRICT = "d3"
LANGUAGE = "lang_es"
COUNTRY = "ar"

# ================= DATA =================
ROLES = [
    "asistente virtual", "administrativo remoto", "data entry",
    "customer support", "chat support", "email support",
    "back office", "atención al cliente remoto"
]

FAST_APPLY = [
    "postúlate", "postulate", "apply now", "easy apply",
    "quick apply", "sin experiencia", "entry level", "junior"
]

EXCLUDE = [
    "presencial", "híbrido", "hybrid", "onsite",
    "senior", "manager", "director", "developer", "engineer"
]

SOURCES = {
    "Todas": [],
    "Instagram": ["instagram.com"],
    "Facebook": ["facebook.com"],
    "Instagram + Facebook": ["instagram.com", "facebook.com"]
}

# ================= HELPERS =================
def clean(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()

def domain(url):
    return urlparse(url).netloc.replace("www.", "")

def contains(text, words):
    text = text.lower()
    return any(w.lower() in text for w in words)

def is_valid(text):
    return (
        contains(text, ["remoto", "remote"])
        and contains(text, ["argentina"])
        and not contains(text, EXCLUDE)
    )

def score(text):
    text = text.lower()
    s = 0

    for r in ROLES:
        if r in text: s += 15

    for f in FAST_APPLY:
        if f in text: s += 20

    if "sin experiencia" in text: s += 25
    if "remoto" in text: s += 20
    if "argentina" in text: s += 15

    return s

def build_query(domains):
    roles = " OR ".join([f'"{r}"' for r in ROLES])
    fast = " OR ".join([f'"{f}"' for f in FAST_APPLY])

    q = f"""
    ({roles})
    ("remoto" OR "remote" OR "work from home")
    ("Argentina")
    ({fast})
    """

    if domains:
        sites = " OR ".join([f"site:{d}" for d in domains])
        q += f" ({sites})"

    for e in EXCLUDE:
        q += f' -"{e}"'

    return q

def search(query, limit):
    url = "https://customsearch.googleapis.com/customsearch/v1"
    results = []
    start = 1

    while len(results) < limit:
        res = requests.get(url, params={
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query,
            "num": 10,
            "start": start,
            "gl": COUNTRY,
            "lr": LANGUAGE,
            "dateRestrict": DATE_RESTRICT
        })

        data = res.json()
        items = data.get("items", [])
        if not items: break

        results += items
        start += 10

    return results[:limit]

def process(items):
    out = []
    seen = set()

    for i in items:
        link = i.get("link")
        if not link or link in seen: continue
        seen.add(link)

        title = clean(i.get("title"))
        snippet = clean(i.get("snippet"))
        text = f"{title} {snippet}"

        if not is_valid(text): continue

        sc = score(text)

        if sc < 40: continue

        out.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "domain": domain(link),
            "score": sc
        })

    return sorted(out, key=lambda x: x["score"], reverse=True)

# ================= UI =================
st.title("💼 Empleos Remotos Argentina PRO")

with st.sidebar:
    source = st.selectbox("Fuente", list(SOURCES.keys()))
    cantidad = st.slider("Cantidad", 10, 40, 20)

if "favoritos" not in st.session_state:
    st.session_state.favoritos = []

if st.button("🔎 Buscar empleos", use_container_width=True):

    if not GOOGLE_API_KEY or not GOOGLE_CX:
        st.error("Faltan API KEY")
        st.stop()

    query = build_query(SOURCES[source])

    st.info("Buscando empleos remotos recientes (últimas 72hs)...")

    items = search(query, cantidad)
    results = process(items)

    st.success(f"{len(results)} encontrados")

    if not results:
        st.warning("No hay resultados buenos ahora mismo")
    else:

        # TOP FACILES
        st.subheader("🟢 Más fáciles para entrar")
        for r in results[:5]:
            st.markdown(f"- [{r['title']}]({r['link']})")

        st.divider()

        # TODOS
        for r in results:
            with st.container(border=True):
                c1, c2 = st.columns([4,1])

                with c1:
                    st.markdown(f"### {r['title']}")
                    st.write(r["snippet"])
                    st.caption(r["domain"])

                    st.link_button("🚀 Postularme", r["link"])
                    st.code(r["link"])

                with c2:
                    st.metric("Score", r["score"])

                    if st.button("⭐ Guardar", key=r["link"]):
                        st.session_state.favoritos.append(r)

# FAVORITOS
if st.session_state.favoritos:
    st.subheader("⭐ Guardados")
    for f in st.session_state.favoritos:
        st.markdown(f"- [{f['title']}]({f['link']})")
