import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# --- CONFIGURAÇÕES (mantenha suas configs originais) ---
configs = {
    "Lotofácil": {"qtd":15,"max":25,"preco":3.5,"api":"lotofacil"},
    "Mega-Sena": {"qtd":6,"max":60,"preco":6,"api":"megasena"},
    "Quina": {"qtd":5,"max":80,"preco":2.5,"api":"quina"},
    "São João": {"qtd":5,"max":80,"preco":2.5,"api":"quina"},
    "Mega Virada": {"qtd":6,"max":60,"preco":6,"api":"megasena"},
}

if "ciclos" not in st.session_state: st.session_state.ciclos = {}
if "historico" not in st.session_state: st.session_state.historico = []
if "dados_caixa" not in st.session_state: st.session_state.dados_caixa = {}
if "ao_vivo" not in st.session_state: st.session_state.ao_vivo = []

def gerar(focus, ciclo):
    # sua função original aqui
    return sorted(random.sample(range(1, configs[lot]["max"]+1), configs[lot]["qtd"]))

def buscar_ao_vivo():
    # sua função original aqui
    return []

st.set_page_config(page_title="LOTOELITE v84", layout="wide")
lot = st.sidebar.selectbox("Loteria", list(configs.keys()))
cfg = configs[lot]
focus = st.sidebar.slider("Focus %", 0, 100, 70)

tabs = st.tabs(["Dashboard","Ciclo","Fechamento","Fechamento 21","Análise","Gráfico","Bolões","Últimos","Meus Jogos","Conferidor","Perfil","Preços","Exportar","AO VIVO","Hub Especiais"])

# --- SUAS ABAS 0-1 (mantenha seu código original aqui) ---
with tabs[0]:
    st.subheader("IA 3 Jogos")
    # seu código da IA aqui

with tabs[1]:
    st.subheader("Ciclo")
    # seu código do ciclo aqui

# --- SUAS ABAS 2-13 (código que você me enviou) ---
with tabs[2]:
    st.subheader("Fechamento")
    if lot not in st.session_state.ciclos: st.error("Atualize ciclo"); st.stop()
    qtd=st.number_input("Quantos jogos?",1,500,20); st.info(f"R$ {qtd*cfg['preco']:.2f}")
    if st.button(f"Gerar {qtd}"):
        ciclo=st.session_state.ciclos[lot]; jogos=[gerar(focus,ciclo) for _ in range(qtd)]
        cols=st.columns(4)
        for i,j in enumerate(jogos[:40]):
            with cols[i%4]: st.text(f"{i+1:03d}: {'-'.join(f'{n:02d}' for n in j)}")

#... (cole aqui tabs[3] até tabs[13] exatamente como você enviou)...

# --- NOVA ABA 14 HUB ESPECIAIS ---
with tabs[14]:
    st.header("🎯 Hub Especiais")
    st.subheader("São João - 15 edições (2011-2025)")
    st.code("2025: 12-19-20-34-35\n2024: 21-38-60-64-70\n2023: 12-13-45-47-70")
    st.info("33 números nunca saíram - use ciclo 3 anos")

    st.subheader("Mega Virada - 17 edições")
    st.code("2025: 09-13-21-32-33-59\n2024: 01-17-19-29-50-57")

    if st.button("Gerar 3 jogos São João"):
        for i in range(3):
            st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in sorted(random.sample(range(1,81),5)))}")
