import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime
import numpy as np

st.set_page_config(page_title="LOTOELITE V89", layout="wide", page_icon="🎯")

st.title("🎯 LOTOELITE V89 - Teste")
st.success("✅ App rodando! Agora vamos adicionar o ciclo.")

# ─── CONFIG ───
USAR_FILTRO_POOL = False # amanhã muda para True

configs = {
    "Lotofácil": {"max": 25, "qtd": 15},
    "Mega-Sena": {"max": 60, "qtd": 6},
    "Quina": {"max": 80, "qtd": 5},
}

API_BASE = "https://loteriascaixa-api.herokuapp.com/api"
API = {"Lotofácil": "lotofacil", "Mega-Sena": "megasena", "Quina": "quina"}

@st.cache_data(ttl=3600)
def busca(lot):
    try:
        slug = API[lot]
        r = requests.get(f"{API_BASE}/{slug}/latest", timeout=10).json()
        return {"ok": True, "concurso": r.get("concurso"), "dezenas": r.get("dezenas", [])}
    except:
        return {"ok": False}

# Sidebar
with st.sidebar:
    st.header("⚙️ V89")
    lot = st.selectbox("Loteria", list(configs.keys()))
    st.link_button("Abrir CAIXA", "https://www.loteriasonline.caixa.gov.br")

    dados = busca(lot)
    if dados["ok"]:
        st.success(f"Concurso {dados['concurso']}")
        st.write("Dezenas:", dados["dezenas"])

# Gerador simples
st.subheader(f"Gerador {lot}")
if st.button("Gerar Jogo", type="primary"):
    q = configs[lot]["qtd"]
    maxn = configs[lot]["max"]
    jogo = sorted(random.sample(range(1, maxn+1), q))
    st.markdown("### " + " - ".join(f"{n:02d}" for n in jogo))
    st.info(f"Pool Duplo: {'ATIVO' if USAR_FILTRO_POOL else 'OFF (teste amanhã)'}")

st.caption("Versão teste - se aparecer isso, o deploy funcionou")
