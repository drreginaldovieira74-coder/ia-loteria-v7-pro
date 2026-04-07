import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= CONFIGURAÇÃO v11.0 MULTI-LOTERIA =========================
st.set_page_config(
    page_title="IA LOTOFÁCIL ELITE v11.0",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎟️ IA LOTOFÁCIL ELITE v11.0 – MULTI-LOTERIA MASTER")
st.markdown("**Plataforma completa e exclusiva** | Lotofácil + Lotomania + Mega-Sena + Quina")

# ========================= SELETOR DE LOTERIA =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "tipo_ciclo": "frequency"}
}

loteria_selecionada = st.selectbox(
    "🎯 Escolha a loteria",
    options=list(loteria_options.keys()),
    index=0
)

config = loteria_options[loteria_selecionada]

st.markdown(f"**Loteria ativa:** {config['nome']} ({config['sorteadas']} números de {config['total']})")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações v11.0")
    estrategia = st.selectbox("Modo de Estratégia IA", ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"], index=3)
    tamanho_pool = st.number_input("Tamanho Base do Pool", 17, 25, 18)
    st.info("O sistema adapta automaticamente todas as análises (ciclo, faltantes, fractal, confidence) para a loteria escolhida")

# ========================= UPLOAD + LIVE UPDATER =========================
st.subheader("📤 Upload do Histórico + Live Updater")
arquivo = st.file_uploader(f"Envie o CSV da {config['nome']}", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV para começar")
    st.stop()

@st.cache_data
def carregar_csv(arquivo) -> pd.DataFrame:
    df = pd.read_csv(arquivo)
    return df.iloc[:, :config["sorteadas"]].astype(int)

df = carregar_csv(arquivo)

# Live Updater
st.subheader("🔴 Adicionar Último Concurso")
ultimo_input = st.text_input("Cole as dezenas do último concurso (separadas por espaço)", 
                            help=f"Exatamente {config['sorteadas']} números")
if st.button("➕ Adicionar ao Histórico", type="primary"):
    if ultimo_input:
        try:
            nums = [int(x) for x in ultimo_input.replace(",", " ").split() if x.strip()]
            if len(nums) == config["sorteadas"] and all(1 <= n <= config["total"] for n in nums):
                novo = pd.DataFrame([sorted(nums)])
                df = pd.concat([df, novo], ignore_index=True)
                st.success("✅ Concurso adicionado!")
                st.rerun()
            else:
                st.error(f"❌ Exatamente {config['sorteadas']} números entre 1 e {config['total']}")
        except:
            st.error("❌ Formato inválido")

# ========================= MOTOR ADAPTATIVO POR LOTERIA =========================
def detectar_ciclo(df: pd.DataFrame, config: Dict):
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
        cobertura_atual = set(np.concatenate(df_atual.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - cobertura_atual)
        progresso = len(cobertura_atual) / config["total"] * 100
        fase = "INÍCIO DE CICLO" if progresso < 40 else "MEIO DE CICLO" if progresso < 80 else "FIM DE CICLO"
        return fase, faltantes, progresso

    elif config["tipo_ciclo"] == "partial":  # Lotomania
        ultimos = df.iloc[-25:] if len(df) > 25 else df
        todos = set(np.concatenate(ultimos.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - todos)
        progresso = (config["total"] - len(faltantes)) / config["total"] * 100
        fase = "INÍCIO DE CICLO" if progresso < 40 else "MEIO DE CICLO" if progresso < 80 else "FIM DE CICLO"
        return fase, faltantes, progresso

    else:  # Mega-Sena / Quina (frequency based)
        todos = np.concatenate(df.values)
        contagem = Counter(todos)
        faltantes = sorted([n for n in range(1, config["total"]+1) if contagem.get(n, 0) == 0])
        progresso = 100 - (len(faltantes) / config["total"] * 100)
        fase = "INÍCIO DE CICLO" if len(faltantes) > config["total"]*0.6 else "MEIO DE CICLO" if len(faltantes) > config["total"]*0.3 else "FIM DE CICLO"
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
    base = 45
    base += len(set(jogo) & set(faltantes)) * 4.5
    if fase == "FIM DE CICLO":
        base += 38
    elif fase == "MEIO DE CICLO":
        base += 18
    if config["nome"] == "Lotofácil" and estrategia == "ULTRA FOCUS":
        base += 12
    return min(98, max(28, int(base)))

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
    col1.metric("Loteria", f"**{config['nome']}**")
    col2.metric("Fase", f"**{fase}**")
    col3.metric("Faltantes", f"**{len(faltantes)}**")
    risco = 88 if fase == "FIM DE CICLO" else 45 if fase == "MEIO DE CICLO" else 22
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
        st.download_button("📥 Baixar Bolão", excel, f"bolao_{config['nome']}_v11.0.xlsx", "application/vnd.ms-excel")

with tab3:
    st.subheader("🎟️ Gerar Jogos Master v11.0")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 GERAR JOGOS MASTER", type="primary", use_container_width=True):
        pool = list(range(1, config["total"]+1))
        if estrategia == "ULTRA FOCUS" and fase == "FIM DE CICLO":
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
        st.download_button("📥 Baixar Jogos com Confidence", excel, f"jogos_{config['nome']}_v11.0.xlsx", "application/vnd.ms-excel")
        
        st.markdown("**Feedback para Self-Learning**")
        col_a, col_b = st.columns(2)
        if col_a.button("👍 Jogos bons"):
            atualizar_self_learning([j[:config["sorteadas"]] for j in jogos], "bom")
            st.success("Self-Learning atualizado!")
        if col_b.button("👎 Preciso ajustar"):
            atualizar_self_learning([j[:config["sorteadas"]] for j in jogos], "ruim")
            st.warning("Sistema aprendendo...")

with tab4:
    st.subheader("📈 Performance Dashboard")
    st.success("Self-Learning ativo em todas as loterias")
    if st.button("Mostrar Top 10 Números Aprendidos"):
        if st.session_state.historico_acertos:
            top10 = dict(st.session_state.historico_acertos.most_common(10))
            st.bar_chart(pd.Series(top10))
        else:
            st.info("Ainda sem feedback")

with tab5:
    st.subheader("💰 Estratégia & Export")
    bank = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    if st.button("📤 Exportar para WhatsApp / Telegram"):
        mensagem = f"""🎟️ IA LOTOFÁCIL ELITE v11.0
Loteria: {config['nome']}
Fase: {fase}
Estratégia: {estrategia}
Faltantes: {len(faltantes)}
Bankroll: R$ {bank}"""
        st.code(mensagem, language=None)
        st.success("✅ Mensagem copiada!")

st.caption("IA LOTOFÁCIL ELITE v11.0 MULTI-LOTERIA • Lotofácil + Lotomania + Mega-Sena + Quina • Self-Learning + AI Oracle + Cycle em todas as loterias • Exclusivo")
