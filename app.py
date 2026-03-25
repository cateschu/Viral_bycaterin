import streamlit as st
import pandas as pd
from pytrends.request import TrendReq

# -----------------------------------
# CONFIGURACIÓN
# -----------------------------------
st.set_page_config(
    page_title="By Caterina Store",
    layout="wide"
)

st.title("🚀 By Caterina Store - Product Finder")

# -----------------------------------
# SELECTOR DE PAÍS
# -----------------------------------
country_map = {
    "Argentina": "AR",
    "Estados Unidos": "US",
    "Brasil": "BR",
    "España": "ES"
}

country = st.selectbox("🌍 Seleccionar país", list(country_map.keys()))
geo_code = country_map[country]

# -----------------------------------
# FUNCIÓN: TENDENCIAS
# -----------------------------------
@st.cache_data(ttl=3600)
def get_trends(country_code):
    pytrends = TrendReq(hl='es-ES', tz=360)

    try:
        df = pytrends.trending_searches(pn=country_code)
        df.columns = ["Producto"]

        # Score base (posición invertida)
        df["Trend Score"] = list(range(len(df), 0, -1))

        return df

    except Exception as e:
        st.error(f"Error obteniendo tendencias: {e}")
        return pd.DataFrame()

# -----------------------------------
# FUNCIÓN: INVENTARIO (EMIDICA SIMULADO)
# -----------------------------------
def get_inventory():
    # Aquí luego conectas la API real
    return [
        "iPhone 15",
        "Smartwatch",
        "Auriculares Bluetooth",
        "Zapatillas deportivas"
    ]

# -----------------------------------
# FUNCIÓN: IA SIMPLE
# -----------------------------------
def analyze_product(product, trend_score, in_inventory):

    score = trend_score

    # Bonus si NO está en inventario (oportunidad)
    if not in_inventory:
        score += 15

    # Keywords que venden
    keywords = [
        "pro", "max", "mini", "smart",
        "wireless", "plus", "automatic"
    ]

    if any(k in product.lower() for k in keywords):
        score += 10

    # Penalización cosas no vendibles
    bad_words = ["facebook", "clima", "noticias"]

    if any(b in product.lower() for b in bad_words):
        score -= 20

    # Clasificación
    if score >= 80:
        verdict = "🔥 Producto GANADOR"
    elif score >= 50:
        verdict = "🟡 Buena oportunidad"
    else:
        verdict = "❌ No recomendado"

    return score, verdict

# -----------------------------------
# BOTÓN PRINCIPAL
# -----------------------------------
if st.button("🔍 Analizar productos"):

    with st.spinner("Analizando mercado..."):

        trends = get_trends(geo_code)
        inventory = get_inventory()

        if trends.empty:
            st.warning("No se pudieron obtener datos.")
        else:

            results = []

            for _, row in trends.iterrows():

                product = row["Producto"]
                trend_score = row["Trend Score"]

                in_inventory = product in inventory

                final_score, verdict = analyze_product(
                    product,
                    trend_score,
                    in_inventory
                )

                results.append({
                    "Producto": product,
                    "Trend Score": trend_score,
                    "En Inventario": "Sí" if in_inventory else "No",
                    "AI Score": final_score,
                    "Recomendación": verdict
                })

            df = pd.DataFrame(results)
            df = df.sort_values(by="AI Score", ascending=False)

            # -----------------------------------
            # DASHBOARD
            # -----------------------------------
            st.subheader("📊 Productos en tendencia")
            st.dataframe(df, use_container_width=True)

            # TOP 5
            st.subheader("🔥 Top 5 productos recomendados")
            st.table(df.head(5))

            # -----------------------------------
            # EXPORTAR CSV
            # -----------------------------------
            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"tendencias_{country}.csv",
                mime="text/csv"
            )
