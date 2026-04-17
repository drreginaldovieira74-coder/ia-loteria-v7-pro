import streamlit as st
from datetime import datetime

st.set_page_config(page_title="LotoElite v84.9", page_icon="🎯", layout="wide")

# DNA
DNA_LOTO = [4,6,10,14,17,19,20,24,25]
DNA_MEGA = [14,32,37,39,42]
DNA_QUINA = [4,10,14,19,20,25,32,37]

# SIDEBAR igual foto
with st.sidebar:
    st.markdown("### LOTOELITE")
    st.radio("Menu", ["MEUS JOGOS"], index=0)
    loteria = st.selectbox("Loteria", ["Lotofácil", "Mega-Sena", "Quina"])
    focus = st.slider("Focus", 0, 100, 50)
    st.caption(f"Moderado {focus}%")

# HEADER
st.markdown("<h1 style='text-align:center;color:#d32f2f;'>LOTOELITE</h1>", unsafe_allow_html=True)

# ABAS exatamente como na foto + HUB depois do AO VIVO
abas = [
    "📊 BALANÇO",
    "📈 RESULTADOS", 
    "🎮 MEUS JOGOS",
    "🎯 PLUS CATCH",
    "📡 LIVE CATCH",
    "👤 PERFIL",
    "💰 PREÇOS",
    "📤 EXPORTAR",
    "🔴 AO VIVO",
    "🎯 HUB ESPECIAL"  # adicionado no final
]

tabs = st.tabs(abas)

# Conteúdo central igual foto
with tabs[0]:
    st.subheader("Ciclo REAL do Ciclo")
    if st.button("🔄 ATUALIZAR CICLO", type="primary"):
        st.success("Ciclo atualizado!")
    st.markdown("### REAL")
    st.write("1. Superação...")

with tabs[1]:
    st.subheader("Resultados")

with tabs[2]:
    st.subheader(f"Meus Jogos - {loteria}")
    jogos = {
        "Lotofácil": [
            "01-04-05-06-10-12-14-17-19-20-22-23-24-25-03",
            "01-03-04-05-06-10-12-14-17-19-20-21-22-24-25", 
            "01-04-05-06-10-12-14-15-17-19-20-22-23-24-25"
        ],
        "Mega-Sena": [
            "14-32-37-39-42-10",
            "14-32-37-44-53-19",
            "32-39-42-33-10-05"
        ],
        "Quina": [
            "14-19-25-29-53",
            "32-37-44-64-74",
            "04-10-20-21-22"
        ]
    }
    for i, j in enumerate(jogos[loteria], 1):
        st.code(f"Jogo {i}: {j}")

with tabs[3]:
    st.subheader("Plus Catch")

with tabs[4]:
    st.subheader("Live Catch")

with tabs[5]:
    st.subheader("Perfil")
    st.write("DNA:", DNA_LOTO)

with tabs[6]:
    st.subheader("Preços")

with tabs[7]:
    st.subheader("Exportar")

with tabs[8]:
    st.subheader("AO VIVO")
    st.info("Última aba antes do Hub, igual na sua foto")

with tabs[9]:
    st.subheader("🎯 HUB ESPECIAL")
    st.success("Hub restaurado após AO VIVO")
    st.write("Fechamentos com seu DNA pré-carregado:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Lotofácil 15 em 12"):
            st.code("04-06-10-14-17-19-20-24-25-01-05-12-22-23-03")
    with col2:
        if st.button("Mega 6 em 4"):
            st.code("14-32-37-39-42-10")

st.divider()
st.caption("v84.9 - layout idêntico v84.5 | Hub após AO VIVO")
