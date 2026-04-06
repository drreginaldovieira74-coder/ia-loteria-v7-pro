import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="IA Loteria ELITE", layout="wide")

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.main {background-color: #0e1117;}
h1, h2, h3 {color: #00ffcc;}
.stButton>button {background-color: #00ffcc; color: black; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("🎯 IA Loteria ELITE")
st.markdown("Sistema profissional de análise e geração inteligente")

# =========================
# FUNÇÕES
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

def frequencia(df):
    freq = {n: 0 for n in range(1, 26)}
    for _, row in df.iterrows():
        for n in row.dropna():
            freq[int(n)] += 1
    return sorted(freq, key=freq.get, reverse=True)

def atraso(df):
    atraso = {n: 0 for n in range(1, 26)}
    rev = df.iloc[::-1]

    for n in range(1, 26):
        for i, row in enumerate(rev.itertuples(index=False)):
            if n in row:
                atraso[n] = i
                break

    return sorted(atraso, key=atraso.get, reverse=True)

def gerar_jogo(base, atrasadas, faltantes):
    jogo = set()
    jogo.update(base[:8])
    jogo.update(atrasadas[:4])
    jogo.update(faltantes[:3])

    while len(jogo) < 15:
        jogo.add(random.randint(1, 25))

    return sorted(jogo)

# =========================
# UPLOAD
# =========================
arquivo = st.file_uploader("📂 Envie seu CSV da Lotofácil")

if arquivo:
    df = pd.read_csv(arquivo)

    fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)
    atrasadas = atraso(df)

    # =========================
    # DASHBOARD
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("📊 Fase do Ciclo", fase)
    col2.metric("🔥 Fortes", len(base[:10]))
    col3.metric("⏳ Atrasadas", len(atrasadas[:10]))

    st.markdown("---")

    # =========================
    # INFORMAÇÕES
    # =========================
    colA, colB = st.columns(2)

    with colA:
        st.subheader("🔥 Dezenas Fortes")
        st.write(base[:10])

    with colB:
        st.subheader("⏳ Atrasadas")
        st.write(atrasadas[:10])

    st.subheader("🎯 Faltantes do Ciclo")
    st.write(faltantes)

    st.markdown("---")

    # =========================
    # BOTÃO PRINCIPAL
    # =========================
    if st.button("🚀 Gerar Jogos Profissionais"):
        st.subheader("🏆 Jogos Gerados")

        for i in range(5):
            jogo = gerar_jogo(base, atrasadas, faltantes)

            st.markdown(f"""
            <div style='background-color:#1c1f26;padding:15px;border-radius:10px;margin-bottom:10px'>
            <b>Jogo {i+1}:</b> {jogo}
            </div>
            """, unsafe_allow_html=True)
