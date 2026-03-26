import streamlit as st
from pytrends.request import TrendReq
import requests
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🚀 Trend Predictor Argentina PRO")

pytrends = TrendReq(hl='es-AR', tz=360)

# 🔥 Keywords base (TikTok + AliExpress)
BASE_KEYWORDS = [
    "mini proyector", "impresora termica", "smartwatch",
    "auriculares bluetooth", "luces led", "portable blender",
    "posture corrector", "robot aspiradora",
    "power bank", "desk lamp", "magnetic phone holder",
    "uv sanitizer", "beauty skincare tool",
    "heatless hair curler", "cleaning gadget"
]

# 🔎 Google Trends
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

# 🌍 Score global (simulación AliExpress + TikTok)
def global_score():
    return random.randint(50, 100)

# 🧠 FASE DE TREND
def get_stage(global_s, trend_ar, comp):
    if global_s > 80 and comp < 30:
        return "🟢 EARLY (POR EXPLOTAR)"
    elif global_s > 70:
        return "🟡 CRECIENDO"
    else:
        return "🔴 SATURADO"

# 🚀 BOTÓN
if st.button("🔍 Detectar productos ganadores"):

    results = []
    progress = st.progress(0)

    for i, kw in enumerate(BASE_KEYWORDS):

        trend_ar = get_trend_score(kw)
        price, comp = get_ml_data(kw)
        global_s = global_score()

        score = (trend_ar * 0.4) + (global_s * 0.4) + ((100 - min(comp,100)) * 0.2)

        results.append({
            "Producto": kw,
            "Trend AR": trend_ar,
            "Global": global_s,
            "Precio ML": price,
            "Competencia": comp,
            "Score": int(score),
            "Fase": get_stage(global_s, trend_ar, comp),
            "Ganador": score > 65 and comp < 50
        })

        progress.progress((i + 1) / len(BASE_KEYWORDS))

    df = pd.DataFrame(results)
    df = df.sort_values(by="Score", ascending=False)

    st.dataframe(df, use_container_width=True)

    st.success("✅ Productos analizados")
