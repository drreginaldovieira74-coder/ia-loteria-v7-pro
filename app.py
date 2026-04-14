import streamlit as st
import pandas as pd
from collections import Counter
import random

st.set_page_config(page_title="LOTOELITE v67.4", layout="wide")

# Configuração simples
CICLOS = {
    "Lotofácil": {"t":25,"s":15,"c1":4,"c2":6,"m1":9,"m2":11},
    "Lotomania": {"t":100,"s":20,"c1":8,"c2":12,"m1":12,"m2":14},
    "Mega-Sena": {"t":60,"s":6,"c1":24,"c2":36,"m1":3,"m2":4},
    "Quina": {"t":80,"s":5,"c1":38,"c2":57,"m1":3,"m2":3},
    "Dupla Sena": {"t":50,"s":6,"c1":20,"c2":30,"m1":3,"m2":4},
    "Timemania": {"t":80,"s":7,"c1":27,"c2":41,"m1":4,"m2":5},
    "Dia de Sorte": {"t":31,"s":7,"c1":10,"c2":15,"m1":4,"m2":5},
}

# Dados mínimos para funcionar
DADOS = {
'lotofacil': [[1,2,5,6,7,8,10,11,12,14,17,18,22,23,24],[3,5,6,7,8,9,10,11,13,14,15,16,17,23,25],[2,3,4,5,9,10,11,12,13,16,18,20,22,23,24]],
'lotomania': [[6,10,12,14,15,18,21,23,31,40,45,47,55,69,70,73,77,87,91,93],[0,5,11,14,15,20,22,26,32,38,43,46,53,58,72,77,93,94,96,97]],
'megasena': [[7,15,23,34,45,56],[3,12,28,33,41,52]],
'quina': [[12,24,36,48,72],[5,17,29,41,63]],
'duplasena': [[3,14,25,36,47,50],[5,16,27,38,49,51]],
'timemania': [[4,11,18,25,32,39,46],[7,14,21,28,35,42,49]],
'diadesorte': [[2,8,14,19,23,27,31],[3,9,15,20,24,28,30]],
}

st.title("🎯 LOTOELITE v67.4")
st.caption("Sistema de Ciclos - Versão Estável")

lot = st.sidebar.selectbox("LOTERIA", list(CICLOS.keys()))
c = CICLOS[lot]

# Mapeamento seguro
mapa = {
    "Lotofácil": "lotofacil",
    "Lotomania": "lotomania", 
    "Mega-Sena": "megasena",
    "Quina": "quina",
    "Dupla Sena": "duplasena",
    "Timemania": "timemania",
    "Dia de Sorte": "diadesorte"
}
k = mapa.get(lot, "lotofacil")

st.sidebar.info(f"**{lot}**\nTotal: {c['t']}\nSorteia: {c['s']}\nCiclo: {c['c1']}-{c['c2']}")

dados = DADOS.get(k, [[1,2,3,4,5]])

# Inicializar session state
if 'analises' not in st.session_state:
    st.session_state.analises = {}

t1,t2,t3,t4 = st.tabs(["🔄 CICLO","📊 Resultados","🎯 Previsão","🤖 IA"])

with t1:
    st.header(f"Ciclo - {lot}")
    col1,col2,col3 = st.columns(3)
    
    with col1:
        ciclo = st.slider("Janela", c['c1'], c['c2'], (c['c1']+c['c2'])//2, key=f"sl_{k}")
        if st.button("ANALISAR", type="primary", key=f"btn_{k}"):
            ult = dados[-min(ciclo, len(dados)):]
            todas = []
            for jogo in ult:
                todas.extend(jogo)
            freq = Counter(todas)
            st.session_state.analises[k] = {
                'u': len(freq),
                'f': [n for n in range(1, c['t']+1) if n not in freq],
                'm': [n for n,v in freq.items() if v >= 2],
                'cob': len(freq)/c['t']*100 if c['t'] > 0 else 0
            }
            st.success("Analisado!")
    
    with col2:
        ana = st.session_state.analises.get(k, {})
        if ana:
            st.metric("Cobertura", f"{ana.get('u',0)}/{c['t']}", f"{ana.get('cob',0):.1f}%")
            st.progress(min(ana.get('cob',0)/100, 1.0))
    
    with col3:
        ana = st.session_state.analises.get(k, {})
        if ana:
            st.metric("Mantidas", len(ana.get('m',[])), f"Meta {c['m1']}-{c['m2']}")
            st.metric("Faltam", len(ana.get('f',[])))

with t2:
    st.header("Resultados")
    df = pd.DataFrame(dados[-10:][::-1])
    if not df.empty:
        df.columns = [f'D{i+1}' for i in range(len(df.columns))]
        st.dataframe(df, use_container_width=True)

with t3:
    st.header("Previsão")
    ana = st.session_state.analises.get(k, {})
    if ana and ana.get('m'):
        col1,col2 = st.columns(2)
        with col1:
            st.subheader("Fechar Ciclo")
            base = ana.get('f', [])[:5] + ana.get('m', [])[:5]
            while len(base) < c['s']:
                base.append(random.randint(1, c['t']))
            jogo = sorted(list(set(base))[:c['s']])
            st.code(" ".join(f"{n:02d}" for n in jogo))
        with col2:
            st.subheader("Manter")
            m = ana.get('m', [])[:c['m2']]
            resto = [n for n in range(1, c['t']+1) if n not in m]
            jogo2 = sorted((m + random.sample(resto, max(0, c['s']-len(m))))[:c['s']])
            st.code(" ".join(f"{n:02d}" for n in jogo2))
    else:
        st.info("Clique em ANALISAR primeiro")

with t4:
    st.header("IA")
    c1,c2,c3 = st.columns(3)
    for i, (col, nome) in enumerate(zip([c1,c2,c3], ["Fechamento","Manutenção","Virada"])):
        with col:
            if st.button(nome, key=f"ia_{k}_{i}", use_container_width=True):
                jogo = sorted(random.sample(range(1, c['t']+1), c['s']))
                st.success(" ".join(f"{n:02d}" for n in jogo))

st.sidebar.success("v67.4 - Estável")
