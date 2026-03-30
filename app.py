import os
import re
from datetime import datetime
from urllib.parse import urlparse

import requests
import streamlit as st

st.set_page_config(
    page_title="Empleos remotos recientes",
    page_icon="💼",
    layout="wide"
)

# =========================
# CONFIG
# =========================
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GOOGLE_CX = st.secrets.get("GOOGLE_CX", os.getenv("GOOGLE_CX", ""))

ROLE_KEYWORDS = [
    "virtual assistant",
    "asistente virtual",
    "administrative assistant",
    "administrativo",
    "admin assistant",
    "data entry",
    "customer support",
    "chat support",
    "back office",
    "email support",
    "office assistant",
    "customer service",
]

EXCLUDE_TERMS = [
    "senior",
    "sr",
    "manager",
    "director",
    "engineer",
    "developer",
    "programador",
    "sales",
    "call center presencial",
    "onsite",
    "on site",
    "híbrido",
    "hybrid",
    "presencial",
    "5 years",
    "3 years",
    "experiencia mínima 3 años",
]

PLATFORM_SITES = {
    "Google": [],
    "Facebook": ["facebook.com"],
    "Instagram": ["instagram.com"],
    "Facebook + Instagram": ["facebook.com", "instagram.com"],
    "Todas": ["facebook.com", "instagram.com"],
}

COUNTRY_OPTIONS = {
    "Argentina": {"gl": "ar", "label": "Argentina"},
    "España": {"gl": "es", "label": "España"},
    "México": {"gl": "mx", "label": "México"},
    "Chile": {"gl": "cl", "label": "Chile"},
    "Colombia": {"gl": "co", "label": "Colombia"},
    "Perú": {"gl": "pe", "label": "Perú"},
    "Uruguay": {"gl": "uy", "label": "Uruguay"},
    "Paraguay": {"gl": "py", "label": "Paraguay"},
    "Solo países en español": {"gl": None, "label": "países en español"},
}

LANGUAGE_MODES = {
    "Español": "lang_es",
    "Español + inglés": None,
}

DATE_RESTRICT = "d3"  # últimos 3 días ≈ 72 horas


# =========================
# HELPERS
# =========================
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def looks_remote(text: str) -> bool:
    remote_signals = [
        "remote", "remoto", "work from home", "home office",
        "100% remote", "fully remote", "teletrabajo"
    ]
    text = text.lower()
    return any(term in text for term in remote_signals)


def looks_spanish_region(text: str, selected_country: str) -> bool:
    text = text.lower()

    if selected_country == "Solo países en español":
        spanish_markers = [
            "argentina", "españa", "méxico", "mexico", "chile", "colombia",
            "perú", "peru", "uruguay", "paraguay", "latam", "américa latina",
            "latin america", "hispano", "español", "spanish"
        ]
        return any(marker in text for marker in spanish_markers)

    return COUNTRY_OPTIONS[selected_country]["label"].lower() in text or selected_country.lower() in text.lower()


def build_query(include_terms, exclude_terms, domains, selected_country, language_mode):
    parts = []

    roles_block = " OR ".join([f'"{term}"' for term in include_terms])
    parts.append(f"({roles_block})")

    # Solo remoto
    parts.append('("remote" OR "remoto" OR "work from home" OR "home office" OR "teletrabajo" OR "fully remote" OR "100% remote")')

    # Sin experiencia / junior / entrada
    parts.append('("entry level" OR "junior" OR "no experience" OR "sin experiencia" OR "training provided" OR "trainee")')

    # Ubicación
    if selected_country == "Solo países en español":
        parts.append('("Argentina" OR "España" OR "México" OR "Chile" OR "Colombia" OR "Perú" OR "Uruguay" OR "Paraguay" OR "LATAM" OR "América Latina")')
    else:
        parts.append(f'"{COUNTRY_OPTIONS[selected_country]["label"]}"')

    # Sitios
    if domains:
        site_block = " OR ".join([f"site:{d}" for d in domains])
        parts.append(f"({site_block})")

    # Exclusiones
    for term in exclude_terms:
        parts.append(f'-"{term}"')

    return " ".join(parts)


def google_custom_search(query, api_key, cx, num=10, start=1, gl=None, lr=None, date_restrict=None):
    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": num,
        "start": start,
        "safe": "active",
    }

    if gl:
        params["gl"] = gl
    if lr:
        params["lr"] = lr
    if date_restrict:
        params["dateRestrict"] = date_restrict

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def score_result(item, selected_country):
    title = clean_text(item.get("title", ""))
    snippet = clean_text(item.get("snippet", ""))
    link = item.get("link", "")
    text = f"{title} {snippet} {link}".lower()

    score = 0

    positive_terms = {
        "remote": 16,
        "remoto": 16,
        "work from home": 16,
        "home office": 16,
        "teletrabajo": 16,
        "virtual assistant": 14,
        "asistente virtual": 14,
        "administrative assistant": 12,
        "administrativo": 12,
        "data entry": 14,
        "customer support": 12,
        "chat support": 12,
        "back office": 10,
        "entry level": 8,
        "junior": 8,
        "sin experiencia": 10,
        "no experience": 10,
        "training provided": 8,
        "trainee": 6,
    }

    negative_terms = {
        "senior": -20,
        "manager": -20,
        "director": -20,
        "developer": -18,
        "engineer": -18,
        "presencial": -25,
        "onsite": -25,
        "on site": -25,
        "hybrid": -15,
        "híbrido": -15,
    }

    for term, pts in positive_terms.items():
        if term in text:
            score += pts

    for term, pts in negative_terms.items():
        if term in text:
            score += pts

    if looks_remote(text):
        score += 20

    if looks_spanish_region(text, selected_country):
        score += 12

    return max(score, 0)


def normalize_results(items, selected_country):
    cleaned = []
    seen = set()

    for item in items:
        link = item.get("link", "")
        if not link or link in seen:
            continue
        seen.add(link)

        title = clean_text(item.get("title", "Sin título"))
        snippet = clean_text(item.get("snippet", ""))
        text = f"{title} {snippet} {link}"

        # Filtro extra fuerte: solo remoto
        if not looks_remote(text):
            continue

        # Filtro región
        if not looks_spanish_region(text, selected_country):
            continue

        cleaned.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "domain": domain_from_url(link),
            "score": score_result(item, selected_country),
        })

    cleaned.sort(key=lambda x: x["score"], reverse=True)
    return cleaned


def export_markdown(results):
    lines = ["# Empleos remotos recientes\n"]
    for i, result in enumerate(results, start=1):
        lines.append(f"## {i}. {result['title']}")
        lines.append(f"- Puntaje IA: {result['score']}")
        lines.append(f"- Plataforma: {result['domain']}")
        lines.append(f"- Link: {result['link']}")
        lines.append(f"- Resumen: {result['snippet']}\n")
    return "\n".join(lines)


# =========================
# UI
# =========================
st.title("💼 Empleos remotos recientes")
st.caption("Buscador de empleos remotos de hasta 72 horas para Argentina o países en español.")

with st.sidebar:
    st.header("Filtros")

    selected_country = st.selectbox(
        "País o región",
        list(COUNTRY_OPTIONS.keys()),
        index=0
    )

    platform = st.selectbox(
        "Fuente",
        list(PLATFORM_SITES.keys()),
        index=0
    )

    language_mode = st.selectbox(
        "Idioma",
        list(LANGUAGE_MODES.keys()),
        index=0
    )

    max_results = st.slider(
        "Cantidad de resultados",
        min_value=10,
        max_value=50,
        value=20,
        step=10
    )

st.subheader("Puestos buscados")

custom_roles = st.text_area(
    "Palabras clave",
    value=", ".join(ROLE_KEYWORDS),
    height=120
)

search_now = st.button("🔎 Buscar ahora", use_container_width=True)

if search_now:
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        st.error("Faltan GOOGLE_API_KEY y GOOGLE_CX en Secrets.")
        st.stop()

    include_terms = [
        item.strip()
        for raw in custom_roles.splitlines()
        for item in raw.split(",")
        if item.strip()
    ]

    query = build_query(
        include_terms=include_terms,
        exclude_terms=EXCLUDE_TERMS,
        domains=PLATFORM_SITES[platform],
        selected_country=selected_country,
        language_mode=language_mode
    )

    gl_value = COUNTRY_OPTIONS[selected_country]["gl"]
    lr_value = LANGUAGE_MODES[language_mode]

    st.info(f"Consulta usada:\n\n`{query}`")
    st.caption("Reciente: últimos 3 días (≈ 72 horas)")

    all_items = []
    fetched = 0
    start = 1

    try:
        while fetched < max_results:
            batch = min(10, max_results - fetched)

            data = google_custom_search(
                query=query,
                api_key=GOOGLE_API_KEY,
                cx=GOOGLE_CX,
                num=batch,
                start=start,
                gl=gl_value,
                lr=lr_value,
                date_restrict=DATE_RESTRICT
            )

            items = data.get("items", [])
            if not items:
                break

            all_items.extend(items)
            fetched += len(items)
            start += len(items)

            if len(items) < batch:
                break

    except requests.HTTPError as exc:
        st.error(f"Error HTTP al consultar Google: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")
        st.stop()

    results = normalize_results(all_items, selected_country)

    st.success(f"Resultados útiles encontrados: {len(results)}")

    if not results:
        st.warning("No encontré resultados que cumplan remoto + español/Argentina + últimos 3 días.")
    else:
        left, right = st.columns([3, 1])

        with right:
            st.download_button(
                "⬇️ Descargar resultados",
                data=export_markdown(results),
                file_name=f"empleos_remotos_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with left:
            st.subheader("Resultados")

        for idx, result in enumerate(results, start=1):
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"### {idx}. [{result['title']}]({result['link']})")
                    st.write(result["snippet"])
                    st.caption(f"Plataforma: {result['domain']}")
                with c2:
                    st.metric("Score", result["score"])

        st.subheader("Top 5")
        for item in results[:5]:
            st.markdown(f"- [{item['title']}]({item['link']}) — **{item['score']} pts**")

with st.expander("Secrets para Streamlit"):
    st.code(
        'GOOGLE_API_KEY = "tu_api_key"\nGOOGLE_CX = "tu_search_engine_id"',
        language="toml"
    )
