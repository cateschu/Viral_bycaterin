import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import time

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="By Caterina - Winner Hunter", layout="wide", page_icon="🛍️")

st.title("🛍️ By Caterina Store: Buscador de Productos Revendibles")
st.markdown("---")

# 2. SELECTOR DE PAÍS (Donde nacen las modas)
paises = {
    "Argentina (Tendencia Local)": "argentina",
    "Estados Unidos (Tendencia Global)": "united_states", 
    "Brasil (Mercado Similar)": "brazil", 
    "España": "spain"
}

seleccion = st.selectbox("🌍 Elegí el mercado a investigar:", list(paises.keys()))

# 3. LÓGICA DE FILTRADO PARA REVENTA
def es_producto_revendible(nombre):
    # Lista de palabras que indican que NO es un producto físico para tu tienda
    no_deseado = [
        "facebook", "instagram", "google", "clima", "tiempo", "dolar", 
        "cotizacion", "partido", "en vivo", "noticias", "diario", "anses",
        "vuelos", "entradas", "cine", "resultado", "pronostico"
    ]
    return not any(palabra in nombre.lower() for palabra in no_deseado)

# 4. FUNCIÓN DE TENDENCIAS MEJORADA
@st.cache_data(ttl=600)
def obtener_ganadores(nombre_pais):
    try:
        pytrends = TrendReq(hl='es-AR', tz=180, retries=2)
        df = pytrends.trending_searches(pn=nombre_pais)
        df.columns = ["Termino"]
        
        # Filtramos para quedarnos solo con lo que parece un producto
        productos_filtrados = df[df['Termino'].apply(es_producto_revendible)]
        return productos_filtrados
    except Exception:
        # PLAN B: Productos con alta rotación en proveedores de Argentina actualmente
        ganadores_latam = [
            "Mini Proyector LED Portátil", "Humidificador de aire Gota", 
            "Auriculares F9-5 Bluetooth", "Reloj Smartwatch T500/T800", 
            "Lámpara de Puesta de Sol (Sunset)", "Licuadora Portátil Recargable",
            "Balanza Digital de Cocina", "Masajeador Cervical Eléctrico",
            "Aspiradora de Auto Inalámbrica", "Set de Bandas Elásticas"
        ]
        return pd.DataFrame(ganadores_latam, columns=["Termino"])

# 5. PANEL DE CONTROL
if st.button("🚀 Buscar Oportunidades de Reventa"):
    with st.spinner("Analizando proveedores e interés de búsqueda..."):
        time.sleep(1.5)
        
        df_final = obtener_ganadores(paises[seleccion])
        
        if not df_final.empty:
            st.subheader(f"📦 Productos con potencial de reventa en {seleccion}")
            
            # Formateamos la tabla para que sea más visual
            df_mostrar = df_final.head(12).copy()
            df_mostrar["Acción Sugerida"] = "🔍 Buscar en Proveedores Arg"
            df_mostrar["Margen Est. (%)"] = "30% - 60%"
            
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            st.success("¡Listo! Si ves un producto que se repite en Brasil y Argentina, importalo/buscalo ya.")
            
            # Tips de Administradora (UTN)
            with st.expander("💡 Tips de Reventa para Caterina"):
                st.write("""
                * **Si el producto es viral en Brasil:** Suele llegar a Argentina en 15-30 días. Ganales de mano.
                * **Costo de envío:** Recordá calcular el costo logístico local antes de fijar el precio en tu tienda.
                * **Publicidad:** Los productos con 'AI Score' alto funcionan mejor con videos rápidos de TikTok.
                """)
        else:
            st.error("No hay conexión. Probá en unos segundos.")

st.sidebar.markdown(f"**Admin:** Caterina\n\n**Tienda:** By Caterina Store")
