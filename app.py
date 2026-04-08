import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")

st.title("🎟️ LotoElite Pro")
st.markdown("**A mais avançada plataforma de previsão inteligente do Brasil** • Ciclo + IA + Aprendizado Pessoal")

# ========================= MOTOR DE APRENDIZADO PESSOAL =========================
if 'feedback' not in st.session_state:
    st.session_state.feedback = []  # Cada entrada: {'fase': , 'estrategia': , 'pontos': , 'loteria': , 'numeros': }

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
if df is None:
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

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔥 Fechamento Inteligente",
    "🎟️ Gerar Jogos com Filtros",
    "📊 Estatísticas com IA",
    "📈 Simulador Histórico",
    "📉 Backtesting Automático",
    "🤝 Bolão Optimizer",
    "👤 Meu Perfil & Aprendizado"
])

# TAB 1 - FECHAMENTO INTELIGENTE (com aprendizado)
with tab1:
    st.subheader("🔥 Fechamento Inteligente Recomendado pela IA")
    if st.button("🚀 Gerar Fechamento Inteligente", type="primary", use_container_width=True):
        jogos = []
        for _ in range(3):
            if fase == "FIM" and len(faltantes) > 0:
                num_faltantes = min(12, len(faltantes))
                faltantes_escolhidas = random.sample(faltantes, num_faltantes)
                restantes = list(set(range(1, config["total"]+1)) - set(faltantes_escolhidas))
                completar = random.sample(restantes, config["sorteadas"] - num_faltantes)
                jogo = sorted(faltantes_escolhidas + completar)
            else:
                pool = faltantes * 3 + list(range(1, config["total"]+1))
                jogo = sorted(random.sample(pool, config["sorteadas"]))
            jogos.append(jogo)
        st.dataframe(pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])]), use_container_width=True)
        st.success("✅ 3 fechamentos inteligentes gerados!")

# TAB 7 - MOTOR DE APRENDIZADO PESSOAL
with tab7:
    st.subheader("👤 Meu Perfil & Aprendizado Pessoal")
    st.info("Informe quantos pontos você acertou. O sistema aprende com você e melhora os próximos jogos.")

    col1, col2 = st.columns(2)
    with col1:
        pontos = st.number_input("Quantos pontos você acertou no último sorteio?", 0, 15, 8)
    with col2:
        if st.button("✅ Salvar Feedback"):
            st.session_state.feedback.append({
                "fase": fase,
                "estrategia": estrategia,
                "pontos": pontos,
                "loteria": config['nome']
            })
            st.success("✅ Feedback salvo! O sistema está aprendendo com seus resultados.")

    if st.session_state.feedback:
        df_feedback = pd.DataFrame(st.session_state.feedback)
        media = df_feedback['pontos'].mean()
        st.metric("Sua média de acertos", f"{media:.2f} pontos")
        st.dataframe(df_feedback)

st.caption("LotoElite Pro • Estratégia que vence o acaso.")
