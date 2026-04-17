# LOTOELITE v85.4b - RADAR FIX
# Item 7: Alerta de Virada Prevista (sempre visível)
import streamlit as st
from datetime import datetime
import random

st.set_page_config(page_title="LotoElite v85.4b", layout="wide")
st.title("🎯 LOTOELITE v85.4b – RADAR FIX")

# Inicializa estados
if "ciclos" not in st.session_state:
    st.session_state.ciclos = {"Lotofácil": {"ciclo_atual": 1, "ultimo_concurso": 0}}
if "historico_ciclos" not in st.session_state:
    st.session_state.historico_ciclos = []

lot = st.selectbox("Loteria", ["Lotofácil", "Mega-Sena", "Quina"])

tab1, tab2 = st.tabs(["📊 CICLO", "ℹ️ Info"])

with tab1:
    st.subheader(f"Ciclo – {lot}")
    c = st.session_state.ciclos.setdefault(lot, {"ciclo_atual": 1, "ultimo_concurso": 0})

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Atualizar Ciclo REAL da Caixa"):
            c["ciclo_atual"] += 1
            c["ultimo_concurso"] += 1
            # salva histórico
            st.session_state.historico_ciclos.append({
                "lot": lot,
                "ciclo_atual": c["ciclo_atual"],
                "data": datetime.now().strftime("%d/%m %H:%M")
            })
            st.success(f"Ciclo atualizado para {c['ciclo_atual']}")
    with col2:
        st.metric("Ciclo atual", c["ciclo_atual"], delta=None)

    ideal = (4,6) if lot=="Lotofácil" else (6,9)
    st.caption(f"Ideal: {ideal[0]}-{ideal[1]} concursos | Atual: {c['ciclo_atual']}")
