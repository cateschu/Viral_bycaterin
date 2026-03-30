import re
from urllib.parse import urlparse

import requests
import streamlit as st

st.set_page_config(page_title="Empleos Remotos AR", page_icon="💼")

# 🔑 TUS CLAVES (YA PUESTAS)
GOOGLE_API_KEY = "AIzaSyDswZxrBOdaz6jZnByoEjwOcvzU7hJ6bQw"
GOOGLE_CX = "d48625c20c6824976"

ROLES = [
    "asistente virtual",
    "administrativo remoto",
    "data entry",
    "customer support",
    "chat support",
    "email support",
]

FAST = [
    "sin experiencia",
    "entry level",
    "postulate",
    "postúlate",
    "apply now",
    "easy apply",
]

EXCLUDE = [
    "presencial",
    "híbrido",
    "senior",
    "manager",
    "developer",
    "engineer",
]

def clean(text):
    return re.sub(r"\s+", " ", text or "")

def contains(text, words):
    text = text.lower()
    return any(w in text for w in words)

def valid(text):
    return (
        contains(text, ["remoto", "remote"])
        and contains(text, ["argentina"])
        and not contains(text, EXCLUDE)
    )

def score(text):
    s = 0
    text = text.lower()

    for r in ROLES:
        if r in text:
            s += 15

    for f in FAST:
        if f in text:
            s += 20

    if "sin experiencia" in text:
        s += 30

    return s

def query():
    return """
    ("asistente virtual" OR "data entry" OR "administrativo")
    ("remoto" OR "remote")
    ("Argentina")
    ("sin experiencia" OR "entry level" OR "postulate" OR "apply now")
    """

def search():
    url = "https://customsearch.googleapis.com/customsearch/v1"

    res = requests.get(url, params={
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query(),
        "num": 20,
        "dateRestrict": "d3"
    })

    return res.json().get("items", [])

# UI
st.title("💼 Empleos Remotos Argentina")
st.write("Trabajos fáciles, remotos y recientes")

if st.button("🔎 Buscar empleos"):

    items = search()

    results = []

    for i in items:
        title = clean(i.get("title"))
        snippet = clean(i.get("snippet"))
        link = i.get("link")

        text = f"{title} {snippet}"

        if not valid(text):
            continue

        sc = score(text)

        if sc < 30:
            continue

        results.append({
            "title": title,
            "link": link,
            "snippet": snippet,
            "score": sc
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    if not results:
        st.warning("No hay resultados ahora mismo")
    else:
        st.subheader("🟢 MÁS FÁCILES")

        for r in results[:5]:
            st.markdown(f"- [{r['title']}]({r['link']})")

        st.divider()

        for r in results:
            st.markdown(f"### {r['title']}")
            st.write(r["snippet"])
            st.link_button("🚀 Postularme", r["link"])
            st.write("---")
