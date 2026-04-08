import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")

st.title("🎟️ LotoElite Pro")
st.markdown("**A mais avançada plataforma de previsão inteligente do Brasil** • Ciclo + IA + Aprendizado Pessoal")

# ========================= SESSÃO DO USUÁRIO =========================
if 'feedback' not in st.session_state:
    st.session_state.feedback = []
if 'historico_pessoal' not in st.session_state:
    st.session_state.historico_pessoal = []

# ========================= SELETOR DE LOTERIA =========================
loteria_options = { ... }  # (mantido igual)

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

# ... (upload, ciclo, tabs 1 a 6 permanecem iguais)

# TAB 7 - PERFIL + APRENDIZADO (agora influencia os jogos)
with tab7:
    st.subheader("👤 Meu Perfil & Aprendizado Pessoal")
    st.info("Informe os pontos que você acertou. O sistema aprende e melhora seus próximos jogos.")

    col1, col2 = st.columns(2)
    with col1:
        pontos = st.number_input("Quantos pontos você acertou no último sorteio?", 0, 15, 8)
    with col2:
        if st.button("✅ Salvar Feedback"):
            st.session_state.feedback.append({
                "fase": fase,
                "estrategia": estrategia,
                "pontos": pontos,
                "loteria": config['nome']
            })
            st.success("✅ Feedback salvo! O sistema está aprendendo com você.")

    if st.session_state.feedback:
        media = np.mean([f['pontos'] for f in st.session_state.feedback])
        st.metric("Sua média de acertos", f"{media:.2f} pontos")

# O resto das tabs permanece igual às versões anteriores.

st.caption("LotoElite Pro • Estratégia que vence o acaso.")
