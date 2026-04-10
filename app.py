import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO v50.4")
st.markdown("**Ciclo por Loteria | Memoria 9-11 | IA Ultra Focus**")

loteria_options = {
    "Lotofacil": {
        "nome": "Lotofacil", "total": 25, "sorteadas": 15, 
        "mantidas": [9, 11], "ciclo_esperado": [4, 6], "fase_limites": [2, 4]
    },
    "Lotomania": {
        "nome": "Lotomania", "total": 100, "sorteadas": 50, 
        "mantidas": [35, 40], "ciclo_esperado": [8, 12], "fase_limites": [4, 8]
    },
    "Quina": {
        "nome": "Quina", "total": 80, "sorteadas": 5, 
        "mantidas": [2, 3], "ciclo_esperado": [35, 50], "fase_limites": [15, 35]
    },
    "Mega-Sena": {
        "nome": "Mega-Sena", "total": 60, "sorteadas": 6, 
        "mantidas": [3, 4], "ciclo_esperado": [22, 30], "fase_limites": [10, 22]
    },
    "Milionaria": {
        "nome": "Milionaria", "total": 50, "sorteadas": 6, 
        "mantidas": [3, 4], "ciclo_esperado": [18, 25], "fase_limites": [8, 18]
    }
}

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]

st.success("**{}** — Ciclo fecha em {}-{} sorteios | Mantem {}-{} dezenas | Total: {} dezenas".format(
    config['nome'], 
    config['ciclo_esperado'][0], 
    config['ciclo_esperado'][1], 
    config['mantidas'][0], 
    config['mantidas'][1], 
    config['total']
))

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

def analisar_ciclo_completo(df, config):
    total = config["total"]
    ciclo_min, ciclo_max = config["ciclo_esperado"]
    lim_inicio, lim_meio = config["fase_limites"]
    
    ciclos = []
    ciclo_atual = []
    dezenas_vistas = set()

    for idx, row in df.iterrows():
        ciclo_atual.append(idx)
        dezenas_vistas.update([int(x) for x in row.values])
        if len(dezenas_vistas) == total:
            ciclos.append({
                "inicio": ciclo_atual[0], 
                "fim": ciclo_atual[-1],
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
    elif sorteios_ciclo <= lim_inicio: 
        fase, boost = "INICIO", 5
    elif sorteios_ciclo <= lim_meio: 
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
        "ciclos_hist": ciclos, "previsao_fecha": max(0, ciclo_max - sorteios_ciclo),
        "quentes": quentes, "ciclo_esperado": config["ciclo_esperado"]
    }

def gerar_jogo_ciclo(config, analise, modo="AVANCADO", ordenar_visual=False):
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    jogo = []

    if modo == "ULTRA_FOCUS":
        if len(faltantes) >= total_jogo:
            jogo = random.sample(faltantes, total_jogo)
        else:
            jogo = faltantes.copy() if len(faltantes) > 0 else []
            mem_shuffled = random.sample(memoria, min(len(memoria), total_jogo - len(jogo)))
            jogo.extend([m for m in mem_shuffled if m not in jogo])
    
    elif modo == "SUPER_FOCUS":
        qtd_f = min(int(total_jogo * 0.6), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        qtd_m = min(random.randint(m_min, m_max), len(mem_disp), max(0, total_jogo - len(jogo)))
        if qtd_m > 0: 
            jogo.extend(random.sample(mem_disp, qtd_m))
    
    elif modo == "AVANCADO":
        qtd_f = min(int(total_jogo * 0.4), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        qtd_m = min(m_min, len(mem_disp), max(0, total_jogo - len(jogo)))
        if qtd_m > 0: 
            jogo.extend(random.sample(mem_disp, qtd_m))
    
    else:
        qtd_f = min(int(total_jogo * 0.3), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        qtd_m = min(m_min - 1, len(mem_disp), max(0, total_jogo - len(jogo)))
        if qtd_m > 0: 
            jogo.extend(random.sample(mem_disp, qtd_m))

    quentes_disp = [q for q in analise["quentes"] if q not in jogo]
    while len(jogo) < total_jogo and len(quentes_disp) > 0:
        jogo.append(quentes_disp.pop(0))

    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo: 
            jogo.append(candidato)

    jogo = [int(x) for x in jogo[:total_jogo]]
