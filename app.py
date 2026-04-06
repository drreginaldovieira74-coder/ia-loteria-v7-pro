import streamlit as st
import pandas as pd
def analisar_ciclo(df):
    todos = set(range(1, 26))
    ciclo = set()
    concursos = 0

    for i in range(len(df)-1, -1, -1):
        linha = set(df.iloc[i].dropna().astype(int))
        ciclo |= linha
        concursos += 1

        if ciclo == todos:
            break

    faltantes = list(todos - ciclo)

    if concursos <= 2:
        fase = "INÍCIO"
    elif concursos <= 4:
        fase = "MEIO"
    else:
        fase = "FINAL"

    return concursos, fase, faltantes
    if arquivo is not None:
       concursos, fase, faltantes = analisar_ciclo(df)

st.subheader("📊 Análise do Ciclo")
st.write(f"Concursos no ciclo: {concursos}")
st.write(f"Fase atual: {fase}")
st.write(f"Dezenas faltantes: {faltantes}") 
st.title("🎯 IA Loteria Profissional")

arquivo = st.file_uploader("📂 Envie o CSV da Lotofácil")

if arquivo is not None:
    df = pd.read_csv(arquivo)

    st.success("Arquivo carregado!")
    st.write(df.head())
