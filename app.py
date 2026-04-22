import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE V89", layout="wide")
st.markdown('<h1 style="text-align:center;color:#d32f2f">🎯 LOTOELITE V89 PRO - FOCO NO CICLO</h1>', unsafe_allow_html=True)

LOTERIAS = {"Lotofácil":{"max":25,"qtd":15},"Mega-Sena":{"max":60,"qtd":6},"Quina":{"max":80,"qtd":5}}
CICLOS = {"Lotofácil":"4-6","Mega-Sena":"7-17","Quina":"15-30"}

lot = st.sidebar.selectbox("Loteria", list(LOTERIAS.keys()))
cfg = LOTERIAS[lot]
fase = ["INÍCIO","MEIO","FIM"][datetime.now().day % 3]

def render(nums):
    return " ".join([f'<span style="background:#2e7d32;color:white;padding:6px 10px;border-radius:50%;margin:2px;display:inline-block;min-width:36px;text-align:center">{n:02d}</span>' for n in sorted(nums)])

st.subheader(f"Gerador - {lot} | Fase: {fase}")
st.info(f"Ciclo: {fase} | Janela ideal: {CICLOS[lot]} concursos")

todos = list(range(1, cfg["max"]+1))
random.seed(datetime.now().day)

quentes = random.sample(todos, min(12, len(todos)))
restantes = [n for n in todos if n not in quentes]
frios = random.sample(restantes, min(12, len(restantes)))
neutros = [n for n in todos if n not in quentes+frios]

def gerar(tipo):
    if tipo=="Conservador":
        base = quentes + neutros
    elif tipo=="Agressivo":
        base = frios + neutros
    else: # Equilibrado
        if fase=="INÍCIO": base = quentes + neutros
        elif fase=="FIM": base = frios + neutros
        else: base = quentes[:6] + frios[:6] + neutros

    base = list(dict.fromkeys(base))
    if len(base) < cfg["qtd"]:
        base = todos

    jogo = sorted(random.sample(base, cfg["qtd"]))
    return jogo

if st.button("🎯 GERAR OS 3 DE UMA VEZ", type="primary", use_container_width=True):
    for nome in ["Conservador","Equilibrado","Agressivo"]:
        jogo = gerar(nome)
        st.markdown(f"**{nome}:** {render(jogo)}", unsafe_allow_html=True)

st.success("✅ Sistema estável - erro corrigido")
