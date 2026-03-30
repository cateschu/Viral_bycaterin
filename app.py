import re
from urllib.parse import urlparse, quote

import requests
import streamlit as st

st.set_page_config(
    page_title="Empleos Remotos en Español",
    page_icon="💼",
    layout="wide"
)

# =========================================================
# TUS DATOS
# =========================================================
GOOGLE_API_KEY = "AIzaSyBJxLHJXug1lYl3riS8dKEatYLPiY9AThA"
GOOGLE_CX = "d48625c20c6824976"

# =========================================================
# CONFIG
# =========================================================
DATE_RESTRICT = "d7"   # última semana
LANGUAGE = "lang_es"

COUNTRIES = {
    "Argentina": {"gl": "ar", "terms": ["argentina", "buenos aires", "rosario", "córdoba", "cordoba", "mendoza", "santa fe"]},
    "España": {"gl": "es", "terms": ["españa", "madrid", "barcelona", "valencia", "sevilla"]},
    "México": {"gl": "mx", "terms": ["méxico", "mexico", "cdmx", "guadalajara", "monterrey"]},
    "Chile": {"gl": "cl", "terms": ["chile", "santiago", "valparaíso", "valparaiso"]},
    "Colombia": {"gl": "co", "terms": ["colombia", "bogotá", "bogota", "medellín", "medellin"]},
    "Perú": {"gl": "pe", "terms": ["perú", "peru", "lima"]},
    "Uruguay": {"gl": "uy", "terms": ["uruguay", "montevideo"]},
    "Paraguay": {"gl": "py", "terms": ["paraguay", "asunción", "asuncion"]},
    "Todos en español": {"gl": None, "terms": [
        "argentina", "españa", "méxico", "mexico", "chile",
        "colombia", "perú", "peru", "uruguay", "paraguay", "latam"
    ]},
}

ROLES = [
    "asistente virtual",
    "virtual assistant",
    "administrativo remoto",
    "administrative assistant",
    "data entry",
    "customer support",
    "chat support",
    "email support",
    "back office",
    "atención al cliente remoto",
    "soporte remoto",
    "asistente administrativo",
]

FAST_APPLY = [
    "sin experiencia",
    "no experience",
    "entry level",
    "junior",
    "trainee",
    "postulate",
    "postúlate",
    "apply now",
    "easy apply",
    "quick apply",
    "aplicación rápida",
    "postulación rápida",
]

REMOTE_TERMS = [
    "remoto",
    "remote",
    "work from home",
    "home office",
    "teletrabajo",
    "100% remoto",
    "fully remote",
]

EXCLUDE = [
    "presencial",
    "híbrido",
    "hybrid",
    "onsite",
    "on site",
    "senior",
    "sr",
    "manager",
    "director",
    "developer",
    "engineer",
    "programador",
    "comercial",
    "vendedor",
]

SOURCES = {
    "Google + Instagram + Facebook": [],
    "Solo Google": [],
    "Instagram": ["instagram.com"],
    "Facebook": ["facebook.com"],
    "Instagram + Facebook": ["instagram.com", "facebook.com"],
}

# =========================================================
# FUNCIONES
# =========================================================
def clean(text: str) -> str:
    text = text or ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def contains_any(text: str, words: list[str]) -> bool:
    text = text.lower()
    return any(w.lower() in text for w in words)


def looks_remote(text: str) -> bool:
    return contains_any(text, REMOTE_TERMS)


def looks_fast_apply(text: str) -> bool:
    return contains_any(text, FAST_APPLY)


def has_excluded(text: str) -> bool:
    return contains_any(text, EXCLUDE)


def looks_country(text: str, country_name: str) -> bool:
    terms = COUNTRIES[country_name]["terms"]
    return contains_any(text, terms)


def score(text: str, country_name: str) -> int:
    text = text.lower()
    s = 0

    for role in ROLES:
        if role.lower() in text:
            s += 14

    for word in FAST_APPLY:
        if word.lower() in text:
            s += 16

    for word in REMOTE_TERMS:
        if word.lower() in text:
            s += 18

    if looks_country(text, country_name):
        s += 14

    if "sin experiencia" in text:
        s += 24
    if "entry level" in text:
        s += 18
    if "junior" in text:
        s += 12
    if "trainee" in text:
        s += 12

    return s


def build_query(domains: list[str], country_name: str) -> str:
    roles = " OR ".join([f'"{r}"' for r in ROLES])
    fast = " OR ".join([f'"{f}"' for f in FAST_APPLY])

    if country_name == "Todos en español":
        country_block = '"Argentina" OR "España" OR "México" OR "Chile" OR "Colombia" OR "Perú" OR "Uruguay" OR "Paraguay" OR "LATAM"'
    else:
        country_block = f'"{country_name}"'

    query = f"""
    ({roles})
    ("remoto" OR "remote" OR "work from home" OR "home office" OR "teletrabajo")
    ({country_block})
    ("español" OR "trabajo" OR "empleo" OR "postúlate" OR "postulate")
    ({fast})
    """

    if domains:
        sites = " OR ".join([f"site:{d}" for d in domains])
        query += f" ({sites})"

    for e in EXCLUDE:
        query += f' -"{e}"'

    return query


def search_google(api_key: str, cx: str, query: str, limit: int, gl_value=None):
    url = "https://customsearch.googleapis.com/customsearch/v1"
    results = []
    start = 1

    while len(results) < limit:
        batch = min(10, limit - len(results))

        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": batch,
            "start": start,
            "lr": LANGUAGE,
            "dateRestrict": DATE_RESTRICT,
            "safe": "active",
        }
        if gl_value:
            params["gl"] = gl_value

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        results.extend(items)
        start += len(items)

        if len(items) < batch:
            break

    return results


def process_results(items: list[dict], country_name: str) -> list[dict]:
    out = []
    seen = set()

    for item in items:
        link = item.get("link", "")
        if not link or link in seen:
            continue
        seen.add(link)

        title = clean(item.get("title", "Sin título"))
        snippet = clean(item.get("snippet", ""))
        domain = get_domain(link)
        full_text = f"{title} {snippet} {link}"

        if has_excluded(full_text):
            continue

        if not looks_remote(full_text):
            continue

        # Para "Todos en español", no exigimos país exacto en todos los casos
        if country_name != "Todos en español":
            if not looks_country(full_text, country_name):
                continue

        sc = score(full_text, country_name)

        # más flexible que antes
        if sc < 28:
            continue

        easy = looks_fast_apply(full_text) or ("sin experiencia" in full_text.lower()) or ("entry level" in full_text.lower())

        out.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "domain": domain,
            "score": sc,
            "easy": easy,
        })

    out.sort(key=lambda x: (x["easy"], x["score"]), reverse=True)
    return out


def make_whatsapp_text(results: list[dict], country_name: str) -> str:
    if not results:
        return "No encontré empleos remotos esta semana."

    lines = [f"Empleos remotos encontrados para {country_name}:"]
    for i, r in enumerate(results[:8], start=1):
        lines.append(f"{i}. {r['title']} - {r['link']}")
    return "\n".join(lines)


def whatsapp_link(phone: str, text: str) -> str:
    phone = re.sub(r"\D", "", phone or "")
    return f"https://wa.me/{phone}?text={quote(text)}"


# =========================================================
# INTERFAZ
# =========================================================
st.title("💼 Empleos Remotos en Español")
st.caption("Remotos, recientes, sin experiencia o junior, con Google / Instagram / Facebook.")

with st.sidebar:
    st.subheader("Filtros")
    country_name = st.selectbox("País", list(COUNTRIES.keys()), index=0)
    source = st.selectbox("Fuente", list(SOURCES.keys()), index=0)
    cantidad = st.slider("Cantidad de resultados", 10, 50, 30, 10)

    st.subheader("WhatsApp")
    phone = st.text_input("Tu número con código país", placeholder="549....")

if "favoritos" not in st.session_state:
    st.session_state.favoritos = []

st.write("La app ya busca sola. No hace falta escribir nada.")

if st.button("🔎 Buscar empleos", use_container_width=True):
    if GOOGLE_API_KEY.startswith("PEGAR") or GOOGLE_CX.startswith("PEGAR"):
        st.error("Primero tenés que pegar tu API key y tu CX arriba del archivo.")
        st.stop()

    query = build_query(SOURCES[source], country_name)
    gl_value = COUNTRIES[country_name]["gl"]

    with st.spinner("Buscando empleos remotos..."):
        try:
            items = search_google(GOOGLE_API_KEY, GOOGLE_CX, query, cantidad, gl_value)
            results = process_results(items, country_name)
            st.session_state["last_results"] = results
            st.session_state["last_country"] = country_name
        except requests.HTTPError as e:
            st.error(f"Error de Google: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Error inesperado: {e}")
            st.stop()

    st.success(f"Encontré {len(results)} resultados útiles.")

    if not results:
        st.warning("Probá con 'Todos en español' o con 'Google + Instagram + Facebook', porque a veces una fuente sola trae muy poco.")
    else:
        easy_results = [r for r in results if r["easy"]]

        if easy_results:
            st.subheader("🟢 Más fáciles para entrar")
            for r in easy_results[:8]:
                st.markdown(f"- [{r['title']}]({r['link']})")
        else:
            st.subheader("🟡 Mejores resultados")
            for r in results[:8]:
                st.markdown(f"- [{r['title']}]({r['link']})")

        st.divider()

        st.subheader("Todos los resultados")
        for r in results:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])

                with c1:
                    st.markdown(f"### [{r['title']}]({r['link']})")
                    st.write(r["snippet"])
                    st.caption(f"Fuente: {r['domain']}")
                    st.link_button("🚀 Postularme", r["link"])

                with c2:
                    st.metric("Score", r["score"])
                    if r["easy"]:
                        st.caption("Fácil / rápida")
                    if st.button("⭐ Guardar", key=f"fav_{r['link']}"):
                        st.session_state.favoritos.append(r)

if st.session_state.get("last_results"):
    st.divider()
    st.subheader("📲 Enviar resumen a WhatsApp")

    text = make_whatsapp_text(
        st.session_state["last_results"],
        st.session_state.get("last_country", "tu búsqueda")
    )

    st.text_area("Mensaje que se enviará", value=text, height=180)

    if phone:
        st.link_button("Enviar a WhatsApp", whatsapp_link(phone, text))
    else:
        st.info("Poné tu número en la barra lateral para abrir WhatsApp con el mensaje listo.")

if st.session_state.favoritos:
    st.divider()
    st.subheader("⭐ Guardados")
    vistos = set()
    for f in st.session_state.favoritos:
        if f["link"] in vistos:
            continue
        vistos.add(f["link"])
        st.markdown(f"- [{f['title']}]({f['link']})")
