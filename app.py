import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO")
st.markdown("**Ciclo 4-6 sorteios | Memoria 9-11 | IA Ultra Focus • v49.4**")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofacil": {"nome": "Lotofacil", "total": 25, "sorteadas": 15, "mantidas": [9, 11]},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "mantidas": [35, 40]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4]},
    "Milionaria": {"nome": "Milionaria", "total": 50, "sorteadas": 6, "mantidas": [3, 4]},
}

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]
st.success("**{}** — Ciclo fecha em 4-6 sorteios | Mantem {}-{} dezenas".format(
    config['nome'], config['mantidas'][0], config['mantidas'][1]))

arquivo = st.file_uploader("CSV de {}".format(config['nome']), type=["csv"])
if arquivo is None: 
    st.warning("Envie o CSV pra continuar")
    st.stop()

try:
    df = pd.read_csv(arquivo, header=None)
    df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
    st.success("OK {} concursos carregados!".format(len(df)))
except Exception as e:
    st.error("Erro ao ler CSV: {}".format(e))
    st.stop()

# ========================= FUNCOES =========================
def analisar_ciclo_completo(df, config):
    total = config["total"]
    mantidas_min, mantidas_max = config["mantidas"]
    ciclos = []
    ciclo_atual = []
    dezenas_vistas = set()

    for idx, row in df.iterrows():
        ciclo_atual.append(idx)
        dezenas_vistas.update([int(x) for x in row.values])
        if len(dezenas_vistas) == total:
            ciclos.append({
                "inicio": ciclo_atual[0], "fim": ciclo_atual[-1],
                "duracao": len(ciclo_atual),
                "dezenas_final": set([int(x) for x in df.iloc[ciclo_atual[-1], :config["sorteadas"]].values])
            })
            ciclo_atual = []
            dezenas_vistas = set()

    faltantes = sorted(set(range(1, total+1)) - dezenas_vistas)
    progresso_raw = len(dezenas_vistas) / total if total > 0 else 0.0
    progresso = float(max(0.0, min(1.0, progresso_raw)))
    sorteios_ciclo = len(ciclo_atual)

    if sorteios_ciclo == 0: 
        fase, boost = "ZERADO", 20
    elif sorteios_ciclo <= 3: 
        fase, boost = "INICIO", 5
    elif sorteios_ciclo <= 5: 
        fase, boost = "MEIO", 10
    else: 
        fase, boost = "FIM", 18

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    quentes = [int(x) for x in np.argsort(np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:])[-15:][::-1] + 1]

    return {
        "fase": fase, "faltantes": [int(x) for x in faltantes], "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "boost": boost, "memoria": [int(x) for x in memoria],
        "ciclos_hist": ciclos, "previsao_fecha": max(0, 6 - sorteios_ciclo),
        "quentes": quentes
    }

def gerar_jogo_ciclo(config, analise, modo="AVANCADO"):
    faltantes, memoria = analise["faltantes"], analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    jogo = []

    if modo == "ULTRA_FOCUS":
        faltantes_shuffled = random.sample(faltantes, len(faltantes))
        jogo = faltantes_shuffled[:total_jogo]
        if len(jogo) < total_jogo:
            mem_shuffled = random.sample(memoria, len(memoria))
            jogo.extend([m for m in mem_shuffled if m not in jogo][:total_jogo - len(jogo)])
    
    elif modo == "SUPER_FOCUS":
        qtd_f = min(int(total_jogo * 0.6), len(faltantes))
        qtd_m = min(random.randint(m_min, m_max), len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))
    
    elif modo == "AVANCADO":
        qtd_f = min(int(total_jogo * 0.4), len(faltantes))
        qtd_m = min(m_min, len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))
    
    else: # MODERADO
        qtd_f = min(int(total_jogo * 0.3), len(faltantes))
        qtd_m = min(m_min - 1, len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))

    quentes_disp = [q for q in analise["quentes"] if q not in jogo]
