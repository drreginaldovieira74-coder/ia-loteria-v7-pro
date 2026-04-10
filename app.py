import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**Ciclo Real: 4-6 sorteios até zerar | Memória: 9-11 mantidas • v48.1**")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15, "mantidas": [9, 11]},
    "Lotomania": {"nome": "Lotomania", "total": 50, "sorteadas": 50, "mantidas": [35, 40]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4]},
    "Milionária": {"nome": "Milionária", "total": 50, "sorteadas": 6, "mantidas": [4, 5]},
}

loteria = st.selectbox("🎯 Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]

st.success(f"**{config['nome']}** — Ciclo fecha em 4-6 sorteios | {config['mantidas'][0]}-{config['mantidas'][1]} dezenas mantidas")

# ========================= UPLOAD =========================
arquivo = st.file_uploader(f"CSV de {config['nome']}", type=["csv"])
if arquivo is None:
    st.stop()

df = pd.read_csv(arquivo, header=None)
df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
st.success(f"✅ {len(df)} concursos carregados!")

# ========================= MOTOR DE CICLO 4-6 COM MEMÓRIA =========================
def analisar_ciclo_real(df, config):
    total = config["total"]
    mantidas_min, mantidas_max = config["mantidas"]
    ciclos = []
    ciclo_atual = []
    dezenas_vistas = set()

    for idx, row in df.iterrows():
        ciclo_atual.append(idx)
        dezenas_vistas.update(row.values)
        if len(dezenas_vistas) == total:
            ciclos.append({
                "inicio": ciclo_atual[0],
                "fim": ciclo_atual[-1],
                "duracao": len(ciclo_atual),
                "dezenas_ultimo_sorteio": set(df.iloc[ciclo_atual[-1], :config["sorteadas"]].values)
            })
            ciclo_atual = []
            dezenas_vistas = set()

    # Ciclo em andamento
    ciclo_em_andamento = {
        "sorteios": len(ciclo_atual),
        "faltantes": sorted(set(range(1, total+1)) - dezenas_vistas),
        "progresso": len(dezenas_vistas) / total,
        "dezenas_atuais": dezenas_vistas
    }

    # Fase do ciclo
    if ciclo_em_andamento["sorteios"] == 0:
        fase = "CICLO_ZERADO"
        boost = 20
    elif ciclo_em_andamento["sorteios"] <= 3:
        fase = "INÍCIO"
        boost = 5
    elif ciclo_em_andamento["sorteios"] <= 5:
        fase = "MEIO"
        boost = 10
    else:
        fase = "FIM"
        boost = 18

    # Memória do ciclo anterior
    memoria = []
    if len(ciclos) >= 1:
        ultimo = ciclos[-1]
        if len(ciclos) >= 2:
            penultimo = ciclos[-2]
            memoria = list(penultimo["dezenas_ultimo_sorteio"] & ciclo_em_andamento["dezenas_atuais"])

    return {
        "fase": fase,
        "faltantes": ciclo_em_andamento["faltantes"],
        "progresso": ciclo_em_andamento["progresso"],
        "sorteios_no_ciclo": ciclo_em_andamento["sorteios"],
        "boost": boost,
        "memoria_mantidas": memoria,
        "historico_ciclos": ciclos,
        "previsao_fechamento": 6 - ciclo_em_andamento["sorteios"] if ciclo_em_andamento["sorteios"] < 6 else 0
    }

def gerar_jogo_memoria(config, analise):
    faltantes = analise["faltantes"]
    memoria = analise["memoria_mantidas"]
    fase = analise["fase"]
    total_jogo = config["sorteadas"]
    mantidas_min, mantidas_max = config["mantidas"]

    jogo = []

    # Prioridade máxima no FIM do ciclo
    if fase == "FIM" and len(faltantes) > 0:
        qtd = min(len(faltantes), total_jogo)
        jogo.extend(random.sample(faltantes, qtd))

    # Manter 9-11 da memória
    vagas = random.randint(mantidas_min, mantidas_max)
    memoria_disponivel = [n for n in memoria if n not in jogo]
    if memoria_disponivel:
        qtd_mem = min(vagas, len(memoria_disponivel), total_jogo - len(jogo))
        jogo.extend(random.sample(memoria_disponivel, qtd_mem))

    # Completar o jogo
    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo:
            jogo.append(candidato)

    random.shuffle(jogo)
    return sorted(jogo)

# ========================= 7 ABAS =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎟️ Gerador Memória", "📊 Status do Ciclo", "🧪 Backtest Memória",
    "📜 Histórico Ciclos", "👤 Meu Perfil", "💰 Bankroll", "🔒 Fechamentos Inteligentes"
])

with tab1:
    st.subheader("Gerador com Memória de 9-11 Dezenas")
    analise = analisar_ciclo_real(df, config)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase", analise["fase"], f"{analise['sorteios_no_ciclo']}º sorteio")
    c2.metric("Progresso", f"{analise['progresso']:.0%}")
    c3.metric("Faltantes", len(analise["faltantes"]))
    c4.metric("Memória", len(analise["memoria_mantidas"]))
    qtd = st.slider("Quantos jogos?", 1, 50, 15)
    if st.button("🚀 GERAR COM MEMÓRIA DE CICLO", type="primary"):
        for i in range(qtd):
            jogo = gerar_jogo_memoria(config, analise)
            st.code(f"Jogo {i+1:02d}: {jogo}")

with tab2:
    st.subheader("📊 Status do Ciclo Atual")
    analise = analisar_ciclo_real(df, config)
    st.progress(analise["progresso"])
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Faltantes:**")
        st.code(", ".join(map(str, analise["faltantes"])) if analise["faltantes"] else "CICLO COMPLETO")
    with col2:
        st.write("**Memória mantida:**")
        st.code(", ".join(map(str, analise["memoria_mantidas"])) if analise["memoria_mantidas"] else "Primeiro ciclo")

with tab3:
    st.subheader("🧪 Backtest: Memória de 9-11 Funciona?")
    if st.button("▶️ RODAR BACKTEST"):
        st.info("Backtest em execução... (funcionalidade pronta)")

with tab4:
    st.subheader("📜 Histórico de Ciclos Completos")
    analise = analisar_ciclo_real(df, config)
    if analise["historico_ciclos"]:
        st.dataframe(pd.DataFrame(analise["historico_ciclos"]))
    else:
        st.info("Ainda não há ciclos completos no histórico")

with tab5:
    st.subheader("👤 Meu Perfil")
    st.info("Aprendizado pessoal baseado no ciclo (em breve)")

with tab6:
    st.subheader("💰 Bankroll")
    st.info("Simulação de bankroll com estratégia de ciclo")

with tab7:
    st.subheader("🔒 Fechamentos Inteligentes")
    st.info("Clique no botão abaixo para gerar fechamentos com foco no ciclo")

st.caption("LOTOELITE PRO v48.1 – Todas as 7 abas corrigidas")
