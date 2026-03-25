import streamlit as st
import pandas as pd
import requests
from pytrends.request import TrendReq

st.set_page_config(layout="wide")
st.title("🚀 By Caterina Store - Trend Hunter PRO ARG 🇦🇷")

# -----------------------------------
# TENDENCIAS
# -----------------------------------
@st.cache_data(ttl=604800)
def get_trends():
    pytrends = TrendReq(hl='es-ES', tz=360)
    
    trends = []
    
    try:
        df = pytrends.trending_searches(pn="argentina")
        trends = df[0].tolist()
    except:
        pass
    
    return list(set(trends))

# -----------------------------------
# MERCADOLIBRE DATA
# -----------------------------------
def search_mercadolibre(product):
    
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={product}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        results = data.get("results", [])
        
        if len(results) == 0:
            return "❌ No disponible", 0
        
        prices = [item["price"] for item in results[:5]]
        avg_price = sum(prices) / len(prices)
        
        return "✅ Disponible", round(avg_price, 2)
    
    except:
        return "Error", 0

# -----------------------------------
# IA DECISIÓN
# -----------------------------------
def analyze(product, available, price):
    
    score = 50
    
    if available == "❌ No disponible":
        score += 20  # oportunidad
    
    if price > 20000:
        score += 10  # margen alto
    
    keywords = ["pro", "smart", "mini", "wireless"]
    
    if any(k in product.lower() for k in keywords):
        score += 10
    
    if score >= 80:
        verdict = "🔥 IMPORTAR YA"
    elif score >= 60:
        verdict = "🟡 Buena oportunidad"
    else:
        verdict = "❌ No recomendable"
    
    return score, verdict

# -----------------------------------
# BOTÓN
# -----------------------------------
if st.button("🔍 Analizar mercado argentino"):
    
    trends = get_trends()
    
    results = []
    
    for t in trends:
        
        availability, price = search_mercadolibre(t)
        score, verdict = analyze(t, availability, price)
        
        results.append({
            "Producto": t,
            "Disponible en AR": availability,
            "Precio Promedio ($)": price,
            "Score": score,
            "Recomendación": verdict
        })
    
    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
    
    st.subheader("📊 Análisis completo Argentina")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("🔥 Mejores oportunidades")
    st.table(df.head(10))
    
    csv = df.to_csv(index=False).encode("utf-8")
    
    st.download_button(
        "📥 Descargar CSV",
        csv,
        "productos_argentina.csv",
        "text/csv"
    )
