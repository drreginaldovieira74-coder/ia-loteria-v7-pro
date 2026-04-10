import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO v49.8")
st.markdown("**Versao minima - testando ULTRA_FOCUS**")

loteria_options = {
    "Lotofacil": {"nome": "Lotofacil", "total": 25, "sorteadas": 15, "mantidas": [9, 11]}
}

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]
st.success("**{}** — Ciclo fecha em 4-6 sorteios".format(config['nome']))

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
        fase = "ZERADO"
    elif sorteios_ciclo <= 3: 
        fase = "INICIO"
    elif sorteios_ciclo <= 5: 
        fase = "MEIO"
    else: 
        fase = "FIM"

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    quentes = [int(x) for x in np.argsort(np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:])[-15:][::-1] + 1]

    return {
        "fase": fase, "faltantes": [int(x) for x in faltantes], "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "memoria": [int(x) for x in memoria],
        "ciclos_hist": ciclos, "previsao_fecha": max(0, 6 - sorteios_ciclo),
        "quentes": quentes
    }

def gerar_jogo_ciclo(config, analise, modo="AVANCADO"):
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    jogo = []

    if modo == "ULTRA_FOCUS":
        if len(faltantes) >= total_jogo:
            jogo = random.sample(faltantes, total_jogo)
        else:
            jogo = random.sample(faltantes, len(faltantes))
            mem_shuffled = random.sample(memoria, len(memoria))
            jogo.extend([m for m in mem_shuffled if m not in jogo][:total_jogo - len(jogo)])
    else:
        qtd_f = min(int(total_jogo * 0.4), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(9, len(mem_disp), total_jogo - len(jogo))))

    quentes_disp = [q for q in analise["quentes"] if q not in jogo]
    while len(jogo) < total_jogo and len(quentes_disp) > 0:
        jogo.append(quentes_disp.pop(0))

    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo: 
            jogo.append(candidato)

    return [int(x) for x in jogo[:total_jogo]]

try:
    analise = analisar_ciclo_completo(df, config)
except Exception as e:
    st.error("Erro ao analisar ciclo: {}".format(e))
    st.stop()

tab1, tab2 = st.tabs(["Gerador de Jogos", "Estatisticas"])

with tab1:
    st.subheader("Gerador de Jogos – Ciclo 4-6 como Motor")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase do Ciclo", analise["fase"], "{}º sorteio".format(analise['sorteios_ciclo']))
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memoria", len(analise["memoria"]))
    c4.metric("Fecha em", "{} concursos".format(analise['previsao_fecha']))

    if analise["fase"] == "FIM":
        st.error("FIM DE CICLO! {} faltantes. Hora de atacar!".format(len(analise['faltantes'])))
    elif analise["fase"] == "MEIO":
        st.warning("MEIO DO CICLO. {} sorteios pro fim".format(6-analise['sorteios_ciclo']))
    else:
        st.info("INICIO. Ciclo formando, {}º sorteio".format(analise['sorteios_ciclo']))

    modo_focus = st.select_slider("Modo Ultra Focus", ["AVANCADO", "ULTRA_FOCUS"], value="AVANCADO")
    qtd = st.slider("Quantos jogos?", 5, 50, 15)

    if st.button("GERAR JOGOS COM CICLO FORTE", type="primary"):
        st.write("**Modo: {} | Fase: {}**".format(modo_focus, analise['fase']))
        for i in range(qtd):
            jogo = gerar_jogo_ciclo(config, analise, modo_focus)
            st.code("Jogo {:02d}: {}".format(i+1, jogo))

with tab2:
    st.subheader("Estatisticas do Ciclo")
    st.metric("Fase Atual", analise["fase"])
    st.metric("Progresso do Ciclo", "{:.0%}".format(analise['progresso']))
    st.progress(float(analise["progresso"]))
    st.write("**Faltantes:**")
    st.code(", ".join(map(str, analise["faltantes"])) if analise["faltantes"] else "Ciclo completo")
    st.write("**Memoria:**")
    st.code(", ".join(map(str, analise["memoria"])) if analise["memoria"] else "Sem memoria")
