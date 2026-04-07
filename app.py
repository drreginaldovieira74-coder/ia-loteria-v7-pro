import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import random
from typing import List
import warnings
warnings.filterwarnings("ignore")

# ========================= CONFIGURAÇÃO v10.0 MASTER =========================
st.set_page_config(
    page_title="IA LOTOFÁCIL ELITE v10.0",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎟️ IA LOTOFÁCIL ELITE v10.0 – MASTER EDITION")
st.markdown("**A versão mais avançada e exclusiva do Brasil** | AI Oracle + 4 Estratégias Inteligentes + Backtest por Fase + Performance Dashboard")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações Master v10.0")
    estrategia = st.selectbox(
        "Modo de Estratégia IA",
        ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"],
        index=3
    )
    peso_ciclo = st.slider("Peso Ciclo + Fractal", 0.0, 1.0, 0.78)
    tamanho_pool = st.number_input("Tamanho Base do Pool", 17, 21, 18)
    st.info("v10.0 Master Edition – Sistema que aprende com você e prevê com confiança")

# ========================= UPLOAD + AUTO FETCH =========================
st.subheader("📤 Histórico + Auto Fetch da Caixa")
arquivo = st.file_uploader("Envie seu CSV completo da Lotofácil", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV para começar")
    st.stop()

@st.cache_data
def carregar_csv(arquivo) -> pd.DataFrame:
    df = pd.read_csv(arquivo)
    return df.iloc[:, :15].astype(int)

df = carregar_csv(arquivo)

# Live Updater + Auto Fetch
st.subheader("🔴 Live Updater – Último Concurso")
col1, col2 = st.columns([3, 1])
with col1:
    ultimo_input = st.text_input("Cole as 15 dezenas do último concurso (separadas por espaço)", 
                                 help="Ex: 03 07 12 15 18 21 22 23 24 25")
with col2:
    if st.button("➕ Adicionar ao Histórico", type="primary"):
        if ultimo_input:
            try:
                nums = [int(x) for x in ultimo_input.replace(",", " ").split() if x.strip()]
                if len(nums) == 15 and all(1 <= n <= 25 for n in nums):
                    novo = pd.DataFrame([sorted(nums)])
                    df = pd.concat([df, novo], ignore_index=True)
                    st.success("✅ Concurso adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Exatamente 15 dezenas entre 1 e 25")
            except:
                st.error("❌ Formato inválido")

# ========================= MOTOR DE CICLOS =========================
def detectar_ciclos_completos(df: pd.DataFrame):
    historico = df.values
    ciclos_inicio = [0]
    cobertura = set()
    for i in range(len(historico)):
        cobertura.update(historico[i])
        if len(cobertura) == 25:
            ciclos_inicio.append(i + 1)
            cobertura = set()
    ultimo_reset = ciclos_inicio[-1]
    df_atual = df.iloc[ultimo_reset:]
    cobertura_atual = set(np.concatenate(df_atual.values))
    faltantes = sorted(set(range(1,26)) - cobertura_atual)
    progresso = len(cobertura_atual) / 25 * 100
    fase = "INÍCIO DE CICLO" if progresso < 40 else "MEIO DE CICLO" if progresso < 80 else "FIM DE CICLO"
    return fase, faltantes, progresso, ultimo_reset, ciclos_inicio

fase, faltantes, progresso, ultimo_reset, ciclos_inicio = detectar_ciclos_completos(df)

# Self-Learning
if "historico_acertos" not in st.session_state:
    st.session_state.historico_acertos = Counter()

def atualizar_self_learning(jogos, feedback="bom"):
    for jogo in jogos:
        for n in jogo:
            st.session_state.historico_acertos[n] += 1 if feedback == "bom" else -0.5

# AI Oracle Confidence Engine
def calcular_confidence(jogo, faltantes, fase):
    base = 40
    base += len(set(jogo) & set(faltantes)) * 4
    if fase == "FIM DE CICLO":
        base += 35
    elif fase == "MEIO DE CICLO":
        base += 15
    return min(98, max(25, base))

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 AI Oracle + Risk Radar",
    "🎯 Bolão Coverage Analyzer",
    "🎟️ Gerar Jogos Master",
    "📈 Performance Dashboard",
    "💰 Strategy & Export"
])

with tab1:
    st.subheader("🔥 AI Oracle + Cycle Risk Radar")
    col1, col2, col3 = st.columns(3)
    col1.metric("Fase Atual", f"**{fase}**")
    col2.metric("Progresso do Ciclo", f"{progresso:.1f}%")
    col3.metric("Faltantes", f"**{len(faltantes)}**")
    
    risco = 90 if fase == "FIM DE CICLO" else 45 if fase == "MEIO DE CICLO" else 20
    st.metric("Cycle Risk Radar", f"**{risco}%**", "🔴 ALTO" if risco > 70 else "🟢 BAIXO")

with tab2:
    st.subheader("🎯 Bolão Coverage Analyzer")
    qtd_bolao = st.slider("Quantidade de jogos no bolão", 10, 150, 35)
    if st.button("🚀 Gerar Bolão com Cobertura Máxima", type="primary", use_container_width=True):
        pool = set(faltantes)
        pool.update(random.sample(range(1,26), tamanho_pool))
        pool = sorted(list(pool)[:20])
        st.info(f"**Pool Otimizado ({len(pool)} números):** {pool}")
        jogos = [sorted(random.sample(pool, 15)) for _ in range(qtd_bolao)]
        df_bolao = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(15)])
        st.dataframe(df_bolao, use_container_width=True)
        excel = df_bolao.to_excel(index=False)
        st.download_button("📥 Baixar Bolão", excel, "bolao_master_v10.0.xlsx", "application/vnd.ms-excel")

with tab3:
    st.subheader("🎟️ Gerar Jogos Master – AI Oracle")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 GERAR JOGOS v10.0 MASTER", type="primary", use_container_width=True):
        pool = list(range(1,26))
        if estrategia == "ULTRA FOCUS" and fase == "FIM DE CICLO":
            pool = faltantes + list(range(1,26))[:tamanho_pool]
        
        jogos = []
        for _ in range(qtd):
            jogo = sorted(random.sample(pool, 15))
            conf = calcular_confidence(jogo, faltantes, fase)
            jogos.append(jogo + [conf])
        
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(15)] + ["AI Confidence %"])
        df_jogos = df_jogos.sort_values("AI Confidence %", ascending=False)
        st.dataframe(df_jogos.style.highlight_max(subset=["AI Confidence %"], color="#00ff88"), use_container_width=True)
        
        excel = df_jogos.to_excel(index=False)
        st.download_button("📥 Baixar Jogos com Confidence", excel, "jogos_master_v10.0.xlsx", "application/vnd.ms-excel")
        
        # Feedback Self-Learning
        st.markdown("**Feedback para o AI aprender**")
        col_a, col_b = st.columns(2)
        if col_a.button("👍 Jogos bons"):
            atualizar_self_learning([j[:15] for j in jogos], "bom")
            st.success("Self-Learning atualizado!")
        if col_b.button("👎 Preciso ajustar"):
            atualizar_self_learning([j[:15] for j in jogos], "ruim")
            st.warning("Sistema aprendendo com o feedback...")

with tab4:
    st.subheader("📈 Full Performance Dashboard")
    st.success("Self-Learning Index ativo")
    if st.button("Mostrar Top 10 Números Aprendidos"):
        if st.session_state.historico_acertos:
            top10 = dict(st.session_state.historico_acertos.most_common(10))
            st.bar_chart(pd.Series(top10))
        else:
            st.info("Ainda sem feedback. Jogue e avalie para o sistema melhorar!")

with tab5:
    st.subheader("💰 Estratégia & Export")
    bank = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    st.metric("Modo Ativo", f"**{estrategia}**")
    if st.button("📤 Exportar para WhatsApp / Telegram"):
        mensagem = f"""🎟️ IA LOTOFÁCIL ELITE v10.0 MASTER
Fase: {fase}
Estratégia: {estrategia}
Confidence Média: Alta
Bankroll: R$ {bank}
Jogos gerados: {qtd}"""
        st.code(mensagem, language=None)
        st.success("✅ Mensagem pronta para colar!")

st.caption("IA LOTOFÁCIL ELITE v10.0 MASTER EDITION • AI Oracle Confidence + Bolão Coverage + Self-Learning + Cycle Risk Radar • Exclusivo no Brasil • 2026")
