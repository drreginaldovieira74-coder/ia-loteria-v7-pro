import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria PRO+", layout="centered")

st.title("🎯 IA Loteria PRO+ Inteligente")

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
def gerar_jogo(base, faltantes, fase):
    jogo = set()

    if fase == "INÍCIO":
        jogo.update(base[:12])
        jogo.update(random.sample(faltantes, min(3, len(faltantes))))

    elif fase == "MEIO":
        jogo.update(base[:10])
        jogo.update(random.sample(faltantes, min(5, len(faltantes))))

    else:  # FINAL
        jogo.update(base[:8])
        jogo.update(random.sample(faltantes, min(7, len(faltantes))))

    pool = list(set(range(1, 26)) - jogo)

    while len(jogo) < 15:
        jogo.add(random.choice(pool))

    return sorted(jogo)

# =========================
# PONTUAÇÃO
# =========================
def pontuar(jogo, base, faltantes):
    score = 0

    score += len(set(jogo) & set(base[:10])) * 2
    score += len(set(jogo) & set(faltantes)) * 3

    pares = sum(1 for n in jogo if n % 2 == 0)
    if 6 <= pares <= 9:
        score += 5

    return score

# =========================
# GERAR RANKING
# =========================
def gerar_rankeados(base, faltantes, fase, qtd=30):
    jogos = []

    for _ in range(qtd):
        jogo = gerar_jogo(base, faltantes, fase)
        score = pontuar(jogo, base, faltantes)
        jogos.append((jogo, score))

    jogos.sort(key=lambda x: x[1], reverse=True)

    return jogos[:5]

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

    concursos, fase, faltantes = analisar_ciclo(df)

    st.subheader("📊 Análise do Ciclo")
    st.write(f"Concursos no ciclo: {concursos}")
    st.write(f"Fase atual: {fase}")
    st.write(f"Dezenas faltantes: {faltantes}")

    base = frequencia(df)

    st.subheader("🔥 Dezenas mais fortes")
    st.write(base[:15])

    st.subheader("❄️ Dezenas mais fracas")
    st.write(base[-10:])

    if st.button("🔥 Gerar jogos PRO+"):
        top = gerar_rankeados(base, faltantes, fase)

        st.subheader("🏆 Melhores jogos otimizados")

        for i, (jogo, score) in enumerate(top, 1):
            st.write(f"Jogo {i}: {jogo} | Score: {score}")
