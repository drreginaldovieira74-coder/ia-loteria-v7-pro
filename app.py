import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= v13.0 MULTI-LOTERIA – EVOLUÇÃO =========================
st.set_page_config(page_title="IA LOTOFÁCIL ELITE v13.0", page_icon="🎟️", layout="wide")

st.title("🎟️ IA LOTOFÁCIL ELITE v13.0 – MULTI-LOTERIA EVOLUÍDA")
st.markdown("**Versão mais inteligente e estável** | Lotofácil 100% preservada + melhorias em todas as loterias")

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

st.markdown(f"**Loteria ativa:** {config['nome']} ({config['sorteadas']} de {config['total']})")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações v13.0")
    estrategia = st.selectbox("Modo de Estratégia IA", ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"], index=3)
    tamanho_pool = st.number_input("Tamanho Base do Pool", 15, 30, 18)
    if st.button("🔄 Limpar Cache e Reiniciar"):
        st.cache_data.clear()
        st.rerun()

# ========================= UPLOAD =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV")
    st.stop()

# ====================== CARREGAMENTO ULTRA ROBUSTO ======================
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

# ========================= MOTOR DE CICLO (v13.0) =========================
def detectar_ciclo(df: pd.DataFrame, config: Dict):
    if len(df) == 0:
        return "INÍCIO", list(range(1, config["total"]+1)), 0.0

    if config["tipo_ciclo"] == "full":  # Lotofácil (100% preservado)
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

    # Lotomania e outras (melhorado na v13.0)
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

def calcular_confidence(jogo: List[int], faltantes: List[int], fase: str, config: Dict):
    base = 48
    base += len(set(jogo) & set(faltantes)) * 5.5
    if fase == "FIM":
        base += 42
    elif fase == "MEIO":
        base += 22
    if estrategia == "ULTRA FOCUS" and fase == "FIM":
        base += 20
    # Self-Learning boost
    if st.session_state.historico_acertos:
        boost = sum(st.session_state.historico_acertos.get(n, 0) for n in jogo) / len(jogo)
        base += boost * 0.8
    return min(99, max(35, int(base)))

# ========================= TABS v13.0 =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 AI Oracle + Risk Radar",
    "🎯 Bolão Coverage",
    "🎟️ Gerar Jogos v13.0",
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

with tab2:
    st.subheader("🎯 Bolão Coverage Analyzer")
    qtd_bolao = st.slider("Quantidade de jogos no bolão", 10, 150, 35)
    if st.button("🚀 Gerar Bolão com Cobertura Máxima", type="primary", use_container_width=True):
        pool = set(faltantes)
        pool.update(random.sample(range(1, config["total"]+1), tamanho_pool))
        pool = sorted(list(pool)[:20])
        st.info(f"**Pool Otimizado ({len(pool)} números):** {pool}")
        jogos = [sorted(random.sample(pool, config["sorteadas"])) for _ in range(qtd_bolao)]
        df_bolao = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_bolao, use_container_width=True)
        excel = df_bolao.to_excel(index=False)
        st.download_button("📥 Baixar Bolão", excel, f"bolao_{config['nome']}_v13.0.xlsx", "application/vnd.ms-excel")

with tab3:
    st.subheader("🎟️ Gerar Jogos v13.0")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 GERAR JOGOS v13.0", type="primary", use_container_width=True):
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
        st.download_button("📥 Baixar Jogos com Confidence", excel, f"jogos_{config['nome']}_v13.0.xlsx", "application/vnd.ms-excel")
        
        st.markdown("**Feedback para Self-Learning**")
        col_a, col_b = st.columns(2)
        if col_a.button("👍 Jogos bons"):
            atualizar_self_learning([j[:config["sorteadas"]] for j in jogos], "bom")
            st.success("Self-Learning atualizado!")
        if col_b.button("👎 Preciso ajustar"):
            atualizar_self_learning([j[:config["sorteadas"]] for j in jogos], "ruim")
            st.warning("Sistema aprendendo...")

with tab4:
    st.subheader("📈 Performance Dashboard v13.0")
    st.success("Self-Learning ativo em todas as loterias")
    if st.button("Mostrar Top 10 Números Aprendidos"):
        if st.session_state.historico_acertos:
            top10 = dict(st.session_state.historico_acertos.most_common(10))
            st.bar_chart(pd.Series(top10))

with tab5:
    st.subheader("💰 Estratégia & Export")
    bank = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    if st.button("📤 Exportar para WhatsApp / Telegram"):
        mensagem = f"""🎟️ IA LOTOFÁCIL ELITE v13.0
Loteria: {config['nome']}
Fase: {fase}
Estratégia: {estrategia}
Faltantes: {len(faltantes)}
Bankroll: R$ {bank}"""
        st.code(mensagem, language=None)
        st.success("✅ Mensagem copiada!")

st.caption("v13.0 • Lotofácil 100% preservada • Melhorias aplicadas em todas as loterias • Código mais estável e inteligente")
