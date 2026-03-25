import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import time
import random

# -----------------------------------
# CONFIGURACIÓN
# -----------------------------------
st.set_page_config(
    page_title="By Caterina Store",
    layout="wide",
    page_icon="🚀"
)

st.title("🚀 By Caterina Store - Product Finder")

# -----------------------------------
# SELECTOR DE PAÍS
# -----------------------------------
# IMPORTANTE: Para trending_searches se usan nombres de país, no códigos ISO cortos.
country_map = {
    "Argentina": "argentina",
    "Estados Unidos": "united_states",
    "Brasil": "brazil",
    "España": "spain"
}

country = st.selectbox("🌍 Seleccionar país", list(country_map.keys()))
geo_name = country_map[country]

# -----------------------------------
# FUNCIÓN: TENDENCIAS (MODIFICADA ANTI-BLOQUEO)
# -----------------------------------
@st.cache_data(ttl=600) # Bajamos el tiempo a 10 min para refrescar
def get_trends(country_name):
    # Agregamos parámetros de reintento y espera para que Google no sospeche
    pytrends = TrendReq(
        hl='es-AR', 
        tz=180, 
        retries=3, 
        backoff_factor=0.5, # Espera un poco entre reintentos
        timeout=(10, 25)
    )

    try:
        # Intentamos obtener las tendencias
        df = pytrends.trending_searches(pn=country_name)
        df.columns = ["Producto"]
        
        # Generamos un score basado en la posición
        df["Trend Score"] = list(range(len(df), 0, -1))
        return df

    except Exception as e:
        st.error(f"Google bloqueó la conexión temporalmente. Probá de nuevo en 1 min.")
        return pd.DataFrame()

# -----------------------------------
# FUNCIÓN: INVENTARIO (SIMULADO)
# -----------------------------------
def get_inventory():
    return ["iPhone 15", "Smartwatch", "Auriculares Bluetooth", "Zapatillas deportivas"]

# -----------------------------------
# FUNCIÓN: IA SIMPLE
# -----------------------------------
def analyze_product(product, trend_score, in_inventory):
    score = trend_score
    if not in_inventory: score += 15
    
    keywords = ["pro", "max", "mini", "smart", "wireless", "plus", "automatic", "portatil", "usb"]
    if any(k in product.lower() for k in keywords):
        score += 15

    bad_words = ["facebook", "clima", "noticias", "diario", "whatsapp", "google"]
    if any(b in product.lower() for b in bad_words):
        score -= 40

    if score >= 25: verdict = "🔥 Producto GANADOR"
    elif score >= 15: verdict = "🟡 Buena oportunidad"
    else: verdict = "❌ No recomendado"

    return score, verdict

# -----------------------------------
# BOTÓN PRINCIPAL
# -----------------------------------
if st.button("🔍 Analizar mercado"):
    with st.spinner(f"Analizando tendencias en {country}..."):
        # Pequeña pausa aleatoria para no parecer un robot
        time.sleep(random.uniform(0.5, 1.5))
        
        trends = get_trends(geo_name)
        inventory = get_inventory()

        if not trends.empty:
            results = []
            for _, row in trends.iterrows():
                product = row["Producto"]
                t_score = row["Trend Score"]
                is_in = product in inventory
                
                f_score, rec = analyze_product(product, t_score, is_in)

                results.append({
                    "Producto": product,
                    "En Mi Tienda": "✅" if is_in else "❌",
                    "AI Score": f_score,
                    "Recomendación": rec
                })

            df_final = pd.DataFrame(results).sort_values(by="AI Score", ascending=False)

            st.subheader("📊 Resultados del Análisis")
            st.dataframe(df_final, use_container_width=True, hide_index=True)

            st.subheader("🏆 Los 3 mejores para importar ahora")
            top_3 = df_final[df_final["En Mi Tienda"] == "❌"].head(3)
            if not top_3.empty:
                for i, row in top_3.iterrows():
                    st.success(f"**{row['Producto']}** - {row['Recomendación']} (Puntaje: {row['AI Score']})")
            else:
                st.write("No se encontraron oportunidades nuevas en este momento.")
        else:
            st.warning("No hay datos disponibles. Refrescá la página en un momento.")
