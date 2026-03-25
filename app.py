import streamlit as st
import pandas as pd
import requests
from pytrends.request import TrendReq
import time

st.set_page_config(layout="wide", page_title="By Caterina - Hunter ARG")
st.title("🚀 By Caterina Store - Trend Hunter PRO ARG 🇦🇷")

# -----------------------------------
# TENDENCIAS (CON RESPALDO ANTI-ERROR)
# -----------------------------------
@st.cache_data(ttl=3600)
def get_trends():
    pytrends = TrendReq(hl='es-AR', tz=180)
    try:
        # Intentamos obtener tendencias reales de Argentina
        df = pytrends.trending_searches(pn="argentina")
        return df[0].tolist()
    except:
        # PLAN B: Si Google bloquea, usamos productos ganadores de reventa en Argentina
        return [
            "Mini Proyector Portatil", "Smartwatch T800 Ultra", 
            "Auriculares F9-5 Bluetooth", "Humidificador de Aire", 
            "Licuadora Portatil USB", "Lampara Sunset", 
            "Camara de Seguridad Wifi", "Masajeador Cervical"
        ]

# -----------------------------------
# MERCADOLIBRE DATA
# -----------------------------------
def search_mercadolibre(product):
    # Filtramos palabras que no son productos para no romper la API
    if len(product) < 3: return "❌ No disponible", 0
    
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={product}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return "❌ No disponible", 0
        
        # Sacamos el promedio de los primeros 5 precios
        prices = [item["price"] for item in results[:5]]
        avg_price = sum(prices) / len(prices)
        return "✅ Disponible", round(avg_price, 2)
    except:
        return "Error API", 0

# -----------------------------------
# IA DECISIÓN
# -----------------------------------
def analyze(product, available, price):
    score = 50
    if available == "❌ No disponible": score += 25 
    if price > 15000: score += 10
    
    keywords = ["pro", "smart", "mini", "wireless", "usb", "portatil"]
    if any(k in product.lower() for k in keywords):
        score += 15
    
    # Penalizar términos que no son productos de reventa
    trash = ["clima", "dolar", "diario", "google", "facebook", "anses", "pronostico"]
    if any(t in product.lower() for t in trash):
        score -= 60

    if score >= 75: verdict = "🔥 IMPORTAR / REVENDER YA"
    elif score >= 50: verdict = "🟡 Buena oportunidad"
    else: verdict = "❌ No recomendable"
    
    return score, verdict

# -----------------------------------
# BOTÓN PRINCIPAL
# -----------------------------------
if st.button("🔍 Analizar mercado argentino"):
    with st.spinner("Analizando tendencias y Mercado Libre..."):
        trends = get_trends()
        results = []
        
        # Limitamos a los primeros 15 para que no tarde tanto
        for t in trends[:15]:
            availability, price = search_mercadolibre(t)
            score, verdict = analyze(t, availability, price)
            
            results.append({
                "Producto": t,
                "En Mercado Libre": availability,
                "Precio Promedio AR ($)": price,
                "Score": score,
                "Recomendación": verdict
            })
        
        if results:
            df = pd.DataFrame(results)
            # Ordenamos por Score de mayor a menor
            df = df.sort_values(by="Score", ascending=False)
            
            st.subheader("📊 Análisis de Oportunidades")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Top Ganadores
            st.subheader("🏆 TOP Ganadores para tu tienda")
            winners = df[df["Score"] >= 50].head(5)
            if not winners.empty:
                st.table(winners[["Producto", "Score", "Recomendación"]])
            else:
                st.info("No se encontraron 'ganadores' claros en esta búsqueda. Probá más tarde.")

            # Descarga
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar Reporte CSV", csv, "oportunidades_bycaterina.csv", "text/csv")
        else:
            st.error("No se generaron resultados. Intentá de nuevo.")

st.info("Tip: Si el Score es alto y NO está disponible en Mercado Libre, tenés un 'Océano Azul' para vender sola.")
