import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from typing import Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= LOTOELITE PRO – v25.0 FINAL =========================
st.set_page_config(
    page_title="LotoElite Pro",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎟️ LotoElite Pro")
st.markdown("**Plataforma Profissional de Previsão Inteligente** • Ciclo + AI Oracle")

# ========================= SELETOR DE LOTERIA =========================
loteria_options = {
    "Lotofácil":       {"nome": "Lotofácil",       "total": 25,  "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania":       {"nome": "Lotomania",       "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena":       {"nome": "Mega-Sena",       "total": 60,  "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Quina":           {"nome": "Quina",           "total": 80,  "sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Dupla Sena":      {"nome": "Dupla Sena",      "total": 50,  "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Super Sete":      {"nome": "Super Sete",      "total": 49,  "sorteadas": 7,  "tipo_ciclo": "frequency"},
    "Loteria Federal": {"nome": "Loteria Federal", "total": 99999,"sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Loteria Milionária": {"nome": "Loteria Milionária", "total": 50, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Timemania":       {"nome": "Timemania",       "total": 80,  "sorteadas": 7,  "tipo_ciclo": "frequency"}
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.markdown(f"**Loteria ativa:** {config['nome']} ({config['sorteadas']} de {config['total']})")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações LotoElite Pro")
    estrategia = st.selectbox("Modo de Estratégia IA", ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"], index=3)
    tamanho_pool = st.number_input("Tamanho Base do Pool", 15, 30, 18)
    if st.button("🔄 Limpar Cache"):
        st.cache_data.clear()
        st.rerun()

# ========================= UPLOAD =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV")
    st.stop()

@st.cache_data
def carregar_csv(arquivo, sorteadas):
    try:
        df = pd.read_csv(arquivo, header=None, dtype=str)
        df = df.iloc[:, :sorteadas]
        df = df.dropna(how='all')
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna()
        df = df.astype(int)
        if df.shape[1] != sorteadas or df.empty:
            st.error("❌ CSV inválido ou vazio.")
            return None
        return df
    except Exception as e:
        st.error(f"❌ Erro ao processar o CSV: {str(e)}")
        return None

df = carregar_csv(arquivo, config["sorteadas"])
if df is None or len(df) == 0:
    st.stop()

st.success(f"✅ {len(df)} concursos carregados com sucesso!")

# ========================= MOTOR DE CICLO =========================
def detectar_ciclo(df: pd.DataFrame, config: Dict):
    if len(df) == 0:
        return "INÍCIO", list(range(1, config["total"]+1)), 0.0

    if config["tipo_ciclo"] == "full":
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
    else:
        ultimos = df.iloc[-45:] if len(df) > 45 else df
        todos = set(np.concatenate(ultimos.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - todos)
        progresso = (config["total"] - len(faltantes)) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# ========================= AI ORACLE =========================
def calcular_confidence(jogo, faltantes, fase):
    base = 50
    base += len(set(jogo) & set(faltantes)) * 6
    if fase == "FIM": base += 45
    elif fase == "MEIO": base += 25
    return min(99, max(40, int(base)))

def gerar_explicacao_ai(jogo, faltantes, fase, conf):
    return f"**AI Oracle explica:** Este jogo tem **{conf}%** de confiança porque prioriza **{len(set(jogo) & set(faltantes))} faltantes** do ciclo atual, está em fase **{fase}** e segue o modo **{estrategia}**."

# ========================= TABS =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎟️ Gerar Jogos",
    "📊 AI Oracle",
    "📈 Analytics",
    "💰 Bankroll Advisor"
])

with tab1:
    st.subheader("🎟️ Gerar Jogos")
    qtd = st.slider("Quantidade de jogos", 5, 100, 25)
    if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
        pool = list(range(1, config["total"]+1))
        if estrategia == "ULTRA FOCUS" and fase == "FIM":
            pool = faltantes + list(range(1, config["total"]+1))[:tamanho_pool]
        jogos = [sorted(random.sample(pool, config["sorteadas"])) for _ in range(qtd)]
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_jogos, use_container_width=True)

with tab2:
    st.subheader("🔥 AI Oracle")
    st.info("Sistema com explicação inteligente ativado")

with tab4:
    st.subheader("💰 Smart Bankroll Advisor")
    bankroll = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    kelly = 0.45 if fase == "FIM" else 0.28 if fase == "MEIO" else 0.12
    valor = bankroll * kelly
    st.metric("Kelly % Recomendado", f"{kelly*100:.1f}%")
    st.metric("Valor ideal por jogo", f"R$ {valor:.2f}")

st.caption("LotoElite Pro • Estratégia que vence o acaso.")
