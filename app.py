import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria ELITE", layout="centered")

st.title("🎯 IA Loteria ELITE (IA Adaptativa + Filtros)")

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
    rev = df.iloc[::-1]

    for n in range(1, 26):
        for i, row in enumerate(rev.itertuples(index=False)):
            if n in row:
                atraso[n] = i
                break

    return sorted(atraso, key=atraso.get, reverse=True)

# =========================
# FILTROS
# =========================
def filtro_valido(jogo):
    soma = sum(jogo)
    if not (180 <= soma <= 220):
        return False

    pares = sum(1 for n in jogo if n % 2 == 0)
    if not (6 <= pares <= 9):
        return False

    # evitar sequências longas
    seq = 0
    for i in range(len(jogo)-1):
        if jogo[i]+1 == jogo[i+1]:
            seq += 1
            if seq >= 3:
                return False
        else:
            seq = 0

    return True

# =========================
# IA ADAPTATIVA (PESOS)
# =========================
def ajustar_pesos(df):
    # simples: usa frequência média como base
    media = df.mean().mean()

    peso_base = 2 if media else 2
    peso_atraso = 3 if media else 3

    return peso_base, peso_atraso

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

    return sorted(jogo)

# =========================
# PONTUAÇÃO COM PESOS
# =========================
def pontuar(jogo, base, atrasadas, peso_base, peso_atraso):
    score = 0
    score += len(set(jogo) & set(base[:10])) * peso_base
    score += len(set(jogo) & set(atrasadas[:10])) * peso_atraso

    pares = sum(1 for n in jogo if n % 2 == 0)
    if 6 <= pares <= 9:
        score += 5

    return score

# =========================
# GERAR FECHAMENTO FILTRADO
# =========================
def gerar_fechamento(base, atrasadas, faltantes, fase, peso_base, peso_atraso):
    jogos = []
    vistos = set()

    while len(jogos) < 10:
        jogo = gerar_jogo(base, atrasadas, faltantes, fase)

        if not filtro_valido(jogo):
            continue

        t = tuple(jogo)

        if t not in vistos:
            score = pontuar(jogo, base, atrasadas, peso_base, peso_atraso)
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

    concursos, fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)
    atrasadas = atraso(df)
    peso_base, peso_atraso = ajustar_pesos(df)

    st.subheader("📊 Ciclo")
    st.write(f"Fase: {fase}")
    st.write(f"Faltantes: {faltantes}")

    st.subheader("⚙️ Pesos IA")
    st.write(f"Base: {peso_base} | Atraso: {peso_atraso}")

    if st.button("🔥 Gerar ELITE"):
        jogos = gerar_fechamento(base, atrasadas, faltantes, fase, peso_base, peso_atraso)

        for i, (jogo, score) in enumerate(jogos, 1):
            st.write(f"Jogo {i}: {jogo} | Score: {score}")
