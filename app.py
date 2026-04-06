import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria", layout="centered")

st.title("🎯 IA Loteria Profissional")

# =========================
# CICLO
# =========================
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

# =========================
# FREQUÊNCIA
# =========================
def frequencia(df):
    freq = {n: 0 for n in range(1, 26)}

    for _, row in df.iterrows():
        for n in row.dropna():
            freq[int(n)] += 1

    ordenado = sorted(freq, key=freq.get, reverse=True)
    return ordenado

# =========================
# GERAR JOGO INTELIGENTE
# =========================
def gerar_jogo(base, faltantes):
    jogo = set()

    # pega 10 mais fortes
    jogo.update(base[:10])

    # adiciona faltantes (se houver)
    jogo.update(faltantes)

    # completa até 15
    pool = list(set(range(1, 26)) - jogo)

    while len(jogo) < 15:
        jogo.add(random.choice(pool))

    return sorted(jogo)

# =========================
# UPLOAD
# =========================
arquivo = st.file_uploader("📂 Envie o CSV da Lotofácil")

# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:
    df = pd.read_csv(arquivo)

    st.success("Arquivo carregado!")
    st.write(df.head())

    # CICLO
    concursos, fase, faltantes = analisar_ciclo(df)

    st.subheader("📊 Análise do Ciclo")
    st.write(f"Concursos no ciclo: {concursos}")
    st.write(f"Fase atual: {fase}")
    st.write(f"Dezenas faltantes: {faltantes}")

    # FREQUÊNCIA
    base = frequencia(df)

    st.subheader("🔥 Dezenas mais fortes")
    st.write(base[:15])

    st.subheader("❄️ Dezenas mais fracas")
    st.write(base[-10:])

    # BOTÃO IA
    if st.button("🔥 Gerar jogo inteligente"):
        jogo = gerar_jogo(base, faltantes)

        st.subheader("🎯 Jogo gerado")
        st.write(jogo)

        pares = sum(1 for n in jogo if n % 2 == 0)
        impares = 15 - pares

        st.write(f"Pares: {pares} | Ímpares: {impares}")
