import streamlit as st
import pandas as pd

st.title("🎯 IA Loteria Profissional")

arquivo = st.file_uploader("📂 Envie o CSV da Lotofácil")

if arquivo is not None:
    df = pd.read_csv(arquivo)

    st.success("Arquivo carregado!")
    st.write(df.head())
