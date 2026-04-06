import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria PRO+++", layout="centered")

st.title("🎯 IA Loteria PRO+++ (Nível Avançado)")

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

    return sorted(freq, key=freq.get, reverse=True)

# =========================
# ATRASO
# =========================
def atraso(df):
    atraso = {n: 0 for n in range(1, 26)}

    ultimo = df.iloc[::-1]

    for n in range(1, 26):
        for i, row in enumerate(ultimo.itertuples(index=False)):
            if n in row:
                atraso[n] = i
                break

    ordenado = sorted(atraso, key=atraso.get, reverse=True)
    return ordenado

# =========================
# GERAR JOGO AVANÇADO
# =========================
def gerar_jogo(base, atrasadas, faltantes, fase):
    jogo = set()

    if fase == "INÍCIO":
        jogo.update(base[:10])
        jogo.update(atrasadas[:3])
        jogo.update(faltantes[:2])

    elif fase == "MEIO":
        jogo.update(base[:8])
        jogo.update(atrasadas[:4])
        jogo.update(faltantes[:3])

    else:
        jogo.update(base[:6])
        jogo.update(atrasadas[:5])
        jogo.update(faltantes[:4])

    pool = list(set(range(1, 26)) - jogo)

    while len(jogo) < 15:
        jogo.add(random.choice(pool))

    return sorted(jogo)

# =========================
# PONTUAÇÃO AVANÇADA
# =========================
def pontuar(jogo, base, atrasadas):
    score = 0

    score += len(set(jogo) & set(base[:10])) * 2
    score += len(set(jogo) & set(atrasadas[:10])) * 3

    pares = sum(1 for n in jogo if n % 2 == 0)
    if 6 <= pares <= 9:
        score += 5

    return score

# =========================
# GERAR FECHAMENTO
# =========================
def gerar_fechamento(base, atrasadas, faltantes, fase, qtd=10):
    jogos = []
    vistos = set()

    while len(jogos) < qtd:
        jogo = gerar_jogo(base, atrasadas, faltantes, fase)
        t = tuple(jogo)

        if t not in vistos:
            score = pontuar(jogo, base, atrasadas)
            jogos.append((jogo, score))
            vistos.add(t)

    jogos.sort(key=lambda x: x[1], reverse=True)
    return jogos

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

    concursos, fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)
    atrasadas = atraso(df)

    st.subheader("📊 Ciclo")
    st.write(f"Fase: {fase}")
    st.write(f"Faltantes: {faltantes}")

    st.subheader("🔥 Fortes")
    st.write(base[:10])

    st.subheader("⏳ Atrasadas")
    st.write(atrasadas[:10])

    if st.button("🔥 Gerar PRO+++"):
        jogos = gerar_fechamento(base, atrasadas, faltantes, fase)

        for i, (jogo, score) in enumerate(jogos, 1):
            st.write(f"Jogo {i}: {jogo} | Score: {score}")
