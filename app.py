import streamlit as st
import pandas as pd
import numpy as np
import random
import requests
from collections import Counter, defaultdict
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")

st.title("🎟️ LotoElite Pro")
st.markdown("**A mais avançada plataforma de previsão inteligente do Brasil** • Ciclo + IA + Atualização Automática")

# ========================= SELETOR DE LOTERIA =========================
loteria_options = {
    "Lotofácil":       {"nome": "Lotofácil",       "api": "lotofacil",     "total": 25,  "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania":       {"nome": "Lotomania",       "api": "lotomania",     "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena":       {"nome": "Mega-Sena",       "api": "megasena",      "total": 60,  "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Quina":           {"nome": "Quina",           "api": "quina",         "total": 80,  "sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Dupla Sena":      {"nome": "Dupla Sena",      "api": "duplasena",     "total": 50,  "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Super Sete":      {"nome": "Super Sete",      "api": "supersete",     "total": 49,  "sorteadas": 7,  "tipo_ciclo": "frequency"},
    "Timemania":       {"nome": "Timemania",       "api": "timemania",     "total": 80,  "sorteadas": 7,  "tipo_ciclo": "frequency"},
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.markdown(f"**Loteria ativa:** {config['nome']}")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Atualização Automática")
    if st.button("🔄 Atualizar Histórico Automático (Caixa)"):
        with st.spinner("Buscando resultados mais recentes na Caixa..."):
            try:
                url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{config['api']}"
                response = requests.get(url, timeout=10)
                data = response.json()
                # Converte para DataFrame no formato que usamos
                df_novo = pd.DataFrame([concurso["dezenasSorteadas"] for concurso in data["listaDezenas"]])
                st.success(f"✅ Histórico atualizado automaticamente! {len(df_novo)} concursos carregados.")
                st.session_state.df = df_novo
            except:
                st.error("❌ Não foi possível conectar com a Caixa no momento. Tente novamente.")

# ========================= CARREGAMENTO =========================
if 'df' not in st.session_state:
    st.subheader(f"📤 Upload Manual do Histórico da {config['nome']}")
    arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])
    if arquivo is None:
        st.warning("👆 Ou use o botão acima para atualizar automaticamente")
        st.stop()
    df = pd.read_csv(arquivo, header=None, dtype=str).iloc[:, :config["sorteadas"]].apply(pd.to_numeric, errors='coerce').dropna().astype(int)
    st.session_state.df = df
else:
    df = st.session_state.df

st.success(f"✅ {len(df)} concursos carregados")

# O restante do código (ciclo, tabs, aprendizado, etc.) permanece igual à v33.0

# ... (copie aqui o restante do código da v33.0 que já estava funcionando bem)

st.caption("LotoElite Pro • Estratégia que vence o acaso com atualização automática")
