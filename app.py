import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict
from datetime import datetime

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO v51.1")
st.markdown("**Ciclo por Loteria | Memoria | Filtros | Desdobramento | IA Híbrida**")

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

if 'historico_perfil' not in st.session_state:
    st.session_state.historico_perfil = []

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]

st.success("**{}** — Ciclo fecha em {}-{} sorteios | Mantem {}-{} dezenas | Total: {} dezenas".format(
    config['nome'], config['ciclo_esperado'][0], config['ciclo_esperado'][1], 
    config['mantidas'][0], config['mantidas'][1], config['total']
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
    elif sorteios_ciclo <= lim_inicio: 
        fase, boost = "INICIO", 5
    elif sorteios_ciclo <= lim_meio: 
        fase, boost = "MEIO", 10
    else: 
        fase, boost = "FIM", 18

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    freq = np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:]
    quentes = [int(x) for x in np.argsort(freq)[-15:][::-1] + 1]

    return {
        "fase": fase, "faltantes": [int(x) for x in faltantes], "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "boost": boost, "memoria": [int(x) for x in memoria],
        "ciclos_hist": ciclos, "previsao_fecha": max(0, ciclo_max - sorteios_ciclo),
        "quentes": quentes, "ciclo_esperado": config["ciclo_esperado"], "freq": freq
    }

def aplicar_filtros(jogo, filtros, fase):
    if not filtros.get("ativo", False):
        return True, []
    
    reprovados = []
    
    if filtros.get("soma", {}).get("ativo") and fase in filtros["soma"].get("fases", ["MEIO", "FIM"]):
        s = sum(jogo)
        if not (filtros["soma"]["min"] <= s <= filtros["soma"]["max"]):
            reprovados.append("Soma {} fora de {}-{}".format(s, filtros["soma"]["min"], filtros["soma"]["max"]))
    
    if filtros.get("pares", {}).get("ativo"):
        pares = len([x for x in jogo if x % 2 == 0])
        if not (filtros["pares"]["min"] <= pares <= filtros["pares"]["max"]):
            reprovados.append("Pares: {} fora de {}-{}".format(pares, filtros["pares"]["min"], filtros["pares"]["max"]))
    
    if filtros.get("primos", {}).get("ativo"):
        primos_set = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97}
        qtd_primos = len([x for x in jogo if x in primos_set])
        if not (filtros["primos"]["min"] <= qtd_primos <= filtros["primos"]["max"]):
            reprovados.append("Primos: {} fora de {}-{}".format(qtd_primos, filtros["primos"]["min"], filtros["primos"]["max"]))
    
    if filtros.get("sequencia_max", {}).get("ativo"):
        jogo_sorted = sorted(jogo)
        seq_max = 1
        seq_atual = 1
        for i in range(1, len(jogo_sorted)):
            if jogo_sorted[i] == jogo_sorted[i-1] + 1:
                seq_atual += 1
                seq_max = max(seq_max, seq_atual)
            else:
                seq_atual = 1
        if seq_max > filtros["sequencia_max"]["valor"]:
            reprovados.append("Sequencia de {} consecutivos".format(seq_max))
    
    return len(reprovados) == 0, reprovados

def calcular_score_jogo(jogo, analise, filtros, historico):
    score = 0
    detalhes = []
    
    faltantes_no_jogo = len(set(jogo) & set(analise["faltantes"]))
    perc_faltantes = faltantes_no_jogo / len(jogo) * 100
    score += min(40, perc_faltantes * 0.4)
    detalhes.append("Faltantes: {}% (+{:.0f}pts)".format(int(perc_faltantes), min(40, perc_faltantes * 0.4)))
    
    memoria_no_jogo = len(set(jogo) & set(analise["memoria"]))
    if len(analise["memoria"]) > 0:
        perc_mem = memoria_no_jogo / len(analise["memoria"]) * 100
        score += min(30, perc_mem * 0.3)
        detalhes.append("Memoria: {}% (+{:.0f}pts)".format(int(perc_mem), min(30, perc_mem * 0.3)))
    
    passou, repro = aplicar_filtros(jogo, filtros, analise["fase"])
    if passou:
        score += 15
        detalhes.append("Filtros: OK (+15pts)")
    else:
        detalhes.append("Filtros: Reprovado")
    
    if len(historico) > 0:
        df_hist = pd.DataFrame(historico)
        modos_bons = df_hist[df_hist['acertos'] >= config['sorteadas'] * 0.6]['modo_usado'].value_counts()
        if len(modos_bons) > 0:
            score += 15
            detalhes.append("Perfil: Match (+15pts)")
    
    return min(100, int(score)), detalhes

def gerar_jogo_ciclo(config, analise, modo="AVANCADO", ordenar_visual=False, filtros=None):
    if filtros is None:
        filtros = {"ativo": False}
    
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    tentativas = 0
    
    while tentativas < 100:
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
        
        passou, _ = aplicar_filtros(jogo, filtros, analise["fase"])
        if passou or not filtros.get("ativo"):
            if ordenar_visual:
                jogo = sorted(jogo)
            return jogo
        
        tentativas += 1
    
    if ordenar_visual:
        jogo = sorted(jogo)
    return jogo

def desdobramento_inteligente(config, analise, dezenas_base, garantia="14-15"):
    from itertools import combinations
    
    total = config["sorteadas"]
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    
    base_inteligente = list(set(faltantes + memoria))
    if len(base_inteligente) < dezenas_base:
        resto = [x for x in analise["quentes"] if x not in base_inteligente]
        base_inteligente.extend(resto[:dezenas_base - len(base_inteligente)])
    
    base_inteligente = base_inteligente[:dezenas_base]
    
    jogos = []
    if garantia == "14-15" and dezenas_base == 18:
        idx_fixas = list(range(12))
        idx_rotativas = list(range(12, 18))
        for comb in combinations(idx_rotativas, 3):
            jogo_idx = idx_fixas + list(comb)
            jogos.append(sorted([base_inteligente[i] for i in jogo_idx]))
    
    elif garantia == "14-15" and dezenas_base == 16:
        for comb in combinations(range(
