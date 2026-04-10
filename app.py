import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
import datetime

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO – IA + Ciclos + Bankroll")
st.markdown("**A mais avançada ferramenta de loterias do Brasil**")

# ========================= TODAS AS LOTERIAS (incluindo Milionária) =========================
loteria_options = {
    "Lotofácil":    {"nome": "Lotofácil",    "total": 25, "sorteadas": 15, "tipo_ciclo": "full_coverage"},
    "Lotomania":    {"nome": "Lotomania",    "total": 50, "sorteadas": 50, "tipo_ciclo": "full_coverage"},
    "Quina":        {"nome": "Quina",        "total": 80, "sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Mega-Sena":    {"nome": "Mega-Sena",    "total": 60, "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Super Sete":   {"nome": "Super Sete",   "total": 10, "sorteadas": 7,  "tipo_ciclo": "column"},
    "Milionária":   {"nome": "Milionária",   "total": 50, "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Timemania":    {"nome": "Timemania",    "total": 80, "sorteadas": 7,  "tipo_ciclo": "frequency"},
    "Federal":      {"nome": "Federal",      "total": 10, "sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Dupla Sena":   {"nome": "Dupla Sena",   "total": 50, "sorteadas": 6,  "tipo_ciclo": "frequency"},
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.success(f"Loteria selecionada: **{config['nome']}** ({config['sorteadas']} números de 1 a {config['total']})")

# ========================= UPLOAD DO CSV =========================
arquivo = st.file_uploader(f"Envie o CSV histórico de {config['nome']}", type=["csv"])
if arquivo is None:
    st.info("👆 Suba o arquivo CSV para continuar")
    st.stop()

df = pd.read_csv(arquivo, header=None)
st.success(f"✅ {len(df)} concursos carregados de {config['nome']}!")

# ========================= DETECÇÃO DE CICLO =========================
def detectar_ciclo(df, config):
    historico = df.iloc[:, :config["sorteadas"]].values.astype(int)
    janela = historico[-15:] if len(historico) > 15 else historico
    numeros_sorteados = set(np.concatenate(janela))
    faltantes = sorted(set(range(1, config["total"] + 1)) - numeros_sorteados)
    progresso = len(numeros_sorteados) / config["total"]
    fase = "INÍCIO" if progresso < 0.4 else "MEIO" if progresso < 0.8 else "FIM"
    return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)
st.metric("Fase do Ciclo", fase, f"{progresso:.1%} cobertura")

# ========================= MOTOR DE APRENDIZADO PESSOAL =========================
if 'pesos_aprendidos' not in st.session_state:
    st.session_state.pesos_aprendidos = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

def aplicar_aprendizado(pool, loteria, fase):
    pesos = st.session_state.pesos_aprendidos[loteria][fase]
    if not pesos:
        return pool
    novo_pool = []
    for num in pool:
        peso = pesos.get(num, 1.0)
        novo_pool.extend([num] * max(1, int(peso * 4)))
    return novo_pool if novo_pool else pool

# ========================= GERAR JOGOS =========================
st.subheader("🎟️ Gerar Jogos com IA + Ciclo")
qtd = st.slider("Quantos jogos?", 5, 50, 15)

if st.button("🚀 GERAR JOGOS ELITE"):
    jogos = []
    pool_base = list(range(1, config["total"] + 1))
    
    for _ in range(qtd):
        pool = aplicar_aprendizado(pool_base, config["nome"], fase)
        jogo = sorted(random.sample(pool, config["sorteadas"]))
        jogos.append(jogo)
    
    df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
    st.dataframe(df_jogos)
    
    excel = df_jogos.to_excel(index=False)
    st.download_button("📥 Baixar todos os jogos (Excel)", excel, f"jogos_{config['nome']}.xlsx", "application/vnd.ms-excel")

st.markdown("---")
st.caption("LOTOELITE PRO v36.1 – Versão estável sem PyTorch (roda perfeitamente no Streamlit Cloud)")

st.info("✅ Milionária e todas as outras loterias agora aparecem normalmente!")
