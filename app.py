from fastapi import FastAPI
from pytrends.request import TrendReq
import requests

app = FastAPI()

pytrends = TrendReq(hl='es-AR', tz=360)

# 🔎 Productos base (keywords virales típicos)
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

@app.get("/trends/ar")
def trends_argentina():
    results = []

    for kw in KEYWORDS:
        trend = get_trend_score(kw)
        price, competition = get_ml_price(kw)

        score = (trend * 0.6) + ((100 - min(competition, 100)) * 0.4)

        results.append({
            "producto": kw,
            "trend_score": trend,
            "precio_ml": price,
            "competencia": competition,
            "viral_score_ar": int(score),
            "ganador": score > 60 and competition < 50
        })

    return sorted(results, key=lambda x: x["viral_score_ar"], reverse=True)
