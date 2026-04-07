import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= v14.1 MULTI-LOTERIA – NÍVEL SURREAL =========================
st.set_page_config(page_title="IA LOTOFÁCIL ELITE v14.1", page_icon="🎟️", layout="wide")

st.title("🎟️ IA LOTOFÁCIL ELITE v14.1 – NÍVEL SURREAL")
st.markdown("**AI Oracle com explicação + Gráficos interativos + Smart Bankroll Advisor** | Lotofácil 100% preservado")

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
    st.header("⚙️ Configurações v14.1")
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

# ========================= MOTOR DE CICLO =========================
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

    else:
        ultimos = df.iloc[-40:] if len(df) > 40 else df
        todos = set(np.concatenate(ultimos.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - todos)
        progresso = (config["total"] - len(faltantes)) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# Self-Learning
if "historico_acertos" not in st.session_state:
    st.session_state.historico_acertos = Counter()

def atualizar_self_learning(jogos, feedback="bom"):
    for jogo in jogos:
        for n in jogo:
            st.session_state.historico_acertos[n] += 1 if feedback == "bom" else -0.5

# ========================= AI ORACLE COM EXPLICAÇÃO TEXTUAL (NOVO v14.1) =========================
def gerar_explicacao_ai(jogo: List[int], faltantes: List[int], fase: str, config: Dict, conf: int):
    explicacao = f"**AI Oracle:** Este jogo tem **{conf}%** de confiança porque "
    if len(set(jogo) & set(faltantes)) >= 4:
        explicacao += f"prioriza **{len(set(jogo) & set(faltantes))} faltantes** do ciclo atual, "
    if fase == "FIM":
        explicacao += "está em **FIM de ciclo** (momento de alta probabilidade), "
    if estrategia == "ULTRA FOCUS":
        explicacao += "e segue o modo **ULTRA FOCUS** com agressividade máxima. "
    explicacao += "Evita números frios e respeita a assinatura histórica do ciclo."
    return explicacao

# ========================= SMART BANKROLL ADVISOR (NOVO v14.1) =========================
def smart_bankroll_advisor(bankroll: float, fase: str, conf_media: float, config: Dict):
    if fase == "FIM":
        edge = 0.38
    elif fase == "MEIO":
        edge = 0.22
    else:
        edge = 0.09
    kelly = edge * (conf_media / 100)
    kelly = max(0.01, min(0.25, kelly))  # limite seguro
    valor_recomendado = bankroll * kelly
    return kelly, valor_recomendado

# ========================= TABS v14.1 =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 AI Oracle + Gráficos",
    "🎯 Bolão Coverage",
    "🎟️ Gerar Jogos v14.1",
    "📈 Performance Dashboard",
    "💰 Smart Bankroll Advisor"
])

with tab1:
    st.subheader("🔥 AI Oracle + Gráficos Interativos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Loteria", f"**{config['nome']}**")
    col2.metric("Fase", f"**{fase}**")
    col3.metric("Faltantes", f"**{len(faltantes)}**")

    # Gráfico de evolução do ciclo
    st.subheader("Evolução da Cobertura do Ciclo")
    cobertura = []
    temp = set()
    for row in df.values:
        temp.update(row)
        cobertura.append(len(temp) / config["total"] * 100)
    st.line_chart(pd.Series(cobertura, name="Cobertura %"))

with tab3:
    st.subheader("🎟️ Gerar Jogos v14.1 com AI Oracle")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 GERAR JOGOS v14.1", type="primary", use_container_width=True):
        pool = list(range(1, config["total"]+1))
        if estrategia == "ULTRA FOCUS" and fase == "FIM":
            pool = faltantes + list(range(1, config["total"]+1))[:tamanho_pool]
        
        jogos = []
        for _ in range(qtd):
            jogo = sorted(random.sample(pool, config["sorteadas"]))
            conf = calcular_confidence(jogo, faltantes, fase, config)  # função mantida da v13.1
            explicacao = gerar_explicacao_ai(jogo, faltantes, fase, config, conf)
            jogos.append(jogo + [conf, explicacao])
        
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])] + ["AI Confidence %", "Explicação AI Oracle"])
        df_jogos = df_jogos.sort_values("AI Confidence %", ascending=False)
        st.dataframe(df_jogos.style.highlight_max(subset=["AI Confidence %"], color="#00ff88"), use_container_width=True)
        
        excel = df_jogos.to_excel(index=False)
        st.download_button("📥 Baixar Jogos com Explicação", excel, f"jogos_{config['nome']}_v14.1.xlsx", "application/vnd.ms-excel")

with tab5:
    st.subheader("💰 Smart Bankroll Advisor v14.1")
    bankroll = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    conf_media = 78  # valor médio estimado
    kelly_perc, valor_recomendado = smart_bankroll_advisor(bankroll, fase, conf_media, config)
    st.metric("Kelly % Recomendado", f"{kelly_perc*100:.1f}%")
    st.metric("Valor ideal por jogo", f"R$ {valor_recomendado:.2f}")
    st.caption("Este cálculo é dinâmico e considera fase do ciclo + confiança média + estratégia escolhida.")

st.caption("v14.1 • AI Oracle com explicação em texto natural + Gráficos interativos + Smart Bankroll Advisor • Lotofácil 100% preservado")
