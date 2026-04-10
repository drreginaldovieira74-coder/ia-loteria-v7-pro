import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**Ciclo 4-6 sorteios | Memória 9-11 | IA Ultra Focus • v48.3**")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15, "mantidas": [9, 11]},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "mantidas": [35, 40]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4]},
    "Milionária": {"nome": "Milionária", "total": 50, "sorteadas": 6, "mantidas": [3, 4]},
}

loteria = st.selectbox("🎯 Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]
st.success(f"**{config['nome']}** — Ciclo fecha em 4-6 sorteios | Mantém {config['mantidas'][0]}-{config['mantidas'][1]} dezenas")

arquivo = st.file_uploader(f"CSV de {config['nome']}", type=["csv"])
if arquivo is None: 
    st.warning("Envie o CSV pra continuar")
    st.stop()

try:
    df = pd.read_csv(arquivo, header=None)
    df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
    st.success(f"✅ {len(df)} concursos carregados!")
except Exception as e:
    st.error(f"Erro ao ler CSV: {e}")
    st.stop()

# ========================= MOTOR CICLO 4-6 + MEMÓRIA 9-11 =========================
def analisar_ciclo_completo(df, config):
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
                "inicio": ciclo_atual[0], "fim": ciclo_atual[-1],
                "duracao": len(ciclo_atual),
                "dezenas_final": set(df.iloc[ciclo_atual[-1], :config["sorteadas"]].values)
            })
            ciclo_atual = []
            dezenas_vistas = set()

    faltantes = sorted(set(range(1, total+1)) - dezenas_vistas)
    progresso = len(dezenas_vistas) / total
    sorteios_ciclo = len(ciclo_atual)

    if sorteios_ciclo == 0: fase, boost = "ZERADO", 20
    elif sorteios_ciclo <= 3: fase, boost = "INÍCIO", 5
    elif sorteios_ciclo <= 5: fase, boost = "MEIO", 10
    else: fase, boost = "FIM", 18

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    quentes = np.argsort(np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:])[-15:][::-1] + 1

    return {
        "fase": fase, "faltantes": faltantes, "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "boost": boost, "memoria": memoria,
        "ciclos_hist": ciclos, "previsao_fecha": max(0, 6 - sorteios_ciclo),
        "quentes": quentes
    }

def gerar_jogo_ciclo(config, analise, modo="AVANÇADO"):
    faltantes, memoria = analise["faltantes"], analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    jogo = []

    if modo == "ULTRA_FOCUS":
        jogo = faltantes[:total_jogo]
        if len(jogo) < total_jogo:
            jogo.extend([m for m in memoria if m not in jogo][:total_jogo - len(jogo)])
    elif modo == "SUPER_FOCUS":
        qtd_f = min(int(total_jogo * 0.6), len(faltantes))
        qtd_m = min(random.randint(m_min, m_max), len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))
    elif modo == "AVANÇADO":
        qtd_f = min(int(total_jogo * 0.4), len(faltantes))
        qtd_m = min(m_min, len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))
    else: # MODERADO
        qtd_f = min(int(total_jogo * 0.3), len(faltantes))
        qtd_m = min(m_min - 1, len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))

    quentes_disp = [q for q in analise["quentes"] if q not in jogo]
    while len(jogo) < total_jogo and len(quentes_disp) > 0:
        jogo.append(quentes_disp.pop(0))

    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo: jogo.append(candidato)

    return sorted(jogo[:total_jogo])

def fechamento_inteligente_3jogos(config, analise):
    faltantes, memoria, quentes = analise["faltantes"], analise["memoria"], analise["quentes"]
    jogos = []

    j1 = gerar_jogo_ciclo(config, analise, "ULTRA_FOCUS")
    jogos.append({"nome": "Fechar Ciclo", "jogo": j1, "estrategia": "100% faltantes + memória"})

    base = memoria[:config["mantidas"][1]] if len(memoria) >= config["mantidas"][0] else memoria
    resto = [q for q in quentes if q not in base]
    j2 = sorted(base + random.sample(resto, min(len(resto), config["sorteadas"] - len(base))))
    jogos.append({"nome": "Memória Pura", "jogo": j2, "estrategia": f"{len(base)} mantidas + quentes"})

    if len(faltantes) >= config["sorteadas"]:
        j3 = sorted(random.sample(faltantes, config["sorteadas"]))
    else:
        j3 = sorted(faltantes + random.sample([q for q in quentes if q not in faltantes], config["sorteadas"] - len(faltantes)))
    jogos.append({"nome": "Ataque Faltantes", "jogo": j3, "estrategia": "Máximo de faltantes"})

    return jogos

# ========================= 7 ABAS CRIADAS PRIMEIRO =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎟️ Gerador de Jogos", "📊 Estatísticas", "🔄 Simulador Histórico",
    "🧪 Backtesting com IA", "👤 Meu Perfil", "💰 Bankroll", "🔒 Fechamentos Inteligentes"
])

# Analisa o ciclo uma vez só
try:
    analise = analisar_ciclo_completo(df, config)
except Exception as e:
    st.error(f"Erro ao analisar ciclo: {e}")
    st.stop()

with tab1:
    st.subheader("Gerador de Jogos – Ciclo 4-6 como Motor")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase do Ciclo", analise["fase"], f"{analise['sorteios_ciclo']}º sorteio")
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memória", len(analise["memoria"]))
    c4.metric("Fecha em", f"{analise['previsao_fecha']} concursos")

    if analise["fase"] == "FIM":
        st.error(f"🔥 FIM DE CICLO! {len(analise['faltantes'])} faltantes. Hora de atacar!")
    elif analise["fase"] == "MEIO":
        st.warning(f"⚖️ MEIO DO CICLO. {6-analise['sorteios_ciclo']} sorteios pro fim")
    else:
        st.info(f"🌱 INÍCIO. Ciclo formando, {analise['sorteios_ciclo']}º sorteio")

    modo_focus = st.select_slider("Modo Ultra Focus", ["MOD
