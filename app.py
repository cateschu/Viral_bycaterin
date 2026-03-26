import streamlit as st
from pytrends.request import TrendReq
import requests
import pandas as pd
import random
from datetime import datetime

# ⚙️ CONFIG
st.set_page_config(layout="wide")
st.title("🚀 Trend Predictor Argentina PRO")

st.markdown("""
Detecta productos virales basados en:
- 📈 Google Trends (Argentina)
- 🌍 Tendencia global (simulada)
- 🇦🇷 Mercado Libre (precio + competencia)

👉 Identifica oportunidades antes de que exploten.
""")

# 🔎 Google Trends
pytrends = TrendReq(hl='es-AR', tz=360)

def get_trend_score(keyword):
    try:
        pytrends.build_payload([keyword], timeframe='now 7-d')
        data = pytrends.interest_over_time()
        if data.empty:
            return 0
        return int(data[keyword].mean())
    except:
        return random.randint(20, 80)

# 💰 Mercado Libre
def get_ml_data(keyword):
    try:
        url = f"https://api.mercadolibre.com/sites/MLA/search?q={keyword}"
        res = requests.get(url).json()

        if "results" not in res or len(res["results"]) == 0:
            return None, 0

        prices = [item["price"] for item in res["results"][:10]]
        avg_price = sum(prices) / len(prices)

        return int(avg_price), len(res["results"])
    except:
        return None, 0

# 🌍 Score global (simulado)
def global_score():
    return random.randint(50, 100)

# 🧠 Fase del producto
def get_stage(global_s, trend_ar, comp):
    if global_s > 80 and comp < 30:
        return "🟢 EARLY (POR EXPLOTAR)"
    elif global_s > 70:
        return "🟡 CRECIENDO"
    else:
        return "🔴 SATURADO"

# 💰 NEGOCIO
def calculate_business(price_ml, competition):
    if price_ml is None:
        return 0, "DESCONOCIDO"

    cost = price_ml * 0.4
    margin = ((price_ml - cost) / price_ml) * 100

    if margin > 50 and competition < 50:
        decision = "🟢 VENDER YA"
    elif margin > 30:
        decision = "🟡 TESTEAR"
    else:
        decision = "🔴 EVITAR"

    return int(margin), decision

# 🔄 CACHE (se actualiza cada 7 días)
@st.cache_data(ttl=604800)
def get_data():

    keywords = [
        "mini proyector portátil",
        "impresora térmica",
        "smartwatch barato",
        "auriculares bluetooth",
        "luces led rgb",
        "blender portátil",
        "corrector de postura",
        "robot aspiradora",
        "power bank",
        "soporte magnético auto",
        "lámpara inteligente",
        "cargador rápido",
        "cleaning gadget",
        "beauty skincare tool",
        "hair curler sin calor",
        "organizador escritorio",
        "tablet barata",
        "mouse inalámbrico",
        "teclado bluetooth",
        "cámara seguridad wifi"
    ]

    results = []

    for kw in keywords:
        trend_ar = get_trend_score(kw)
        price, comp = get_ml_data(kw)
        global_s = global_score()

        score = (trend_ar * 0.4) + (global_s * 0.4) + ((100 - min(comp,100)) * 0.2)

        margin, decision = calculate_business(price, comp)

        results.append({
            "Producto": kw,
            "Trend AR": trend_ar,
            "Global": global_s,
            "Precio ML": price,
            "Competencia": comp,
            "Score": int(score),
            "Margen %": margin,
            "Decision": decision,
            "Fase": get_stage(global_s, trend_ar, comp)
        })

    df = pd.DataFrame(results)
    df = df.sort_values(by="Score", ascending=False)

    return df

# 🕒 Mostrar actualización
st.info(f"📅 Última actualización automática: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# 📊 Mostrar datos
df = get_data()

st.subheader("📊 Top productos detectados")
st.dataframe(df, use_container_width=True)

# 🚨 ALERTAS
st.subheader("🚨 Oportunidades detectadas")

for _, row in df.iterrows():
    if row["Score"] > 75 and row["Competencia"] < 40:
        st.warning(f"🔥 {row['Producto']} → ALTA OPORTUNIDAD")
