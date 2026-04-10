import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**Ciclo com validação estatística • v46.2 - Sem dependências**")

# ========================= FUNÇÕES ESTATÍSTICAS SEM SCIPY =========================
def qui_quadrado(freq_obs, freq_esp):
    """Qui-quadrado manual pra não depender de scipy"""
    chi2 = np.sum((freq_obs - freq_esp) ** 2 / freq_esp)
    return chi2

def p_valor_aproximado(chi2, graus_liberdade):
    """Aproximação de p-valor sem scipy. Se chi2 > valor crítico, p < 0.05"""
    # Valores críticos pra 95% confiança
    criticos = {24: 36.4, 49: 66.3, 59: 77.9, 79: 100.7, 99: 123.2}
    critico = criticos.get(graus_liberdade, 3.84) # fallback
    p_aprox = 0.01 if chi2 > critico * 1.5 else 0.06 if chi2 > critico else 0.5
    return p_aprox

def entropia(x):
    """Entropia de Shannon sem scipy"""
    x = x[x > 0] # remove zeros
    probs = x / np.sum(x)
    return -np.sum(probs * np.log(probs))

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6},
    "Milionária": {"nome": "Milionária", "total": 50, "sorteadas": 6},
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]
st.success(f"Loteria: **{config['nome']}** — Ciclo validado sem dependências externas")

# ========================= UPLOAD =========================
arquivo = st.file_uploader(f"Envie o CSV de {config['nome']}", type=["csv"])
if arquivo is None:
    st.stop()

try:
    df = pd.read_csv(arquivo, header=None)
    df = df.iloc[:, :config["sorteadas"]].dropna()
    df = df.astype(int)
except Exception as e:
    st.error(f"Erro ao ler CSV: {e}")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados!")

# ========================= MOTOR DE CICLO =========================
def detectar_ciclo_robusto(df, config, idx_final=None, janela=20):
    if idx_final is None:
        idx_final = len(df)
    if idx_final < janela:
        return "DADOS_INSUFICIENTES", [], 1.0, 0.0, np.array([])

    historico = df.iloc[idx_final-janela:idx_final, :config["sorteadas"]].values
    freq = np.bincount(historico.flatten(), minlength=config["total"]+1)[1:]

    esperado = janela * config["sorteadas"] / config["total"]
    esperado_array = np.array([esperado] * config["total"])

    chi2 = qui_quadrado(freq, esperado_array)
    p_valor = p_valor_aproximado(chi2, config["total"] - 1)
    ent = entropia(freq + 1e-9)
    faltantes = np.where(freq == 0)[0] + 1

    if p_valor < 0.05 and ent < 3.1:
        fase = "CICLO_ATIVO"
        boost = 15 * (1 - p_valor) * (3.2 - ent)
    elif p_valor < 0.05:
        fase = "PADRÃO_FRACO"
        boost = 5 * (1 - p_valor)
    else:
        fase = "ALEATÓRIO"
        boost = 0

    return fase, faltantes.tolist(), p_valor, round(boost, 2), freq

def backtest_walkforward(df, config, janela=20):
    resultados = []
    for i in range(janela + 10, len(df)):
        fase, faltantes, p_valor, boost, _ = detectar_ciclo_robusto(df, config, idx_final=i, janela=janela)
        if fase == "CICLO_ATIVO" and len(faltantes) >= config["sorteadas"]:
            jogo = sorted(random.sample(faltantes, config["sorteadas"]))
        elif len(faltantes) > 0:
            qtd_faltantes = min(int(config["sorteadas"] * 0.7), len(faltantes))
            qtd_outras = config["sorteadas"] - qtd_faltantes
            outras = [n for n in range(1, config["total"]+1) if n not in faltantes]
            jogo = sorted(random.sample(faltantes, qtd_faltantes) + random.sample(outras, qtd_outras))
        else:
            jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
        sorteado = set(df.iloc[i, :config["sorteadas"]].values)
        acerto = len(set(jogo) & sorteado)
        resultados.append({"concurso": i + 1, "acertos": acerto, "fase": fase, "p_valor": p_valor, "boost": boost})
    return pd.DataFrame(resultados)

# ========================= INTERFACE =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎟️ Gerador", "📊 Diagnóstico", "🧪 Backtesting", "🔬 Teste vs Aleatório"
])

with tab1:
    st.subheader("Gerador com Ciclo Validado")
    janela = st.slider("Janela de análise", 10, 50, 20, key="janela_gerador")
    fase, faltantes, p_valor, boost, freq = detectar_ciclo_robusto(df, config, janela=janela)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fase", fase)
    col2.metric("p-valor aprox.", f"{p_valor:.2f}")
    col3.metric("Boost", f"{boost}x")
    col4.metric("Faltantes", len(faltantes))

    if fase == "ALEATÓRIO":
        st.warning("⚠️ Ciclo não é estatisticamente relevante. Boost zerado.")
    elif fase == "CICLO_ATIVO":
        st.success(f"✅ Ciclo ativo! Força: {boost}x")

    qtd = st.slider("Quantos jogos?", 1, 50, 10)
    if st.button("🚀 GERAR JOGOS", type="primary"):
        jogos = []
        for _ in range(qtd):
            if fase == "CICLO_ATIVO" and len(faltantes) >= config["sorteadas"]:
                qtd_falt = min(int(config["sorteadas"] * 0.8), len(faltantes))
                outras = [n for n in range(1, config["total"]+1) if n not in faltantes]
                jogo = sorted(random.sample(faltantes, qtd_falt) + random.sample(outras, config["sorteadas"] - qtd_falt))
            else:
                jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
            jogos.append(jogo)
        for i, j in enumerate(jogos, 1):
            st.code(f"Jogo {i:02d}: {j}")

with tab2:
    st.subheader("📊 Diagnóstico do Ciclo")
    janela_diag = st
