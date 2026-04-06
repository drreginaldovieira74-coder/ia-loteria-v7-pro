import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria ULTRA", layout="centered")

st.title("🎯 IA Loteria ULTRA (Auto-Aprendizado)")

# =========================
# CICLO
# =========================
def analisar_ciclo(df):
    todos = set(range(1, 26))
    ciclo = set()

    for i in range(len(df)-1, -1, -1):
        ciclo |= set(df.iloc[i].dropna().astype(int))
        if ciclo == todos:
            break

    faltantes = list(todos - ciclo)
    fase = "FINAL" if len(ciclo) > 20 else "MEIO"

    return fase, faltantes

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
    rev = df.iloc[::-1]

    for n in range(1, 26):
        for i, row in enumerate(rev.itertuples(index=False)):
            if n in row:
                atraso[n] = i
                break

    return sorted(atraso, key=atraso.get, reverse=True)

# =========================
# GERAR JOGO
# =========================
def gerar_jogo(base, atrasadas, faltantes, fase):
    jogo = set()

    jogo.update(base[:8])
    jogo.update(atrasadas[:4])
    jogo.update(faltantes[:3])

    while len(jogo) < 15:
        jogo.add(random.randint(1, 25))

    return sorted(jogo)

# =========================
# PONTUAÇÃO
# =========================
def pontuar(jogo, base, atrasadas, pb, pa):
    score = 0
    score += len(set(jogo) & set(base[:10])) * pb
    score += len(set(jogo) & set(atrasadas[:10])) * pa
    return score

# =========================
# BACKTEST PARA APRENDER
# =========================
def otimizar(df):
    melhores = (0, 0, 0)

    for pb in range(1, 5):
        for pa in range(1, 5):
            resultados = []

            for i in range(30, len(df)-1):
                passado = df.iloc[:i]
                futuro = set(df.iloc[i].dropna().astype(int))

                fase, faltantes = analisar_ciclo(passado)
                base = frequencia(passado)
                atrasadas = atraso(passado)

                jogo = gerar_jogo(base, atrasadas, faltantes, fase)

                acertos = len(set(jogo) & futuro)
                resultados.append(acertos)

            media = sum(resultados)/len(resultados)

            if media > melhores[2]:
                melhores = (pb, pa, media)

    return melhores

# =========================
# EXECUÇÃO
# =========================
arquivo = st.file_uploader("📂 Envie o CSV")

if arquivo is not None:
    df = pd.read_csv(arquivo)

    base = frequencia(df)
    atrasadas = atraso(df)
    fase, faltantes = analisar_ciclo(df)

    if st.button("🧠 Treinar IA"):
        pb, pa, media = otimizar(df)
        st.success(f"Melhores pesos → Base: {pb} | Atraso: {pa}")
        st.write(f"Média histórica: {round(media,2)}")

    if st.button("🔥 Gerar com IA treinada"):
        pb, pa, _ = otimizar(df)

        jogo = gerar_jogo(base, atrasadas, faltantes, fase)
        score = pontuar(jogo, base, atrasadas, pb, pa)

        st.write(jogo)
        st.write(f"Score: {score}")
