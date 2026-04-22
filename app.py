import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="LOTOELITE TESTE", layout="wide")
st.title("🎯 LOTOELITE - TESTE CICLO")

lot = st.sidebar.selectbox("Loteria", ["Lotofácil","Mega-Sena","Quina"])

# Simula ciclo
fase = ["INÍCIO","MEIO","FIM"][datetime.now().day % 3]
st.success(f"Fase do ciclo hoje: {fase}")

if st.button("Gerar 3 jogos (teste)"):
    for i in range(3):
        jogo = sorted(pd.Series(range(1,26)).sample(15))
        st.code(" ".join(f"{n:02d}" for n in jogo))
