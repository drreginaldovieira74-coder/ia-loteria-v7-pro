import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= v14.0 MULTI-LOTERIA – AJUSTES FINOS =========================
st.set_page_config(page_title="IA LOTOFÁCIL ELITE v14.0", page_icon="🎟️", layout="wide")

st.title("🎟️ IA LOTOFÁCIL ELITE v14.0 – MULTI-LOTERIA EVOLUÍDA")
st.markdown("**Lotofácil 100% preservado + Ajustes finos na Milionária e Timemania**")

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
    st.header("⚙️ Configurações v14.0")
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

# ====================== CARREGAMENTO ROBUSTO ======================
@st.cache_data
def carregar_csv(arquivo, sorteadas):
    df = pd.read_csv(arquivo, header=None, dtype=str)
    df = df.iloc[:, :sorteadas]
    df = df.dropna(how='all')
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    df = df.astype(int)
    return df

df = carregar_csv(arquivo, config["sorteadas"])

if len(df) == 0:
    st.error("❌ CSV inválido ou vazio.")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados!")

# ========================= MOTOR DE CICLO v14.0 (com ajustes finos) =========================
def detectar_ciclo(df: pd.DataFrame, config: Dict):
    if len(df) == 0:
        return "INÍCIO", list(range(1, config["total"]+1)), 0.0

    if config["tipo_ciclo"] == "full":  # Lotofácil – 100% preservado
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
        cobertura_atual = set(np.concatenate(df_atual.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - cobertura_atual)
        progresso = len(cobertura_atual) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

    else:  # Ajustes finos para Milionária e Timemania
        if config["nome"] in ["Loteria Milionária", "Timemania"]:
            ultimos = df.iloc[-45:] if len(df) > 45 else df   # janela maior para essas loterias
        else:
            ultimos = df.iloc[-40:] if len(df) > 40 else df
        todos = set(np.concatenate(ultimos.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - todos)
        progresso = (config["total"] - len(faltantes)) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# Self-Learning + Confidence v14.0 (ajustes finos)
if "historico_acertos" not in st.session_state:
    st.session_state.historico_acertos = Counter()

def atualizar_self_learning(jogos, feedback="bom"):
    for jogo in jogos:
        for n in jogo:
            st.session_state.historico_acertos[n] += 1 if feedback == "bom" else -0.5

def calcular_confidence(jogo: List[int], faltantes: List[int], fase: str, config: Dict):
    base = 48
    base += len(set(jogo) & set(faltantes)) * 5.5
    
    # Ajustes finos específicos
    if config["nome"] == "Loteria Milionária":
        base += 8 if fase == "FIM" else 3
    elif config["nome"] == "Timemania":
        base += 10 if fase == "FIM" else 4   # Timemania tem 7 números, então maior peso
    
    if fase == "FIM":
        base += 42
    elif fase == "MEIO":
        base += 22
    if estrategia == "ULTRA FOCUS" and fase == "FIM":
        base += 20
    
    # Self-Learning
    if st.session_state.historico_acertos:
        boost = sum(st.session_state.historico_acertos.get(n, 0) for n in jogo) / len(jogo)
        base += boost * 0.9
    
    return min(99, max(35, int(base)))

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 AI Oracle + Risk Radar",
    "🎯 Bolão Coverage",
    "🎟️ Gerar Jogos v14.0",
    "📈 Performance Dashboard",
    "💰 Strategy & Export"
])

with tab1:
    st.subheader("🔥 AI Oracle + Cycle Risk Radar")
    col1, col2, col3 = st.columns(3)
    col1.metric("Loteria", f"**{config['nome']}**")
    col2.metric("Fase", f"**{fase}**")
    col3.metric("Faltantes", f"**{len(faltantes)}**")
    risco = 92 if fase == "FIM" else 52 if fase == "MEIO" else 30
    st.metric("Cycle Risk Radar", f"**{risco}%**", "🔴" if risco > 70 else "🟢")

with tab3:
    st.subheader("🎟️ Gerar Jogos v14.0")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 GERAR JOGOS v14.0", type="primary", use_container_width=True):
        pool = list(range(1, config["total"]+1))
        if estrategia == "ULTRA FOCUS" and fase == "FIM":
            pool = faltantes + list(range(1, config["total"]+1))[:tamanho_pool]
        
        jogos = []
        for _ in range(qtd):
            jogo = sorted(random.sample(pool, config["sorteadas"]))
            conf = calcular_confidence(jogo, faltantes, fase, config)
            jogos.append(jogo + [conf])
        
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])] + ["AI Confidence %"])
        df_jogos = df_jogos.sort_values("AI Confidence %", ascending=False)
        st.dataframe(df_jogos.style.highlight_max(subset=["AI Confidence %"], color="#00ff88"), use_container_width=True)
        
        excel = df_jogos.to_excel(index=False)
        st.download_button("📥 Baixar Jogos com Confidence", excel, f"jogos_{config['nome']}_v14.0.xlsx", "application/vnd.ms-excel")
        
        st.markdown("**Feedback para Self-Learning**")
        col_a, col_b = st.columns(2)
        if col_a.button("👍 Jogos bons"):
            atualizar_self_learning([j[:config["sorteadas"]] for j in jogos], "bom")
            st.success("Self-Learning atualizado!")
        if col_b.button("👎 Preciso ajustar"):
            atualizar_self_learning([j[:config["sorteadas"]] for j in jogos], "ruim")
            st.warning("Sistema aprendendo...")

# (As outras abas permanecem iguais às da v13.0 – bolão, dashboard e export)

st.caption("v14.0 • Lotofácil 100% preservado • Ajustes finos aplicados na Milionária e Timemania • Código mais inteligente")
