import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria PRO++++", layout="centered")

st.title("🎯 IA Loteria PRO++++ (Com Backtest)")

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

    return set(jogo)

# =========================
# BACKTEST
# =========================
def backtest(df, jogos=50):
    resultados = []

    for i in range(50, len(df)-1):
        passado = df.iloc[:i]
        futuro = set(df.iloc[i].dropna().astype(int))

        fase, faltantes = analisar_ciclo(passado)
        base = frequencia(passado)
        atrasadas = atraso(passado)

        melhor = 0

        for _ in range(jogos):
            jogo = gerar_jogo(base, atrasadas, faltantes, fase)
            acertos = len(jogo & futuro)

            if acertos > melhor:
                melhor = acertos

        resultados.append(melhor)

    return resultados

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

    if st.button("📊 Rodar Backtest"):
        res = backtest(df)

        st.subheader("📈 Resultados do Backtest")

        st.write(f"Média de acertos: {sum(res)/len(res):.2f}")
        st.write(f"Maior pontuação: {max(res)}")
        st.write(f"Menor pontuação: {min(res)}")

        st.write("Distribuição:")
        st.write(res)
