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

# =========================
# FILTRO PROFISSIONAL
# =========================
def jogo_valido(jogo):
    soma = sum(jogo)
    if soma < 180 or soma > 220:
        return False

    pares = sum(1 for n in jogo if n % 2 == 0)
    if pares < 6 or pares > 9:
        return False

    # distribuição por grupos (1-5, 6-10...)
    grupos = [0]*5
    for n in jogo:
        grupos[(n-1)//5] += 1

    # evita concentração
    if any(g > 5 for g in grupos):
        return False

    return True
    soma = sum(jogo)
    if soma < 170 or soma > 230:
        return False

    pares = sum(1 for n in jogo if n % 2 == 0)
    if pares < 5 or pares > 10:
        return False

    return True

# =========================
# GERADOR MELHORADO
# =========================
def gerar_jogo(base, atrasadas, faltantes):
    tentativas = 0

    while True:
        jogo = set()

        # BASE FORTE
        jogo.update(base[:10])

        # ATRASADAS IMPORTANTES
        jogo.update(atrasadas[:5])

        # FALTANTES
        jogo.update(faltantes[:2])

        # POOL INTELIGENTE (NÃO MAIS ALEATÓRIO PURO)
        pool = list(set(base[:15] + atrasadas[:10] + faltantes))

        while len(jogo) < 15:
            jogo.add(random.choice(pool))

        jogo = sorted(jogo)

        if jogo_valido(jogo):
            return jogo

        tentativas += 1
        if tentativas > 100:
            return sorted(random.sample(pool, 15))
    tentativas = 0

    while True:
        jogo = set()

        jogo.update(base[:9])
        jogo.update(atrasadas[:4])
        jogo.update(faltantes[:2])

        while len(jogo) < 15:
            jogo.add(random.randint(1, 25))

        jogo = sorted(jogo)

        if jogo_valido(jogo):
            return jogo

        tentativas += 1
        if tentativas > 100:
            return sorted(random.sample(range(1,26), 15))

# =========================
# MELHOR JOGO IA
# =========================
def melhor_jogo(base, atrasadas, faltantes):
    melhor = None
    melhor_score = -1

    for _ in range(100):
        jogo = gerar_jogo(base, atrasadas, faltantes)

        score = 0
        score += len(set(jogo) & set(base[:10])) * 2
        score += len(set(jogo) & set(atrasadas[:10])) * 2
        score += len(set(jogo) & set(faltantes)) * 3

        if score > melhor_score:
            melhor_score = score
            melhor = jogo

    return melhor

# =========================
# LABORATÓRIO
# =========================
def contar_acertos(jogo, resultado_real):
    return len(set(jogo) & set(resultado_real))

def rodar_backtest(df, janela=100):
    resultados = []

    inicio = max(30, len(df) - janela)

    for i in range(inicio, len(df)-1):
        passado = df.iloc[:i]
        futuro = df.iloc[i].dropna().astype(int).tolist()

        fase, faltantes = analisar_ciclo(passado)
        base = frequencia(passado)
        atrasadas = atraso(passado)

        jogo = gerar_jogo(base, atrasadas, faltantes)
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

    st.success("Arquivo carregado!")
    st.dataframe(df)

    fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)
    atrasadas = atraso(df)

    st.subheader("📊 Ciclo")
    st.write(f"Fase: {fase}")
    st.write(f"Faltantes: {faltantes}")

    st.subheader("🎯 Gerador")

    if st.button("Gerar 5 jogos"):
        for i in range(5):
            st.write(gerar_jogo(base, atrasadas, faltantes))

    if st.button("🔥 Melhor jogo IA"):
        st.success(melhor_jogo(base, atrasadas, faltantes))

    st.markdown("---")
    st.subheader("🧪 Laboratório")

    janela = st.slider("Qtd concursos", 50, 300, 100)

    if st.button("🚀 Rodar Teste"):
        resultado = rodar_backtest(df, janela)

        if resultado:
            st.success("Teste concluído")

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
