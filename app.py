import streamlit as st
from urllib.parse import quote_plus

st.set_page_config(
    page_title="Empleos Remotos en Español",
    page_icon="💼",
    layout="wide"
)

# =========================
# DATOS FIJOS
# =========================
COUNTRIES = {
    "Argentina": ["Argentina"],
    "España": ["España"],
    "México": ["México"],
    "Chile": ["Chile"],
    "Colombia": ["Colombia"],
    "Perú": ["Perú"],
    "Uruguay": ["Uruguay"],
    "Paraguay": ["Paraguay"],
    "Todos en español": ["Argentina", "España", "México", "Chile", "Colombia", "Perú", "Uruguay", "Paraguay"],
}

ROLES = {
    "Asistente virtual": [
        "asistente virtual", "virtual assistant"
    ],
    "Administrativo": [
        "administrativo remoto", "administrative assistant", "asistente administrativo"
    ],
    "Data entry": [
        "data entry", "data entry remoto"
    ],
    "Soporte y atención al cliente": [
        "customer support", "chat support", "email support", "atención al cliente remoto", "soporte remoto"
    ],
    "Back office": [
        "back office", "backoffice remoto"
    ],
    "Todos": [
        "asistente virtual", "virtual assistant", "administrativo remoto",
        "administrative assistant", "asistente administrativo", "data entry",
        "customer support", "chat support", "email support",
        "atención al cliente remoto", "soporte remoto", "back office"
    ]
}

FAST_TERMS = [
    "sin experiencia",
    "entry level",
    "junior",
    "postúlate",
    "postulate",
    "easy apply",
    "apply now",
    "aplicación rápida",
    "postulación rápida"
]

REMOTE_TERMS = [
    "remoto",
    "remote",
    "work from home",
    "home office",
    "teletrabajo"
]

EXCLUDE_TERMS = [
    "-presencial",
    "-híbrido",
    "-hybrid",
    "-onsite",
    "-senior",
    "-manager",
    "-director",
    "-developer",
    "-engineer",
    "-programador",
    "-vendedor",
    "-comercial"
]

PLATFORMS = {
    "Google": None,
    "Instagram": "instagram.com",
    "Facebook": "facebook.com",
    "LinkedIn": "linkedin.com",
    "Indeed": "indeed.com",
}

# =========================
# FUNCIONES
# =========================
def build_query(country_name: str, role_name: str, platform: str) -> str:
    countries = COUNTRIES[country_name]
    roles = ROLES[role_name]

    roles_block = " OR ".join([f'"{r}"' for r in roles])
    countries_block = " OR ".join([f'"{c}"' for c in countries])
    remote_block = " OR ".join([f'"{r}"' for r in REMOTE_TERMS])
    fast_block = " OR ".join([f'"{f}"' for f in FAST_TERMS])
    exclude_block = " ".join(EXCLUDE_TERMS)

    parts = [
        f"({roles_block})",
        f"({remote_block})",
        f"({countries_block})",
        f"({fast_block})",
        exclude_block
    ]

    domain = PLATFORMS[platform]
    if domain:
        parts.append(f"site:{domain}")

    # Última semana con operadores que ayudan en búsquedas
    parts.append('"última semana" OR "last week" OR "7 días"')

    return " ".join(parts)


def google_search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}&hl=es"


def whatsapp_url(text: str, phone: str = "") -> str:
    base = "https://wa.me/"
    return f"{base}{phone}?text={quote_plus(text)}"


def make_bundle(country_name: str, role_name: str):
    rows = []
    for platform in PLATFORMS.keys():
        q = build_query(country_name, role_name, platform)
        rows.append({
            "plataforma": platform,
            "query": q,
            "url": google_search_url(q)
        })
    return rows


# =========================
# UI
# =========================
st.title("💼 Empleos remotos en español")
st.caption("Sin API. Genera búsquedas listas para encontrar empleos remotos, recientes y con postulación fácil.")

col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("País o región", list(COUNTRIES.keys()), index=0)
with col2:
    role = st.selectbox("Tipo de puesto", list(ROLES.keys()), index=5)

st.write("La app no te pide palabras clave. Ya usa filtros fijos: remoto, sin experiencia, junior, países en español y última semana.")

bundle = make_bundle(country, role)

st.subheader("Buscar ahora")

for item in bundle:
    with st.container(border=True):
        st.markdown(f"### {item['plataforma']}")
        st.caption(item["query"])
        st.link_button(f"Abrir búsqueda en {item['plataforma']}", item["url"])

st.subheader("Abrir todas")
cols = st.columns(len(bundle))
for idx, item in enumerate(bundle):
    with cols[idx]:
        st.link_button(item["plataforma"], item["url"])

# =========================
# WHATSAPP
# =========================
st.subheader("Enviar a WhatsApp")

phone = st.text_input(
    "Número de WhatsApp en formato internacional, sin + ni espacios (opcional)",
    placeholder="549..."
)

summary_lines = [
    f"Empleos remotos - {country} - {role}",
    "",
    "Búsquedas listas:"
]

for item in bundle:
    summary_lines.append(f"{item['plataforma']}: {item['url']}")

summary_text = "\n".join(summary_lines)

if phone.strip():
    st.link_button("Mandarme búsquedas por WhatsApp", whatsapp_url(summary_text, phone.strip()))
else:
    st.link_button("Abrir WhatsApp con mensaje", whatsapp_url(summary_text))

st.text_area("Mensaje que se enviará", summary_text, height=220)

st.info(
    "Esta versión no depende de API. Genera búsquedas listas y un mensaje de WhatsApp para no trabarte con bloqueos."
)
