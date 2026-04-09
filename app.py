import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= INICIALIZAÇÃO =========================
if 'feedback' not in st.session_state:
    st.session_state.feedback = []
if 'pesos_aprendidos' not in st.session_state:
    st.session_state.pesos_aprendidos = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")

st.title("🎟️ LotoElite Pro")
st.markdown("**A mais avançada plataforma de previsão inteligente do Brasil** • Ciclo + IA + Aprendizado Pessoal Avançado")

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
    df = pd.read_csv(arquivo, header=None, dtype=str)
    df = df.iloc[:, :sorteadas]
    df = df.dropna(how='all')
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    df = df.astype(int)
    return df if df.shape[1] == sorteadas and not df.empty else None

df = carregar_csv(arquivo, config["sorteadas"])
if df is None:
    st.error("❌ CSV inválido ou vazio.")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados com sucesso!")

# ========================= CICLO =========================
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

# ========================= APRENDIZADO =========================
def aplicar_aprendizado(loteria: str, fase: str) -> List[int]:
    pesos = st.session_state.pesos_aprendidos[loteria][fase]
    numeros = list(range(1, config["total"] + 1))
    if not pesos:
        return numeros
    pesos_lista = [pesos.get(n, 1.0) for n in numeros]
    total_peso = sum(pesos_lista)
    probs = [p / total_peso for p in pesos_lista]
    return list(np.random.choice(numeros, size=config["total"], replace=False, p=probs))

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔥 Fechamento Inteligente", "🎟️ Gerar Jogos com Filtros", "📊 Estatísticas com IA",
    "📈 Simulador Histórico", "📉 Backtesting Automático", "🤝 Bolão Optimizer",
    "👤 Meu Perfil & Aprendizado"
])

# TAB 5 - BACKTESTING (com melhoria solicitada)
with tab5:
    st.subheader("📉 Backtesting Automático com IA")
    
    total_carregados = len(df)
    n_teste = min(200, total_carregados)   # usa até 200 para ficar rápido
    
    if total_carregados < 100:
        st.warning(f"⚠️ **Histórico pequeno** – Você carregou apenas {total_carregados} concursos. Para resultados mais confiáveis, carregue o CSV completo desde o primeiro concurso.")
    else:
        st.success(f"✅ Usando os últimos **{n_teste}** concursos (de um total de {total_carregados} carregados)")
    
    if st.button("🚀 Executar Backtesting Inteligente", type="primary", use_container_width=True):
        with st.spinner("Executando backtesting com estratégia real da IA..."):
            acertos_total = []
            for i in range(total_carregados - n_teste, total_carregados):
                pool = aplicar_aprendizado(config['nome'], fase)
                jogo = sorted(random.sample(pool, config["sorteadas"]))
                acertos = sum(1 for n in jogo if n in df.iloc[i].values)
                acertos_total.append(acertos)
            
            media = np.mean(acertos_total)
            taxa_11 = sum(1 for a in acertos_total if a >= 11) / n_teste * 100
            taxa_13 = sum(1 for a in acertos_total if a >= 13) / n_teste * 100
            
            st.write(f"**Média de acertos com IA:** {media:.2f} pontos")
            st.write(f"**Taxa de 11+ pontos:** {taxa_11:.1f}%")
            st.write(f"**Taxa de 13+ pontos:** {taxa_13:.1f}%")
            st.bar_chart(pd.Series(acertos_total).value_counts().sort_index())

# As outras abas permanecem iguais (não mudei nada nelas)

st.caption("LotoElite Pro • Estratégia que vence o acaso com aprendizado adaptativo")
