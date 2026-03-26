import streamlit as st
from pytrends.request import TrendReq
import requests

st.title("🔥 Productos Virales Argentina")

pytrends = TrendReq(hl='es-AR', tz=360)

KEYWORDS = [
    "mini proyector",
    "impresora termica",
    "luces led rgb",
    "smartwatch barato",
    "auriculares bluetooth"
]

def get_trend_score(keyword):
    pytrends.build_payload([keyword], timeframe='now 7-d')
    data = pytrends.interest_over_time()
    
    if data.empty:
        return 0
    
    return int(data[keyword].mean())

def get_ml_price(keyword):
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={keyword}"
    res = requests.get(url).json()

    if "results" not in res or len(res["results"]) == 0:
        return None, 0

    prices = [item["price"] for item in res["results"][:5]]
    avg_price = sum(prices) / len(prices)

    return int(avg_price), len(res["results"])

if st.button("Buscar productos virales"):
    results = []

    for kw in KEYWORDS:
        trend = get_trend_score(kw)
        price, competition = get_ml_price(kw)

        score = (trend * 0.6) + ((100 - min(competition, 100)) * 0.4)

        results.append({
            "producto": kw,
            "trend": trend,
            "precio": price,
            "competencia": competition,
            "score": int(score),
            "ganador": score > 60
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    for r in results:
        st.subheader(r["producto"])
        st.write(f"🔥 Score: {r['score']}")
        st.write(f"💰 Precio ML: {r['precio']}")
        st.write(f"📦 Competencia: {r['competencia']}")
        st.write("🚀 GANADOR" if r["ganador"] else "❌ No recomendado")
        st.divider()
