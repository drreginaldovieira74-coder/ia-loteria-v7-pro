import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="IA LOTOFÁCIL ELITE v11.0", page_icon="🎟️", layout="wide")

st.title("🎟️ IA LOTOFÁCIL ELITE v11.0 – MULTI-LOTERIA MASTER")
st.markdown("**Versão 100% robusta e corrigida**")

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

# ========================= UPLOAD =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV com apenas números")
    st.stop()

# ====================== CARREGAMENTO ULTRA ROBUSTO ======================
@st.cache_data
def carregar_csv(arquivo, sorteadas):
    # Lê como string para evitar qualquer erro
    df = pd.read_csv(arquivo, header=None, dtype=str)
    
    # Pega só as colunas necessárias
    df = df.iloc[:, :sorteadas]
    
    # Remove linhas completamente vazias
    df = df.dropna(how='all')
    
    # Converte para número (qualquer coisa que não for número vira NaN)
    df = df.apply(pd.to_numeric, errors='coerce')
    
    # Remove linhas com qualquer NaN
    df = df.dropna()
    
    # Converte para inteiro
    df = df.astype(int)
    
    return df

df = carregar_csv(arquivo, config["sorteadas"])

if len(df) == 0:
    st.error("❌ O CSV está vazio ou inválido.\n\nCertifique-se de que contém **apenas números** (sem linha de cabeçalho D1,D2...).")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados com sucesso!")

# ========================= MOTOR DE CICLO (com proteção total) =========================
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
        
        # PROTEÇÃO EXTRA
        if len(df_atual) == 0:
            return "INÍCIO", list(range(1, config["total"]+1)), 0.0
        
        # Agora é seguro fazer concatenate
        cobertura_atual = set(np.concatenate(df_atual.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - cobertura_atual)
        progresso = len(cobertura_atual) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

    # Para as outras loterias
    ultimos = df.iloc[-40:] if len(df) > 40 else df
    todos = set(np.concatenate(ultimos.values))
    faltantes = sorted(set(range(1, config["total"]+1)) - todos)
    progresso = (config["total"] - len(faltantes)) / config["total"] * 100
    fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
    return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# ========================= TESTE RÁPIDO =========================
st.subheader("🔥 Status do Ciclo")
col1, col2, col3 = st.columns(3)
col1.metric("Fase", f"**{fase}**")
col2.metric("Faltantes", f"**{len(faltantes)}**")
col3.metric("Progresso", f"{progresso:.1f}%")

st.success("✅ Sistema carregou corretamente! Agora teste gerando jogos.")

st.caption("v11.0 MULTI-LOTERIA • Versão ultra robusta e corrigida")
