import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= v11.0 MULTI-LOTERIA - VERSÃO CORRIGIDA =========================
st.set_page_config(page_title="IA LOTOFÁCIL ELITE v11.0", page_icon="🎟️", layout="wide")

st.title("🎟️ IA LOTOFÁCIL ELITE v11.0 – MULTI-LOTERIA MASTER")
st.markdown("**Todas as loterias com ciclo adaptado**")

# ========================= SELETOR =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Quina":     {"nome": "Quina",     "total": 80, "sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Dupla Sena":{"nome": "Dupla Sena","total": 50, "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Super Sete":{"nome": "Super Sete","total": 49, "sorteadas": 7,  "tipo_ciclo": "frequency"}
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.markdown(f"**Loteria ativa:** {config['nome']}")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações")
    estrategia = st.selectbox("Modo de Estratégia", ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"], index=3)
    tamanho_pool = st.number_input("Tamanho do Pool", 15, 30, 18)

# ========================= UPLOAD =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
arquivo = st.file_uploader("Envie o CSV (sem linha de cabeçalho)", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV")
    st.stop()

# === LEITURA SEGURA DO CSV ===
@st.cache_data
def carregar_csv(arquivo, sorteadas):
    df = pd.read_csv(arquivo, header=None)        # ← ESSA É A CORREÇÃO PRINCIPAL
    df = df.iloc[:, :sorteadas].dropna(how='all')
    df = df.astype(int)
    return df

df = carregar_csv(arquivo, config["sorteadas"])

if len(df) == 0:
    st.error("CSV vazio ou inválido. Por favor envie um CSV com números.")
    st.stop()

# ========================= MOTOR DE CICLO (corrigido) =========================
def detectar_ciclo(df: pd.DataFrame, config: Dict):
    if len(df) == 0:
        return "INÍCIO", list(range(1, config["total"]+1)), 0.0

    if config["tipo_ciclo"] == "full":  # Lotofácil
        historico = df.values
        ciclos_inicio = [0]
        cobertura = set()
        for i in range(len(historico)):
            cobertura.update(historico[i])
            if len(cobertura) == config["total"]:
                ciclos_inicio.append(i + 1)
                cobertura = set()
        ultimo_reset = ciclos_inicio[-1]
        df_atual = df.iloc[ultimo_reset:]
        
        if len(df_atual) == 0:
            return "INÍCIO", list(range(1, config["total"]+1)), 0.0
        
        cobertura_atual = set(np.concatenate(df_atual.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - cobertura_atual)
        progresso = len(cobertura_atual) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

    # Demais loterias (Lotomania, Mega, Quina, etc.)
    ultimos = df.iloc[-40:] if len(df) > 40 else df
    todos = set(np.concatenate(ultimos.values))
    faltantes = sorted(set(range(1, config["total"]+1)) - todos)
    progresso = (config["total"] - len(faltantes)) / config["total"] * 100
    fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
    return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# ========================= TABS (mantidas) =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 AI Oracle + Risk Radar",
    "🎯 Bolão Coverage",
    "🎟️ Gerar Jogos",
    "📈 Dashboard",
    "💰 Export"
])

with tab1:
    st.subheader("🔥 AI Oracle + Risk Radar")
    col1, col2, col3 = st.columns(3)
    col1.metric("Loteria", f"**{config['nome']}**")
    col2.metric("Fase", f"**{fase}**")
    col3.metric("Faltantes", f"**{len(faltantes)}**")

with tab3:
    st.subheader("🎟️ Gerar Jogos Master")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
        pool = list(range(1, config["total"]+1))
        if estrategia == "ULTRA FOCUS" and fase == "FIM":
            pool = faltantes + list(range(1, config["total"]+1))[:tamanho_pool]
        
        jogos = [sorted(random.sample(pool, config["sorteadas"])) for _ in range(qtd)]
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_jogos, use_container_width=True)
        excel = df_jogos.to_excel(index=False)
        st.download_button("📥 Baixar", excel, f"jogos_{config['nome']}.xlsx", "application/vnd.ms-excel")

st.caption("v11.0 MULTI-LOTERIA • Código corrigido • Teste novamente com Lotofácil")
