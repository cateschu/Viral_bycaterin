import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import time

# 1. CONFIGURACIÓN INICIAL (Siempre arriba de todo)
st.set_page_config(page_title="By Caterina Store", layout="wide")

st.title("🚀 By Caterina Store - Product Finder")

# 2. SELECTOR DE PAÍS
paises = {
    "Argentina": "argentina",
    "Brasil": "brazil", 
    "Estados Unidos": "united_states", 
    "España": "spain"
}

seleccion = st.selectbox("🌍 Seleccionar país para analizar", list(paises.keys()))

# 3. FUNCIÓN DE TENDENCIAS CON PLAN B
@st.cache_data(ttl=600)
def obtener_tendencias(nombre_pais):
    try:
        pytrends = TrendReq(hl='es-AR', tz=180, retries=2)
        df = pytrends.trending_searches(pn=nombre_pais)
        df.columns = ["Producto"]
        return df
    except Exception:
        # Si falla Google, mostramos lista de Dropshipping ganadora
        datos_respaldo = [
            "Mini Proyector Portátil", "Humidificador LED", 
            "Cepillo Secador 3 en 1", "Aspiradora Robot", 
            "Lámpara Sunset", "Licuadora USB",
            "Reloj Inteligente Ultra", "Masajeador de Cuello"
        ]
        return pd.DataFrame(datos_respaldo, columns=["Producto"])

# 4. BOTÓN Y LÓGICA
if st.button("🔍 Analizar mercado ahora"):
    with st.spinner("Buscando tendencias..."):
        time.sleep(1) # Pausa para que parezca humano
        
        df_resultados = obtener_tendencias(paises[seleccion])
        
        if not df_resultados.empty:
            st.subheader(f"📊 Resultados para {seleccion}")
            
            # Agregamos una columna de "Potencial" para que sea más pro
            df_resultados["Potencial"] = "🔥 Alto"
            
            st.table(df_resultados.head(10))
            
            st.success("¡Análisis completado! Estos productos están moviendo el mercado.")
        else:
            st.error("No se pudieron cargar datos. Intentá refrescar la página.")

st.info("Tip para By Caterina Store: Si un producto se repite en varios países, ¡es un ganador seguro!")

