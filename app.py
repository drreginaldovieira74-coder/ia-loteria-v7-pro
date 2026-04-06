import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria Profissional", layout="wide")

st.title("🤖 IA Loteria Profissional")

# =========================
# UPLOAD
# =========================
arquivo = st.file_uploader("📂 Envie o CSV da Lotofácil", type=["csv"])

# =========================
# FUNÇÕES
# =========================
def analisar_ciclo(df):
    numeros = set(range(1, 26))
    sorteados = set(df.values.flatten())
    faltantes = list(numeros - sorteados)

    progresso = len(sorteados) / 25

    if progresso < 0.4:
        fase = "Início"
    elif progresso < 0.8:
        fase = "Meio"
    else:
        fase = "Final"

    return fase, faltantes

def frequencia(df):
    freq = df.stack().value_counts()
    return list(freq.index)

def atraso(df):
    ultimo = {}
    for i, row in df.iterrows():
        for num in row:
            ultimo[num] = i

    atraso = {num: len(df) - ultimo.get(num, 0) for num in range(1,26)}
    return sorted(atraso, key=atraso.get, reverse=True)

def gerar_pool(base, atrasadas, faltantes):
    pool = set()
    pool.update(base[:12])
    pool.update(atrasadas[:8])
    pool.update(faltantes[:5])
    pool = list(pool)

    if len(pool) < 15:
        pool = list(range(1, 26))

    return pool

import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria Profissional", layout="wide")

st.title("🤖 IA Loteria Profissional")

# =========================
# UPLOAD
# =========================
arquivo = st.file_uploader("📂 Envie o CSV da Lotofácil", type=["csv"])

# =========================
# FUNÇÕES
# =========================
def analisar_ciclo(df):
    numeros = set(range(1, 26))
    sorteados = set(df.values.flatten())
    faltantes = list(numeros - sorteados)

    progresso = len(sorteados) / 25

    if progresso < 0.4:
        fase = "Início"
    elif progresso < 0.8:
        fase = "Meio"
    else:
        fase = "Final"

    return fase, faltantes

def frequencia(df):
    freq = df.stack().value_counts()
    return list(freq.index)

def atraso(df):
    ultimo = {}
    for i, row in df.iterrows():
        for num in row:
            ultimo[num] = i

    atraso = {num: len(df) - ultimo.get(num, 0) for num in range(1,26)}
    return sorted(atraso, key=atraso.get, reverse=True)

def gerar_pool(base, atrasadas, faltantes):
    pool = set()
    pool.update(base[:12])
    pool.update(atrasadas[:8])
    pool.update(faltantes[:5])
    pool = list(pool)

    if len(pool) < 15:
        pool = list(range(1, 26))

    return pool

def gerar_jogo(base, atrasadas, faltantes):
    pool = gerar_pool(base, atrasadas, faltantes)
    return sorted(random.sample(pool, 15))

def melhor_jogo(base, atrasadas, faltantes):
    melhor = None
    melhor_score = -1

    for _ in range(100):
        jogo = gerar_jogo(base, atrasadas, faltantes)

        score = 0
        score += len(set(jogo) & set(base[:10])) * 2
        score += len(set(jogo) & set(atrasadas[:10])) * 1.5
        score += len(set(jogo) & set(faltantes)) * 2

        if score > melhor_score:
            melhor_score = score
            melhor = jogo

    return melhor

# =========================
# LABORATÓRIO
# =========================
def contar_acertos(jogo, resultado_real):
    return len(set(jogo) & set(resultado_real))

def gerar_jogo_lab(base, atrasadas, faltantes):
    pool = gerar_pool(base, atrasadas, faltantes)
    k = min(15, len(pool))
    return sorted(random.sample(pool, k))

def rodar_backtest(df, janela=100):
    resultados = []

    inicio = max(30, len(df) - janela)

    for i in range(inicio, len(df)-1):
        passado = df.iloc[:i]
        futuro = df.iloc[i].dropna().astype(int).tolist()

        fase, faltantes = analisar_ciclo(passado)
        base = frequencia(passado)
        atrasadas = atraso(passado)

        jogo = gerar_jogo_lab(base, atrasadas, faltantes)
        acertos = contar_acertos(jogo, futuro)

        resultados.append(acertos)

    if not resultados:
        return None

    media = sum(resultados) / len(resultados)
    melhor = max(resultados)
    pior = min(resultados)
    dist = {i: resultados.count(i) for i in range(10, 16)}

    return {
        "media": round(media, 2),
        "melhor": melhor,
        "pior": pior,
        "total": len(resultados),
        "dist": dist
    }

# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:
    df = pd.read_csv(arquivo)

    st.success("Arquivo carregado com sucesso!")
    st.dataframe(df)

    fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)
    atrasadas = atraso(df)

    st.subheader("📊 Análise do Ciclo")
    st.write(f"Fase atual: {fase}")
    st.write(f"Dezenas faltantes: {faltantes}")

    st.subheader("🎯 Gerador Inteligente")

    if st.button("Gerar 5 jogos"):
        for i in range(5):
            jogo = gerar_jogo(base, atrasadas, faltantes)
            st.write(f"Jogo {i+1}: {jogo}")

    if st.button("🔥 Melhor jogo (IA)"):
        jogo = melhor_jogo(base, atrasadas, faltantes)
        st.success(jogo)

    # =========================
    # LABORATÓRIO UI
    # =========================
    st.markdown("---")
    st.markdown("## 🧪 Modo Laboratório")

    janela = st.slider("Concursos para teste", 50, 300, 100)

    if st.button("🚀 Rodar Teste"):
        resultado = rodar_backtest(df, janela)

        if resultado:
            st.success("Teste concluído!")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Média", resultado["media"])
            c2.metric("Melhor", resultado["melhor"])
            c3.metric("Pior", resultado["pior"])
            c4.metric("Testes", resultado["total"])

            st.write("Distribuição:", resultado["dist"])

            if resultado["media"] >= 11.5:
                st.success("Sistema FORTE")
            elif resultado["media"] >= 11:
                st.info("Sistema BOM")
            else:
                st.warning("Precisa melhorar")
    pool = gerar_pool(base, atrasadas, faltantes)
    return sorted(random.sample(pool, 15))

def melhor_jogo(base, atrasadas, faltantes):
    melhor = None
    melhor_score = -1

    for _ in range(100):
        jogo = gerar_jogo(base, atrasadas, faltantes)

        score = 0
        score += len(set(jogo) & set(base[:10])) * 2
        score += len(set(jogo) & set(atrasadas[:10])) * 1.5
        score += len(set(jogo) & set(faltantes)) * 2

        if score > melhor_score:
            melhor_score = score
            melhor = jogo

    return melhor

# =========================
# LABORATÓRIO
# =========================
def contar_acertos(jogo, resultado_real):
    return len(set(jogo) & set(resultado_real))

def gerar_jogo_lab(base, atrasadas, faltantes):
    pool = gerar_pool(base, atrasadas, faltantes)
    k = min(15, len(pool))
    return sorted(random.sample(pool, k))

def rodar_backtest(df, janela=100):
    resultados = []

    inicio = max(30, len(df) - janela)

    for i in range(inicio, len(df)-1):
        passado = df.iloc[:i]
        futuro = df.iloc[i].dropna().astype(int).tolist()

        fase, faltantes = analisar_ciclo(passado)
        base = frequencia(passado)
        atrasadas = atraso(passado)

        jogo = gerar_jogo_lab(base, atrasadas, faltantes)
        acertos = contar_acertos(jogo, futuro)

        resultados.append(acertos)

    if not resultados:
        return None

    media = sum(resultados) / len(resultados)
    melhor = max(resultados)
    pior = min(resultados)
    dist = {i: resultados.count(i) for i in range(10, 16)}

    return {
        "media": round(media, 2),
        "melhor": melhor,
        "pior": pior,
        "total": len(resultados),
        "dist": dist
    }

# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:
    df = pd.read_csv(arquivo)

    st.success("Arquivo carregado com sucesso!")
    st.dataframe(df)

    fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)
    atrasadas = atraso(df)

    st.subheader("📊 Análise do Ciclo")
    st.write(f"Fase atual: {fase}")
    st.write(f"Dezenas faltantes: {faltantes}")

    st.subheader("🎯 Gerador Inteligente")

    if st.button("Gerar 5 jogos"):
        for i in range(5):
            jogo = gerar_jogo(base, atrasadas, faltantes)
            st.write(f"Jogo {i+1}: {jogo}")

    if st.button("🔥 Melhor jogo (IA)"):
        jogo = melhor_jogo(base, atrasadas, faltantes)
        st.success(jogo)

    # =========================
    # LABORATÓRIO UI
    # =========================
    st.markdown("---")
    st.markdown("## 🧪 Modo Laboratório")

    janela = st.slider("Concursos para teste", 50, 300, 100)

    if st.button("🚀 Rodar Teste"):
        resultado = rodar_backtest(df, janela)

        if resultado:
            st.success("Teste concluído!")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Média", resultado["media"])
            c2.metric("Melhor", resultado["melhor"])
            c3.metric("Pior", resultado["pior"])
            c4.metric("Testes", resultado["total"])

            st.write("Distribuição:", resultado["dist"])

            if resultado["media"] >= 11.5:
                st.success("Sistema FORTE")
            elif resultado["media"] >= 11:
                st.info("Sistema BOM")
            else:
                st.warning("Precisa melhorar")
