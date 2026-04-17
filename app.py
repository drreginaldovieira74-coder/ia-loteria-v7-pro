import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests

st.set_page_config(page_title="LOTOELITE v86", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:3.5rem; font-weight:900; text-align:center; margin:10px 0 20px 0;}
.status-online {background:#e8f5e9; padding:5px; border-radius:5px; border-left:4px solid #2e7d32; font-size:0.8em;}
.status-offline {background:#ffebee; padding:5px; border-radius:5px; border-left:4px solid #d32f2f; font-size:0.8em;}
.acumulada {background:#ffebee; padding:10px; border-radius:8px; border-left:5px solid #d32f2f; margin:5px 0;}
</style>
""", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
if 'qtd_fechamento' not in st.session_state: st.session_state.qtd_fechamento = 21

configs = {"Lotofácil":{"max":25,"qtd":15},"Mega-Sena":{"max":60,"qtd":6},"Quina":{"max":80,"qtd":5},"Dupla Sena":{"max":50,"qtd":6},"Timemania":{"max":80,"qtd":10},"Lotomania":{"max":100,"qtd":50},"Dia de Sorte":{"max":31,"qtd":7},"Super Sete":{"max":9,"qtd":7},"+Milionária":{"max":50,"qtd":6}}
DNAS = {"Lotofácil":[4,6,10,14,17,19,20,24,25],"Mega-Sena":[14,32,37,39,42],"Quina":[4,10,14,19,20,25,32,37]}

def buscar_ciclo_real(loteria):
    try:
        api = {"Lotofácil":"lotofacil","Mega-Sena":"megasena","Quina":"quina","Dupla Sena":"duplasena","Timemania":"timemania","Lotomania":"lotomania","Dia de Sorte":"diadesorte","Super Sete":"supersete","+Milionária":"maismilionaria"}[loteria]
        max_n = configs[loteria]["max"]
        base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}"
        latest = requests.get(base, timeout=8).json()
        num = latest.get("numero",0)
        freq = {i:0 for i in range(1,max_n+1)}
        draws=[]; buscados=0
        for i in range(num, max(num-60,0), -1):
            try:
                r = requests.get(f"{base}/{i}", timeout=4)
                if r.status_code!=200: continue
                d=r.json(); dezenas = d.get("listaDezenas") or []
                nums=[int(x) for x in dezenas if str(x).isdigit()]
                for n in nums:
                    if 1<=n<=max_n: freq[n]+=1
                if nums: draws.append(nums)
                buscados+=1
            except: pass
        seen=set(); ciclo=0
        for dr in draws:
            seen.update(dr); ciclo+=1
            if len(seen)>=max_n: break
        ordenados = sorted(freq.items(), key=lambda x:x[1], reverse=True)
        quentes = sorted([n for n,_ in ordenados[:int(max_n*0.35)]])
        frios = sorted([n for n,_ in ordenados[-int(max_n*0.3):]])
        neutros = sorted([n for n in range(1,max_n+1) if n not in quentes and n not in frios])
        return {"q":quentes,"f":frios,"n":neutros,"fase":"REAL","ciclo_atual":ciclo,"status":"online"}
    except:
        max_n=configs[loteria]["max"]
        quentes=sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
        resto=[x for x in range(1,max_n+1) if x not in quentes]
        frios=sorted(random.sample(resto, int(max_n*0.3)))
        neutros=sorted([x for x in resto if x not in frios])
        return {"q":quentes,"f":frios,"n":neutros,"fase":"OFFLINE","ciclo_atual":random.randint(3,6),"status":"offline"}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v86")
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, 40, 5)
    ciclo = buscar_ciclo_real(lot)
    if ciclo["status"]=="online":
        st.markdown('<div class="status-online">🟢 ONLINE - Dados reais Caixa</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-offline">🔴 OFFLINE - Simulado</div>', unsafe_allow_html=True)

cfg = configs[lot]

def gerar():
    qtd=cfg["qtd"]; jogo=[]; dna=DNAS.get(lot,[])
    for d in dna[:int(qtd*focus/100)]:
        if d<=cfg["max"]: jogo.append(d)
    pool = list(range(1,cfg["max"]+1)); random.shuffle(pool)
    for n in pool:
        if len(jogo)>=qtd: break
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

st.markdown('<h1 class="main-title">🎯 LOTOELITE</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🎲 GERADOR","🔄 CICLO","💰 PREÇOS","🔴 AO VIVO","🔢 FECHAMENTO"])

with tabs[0]:
    if st.button("🎲 GERAR 3 JOGOS", type="primary"):
        for i in range(3):
            jogo=gerar(); st.success(f"JOGO {i+1}: {' - '.join(f'{n:02d}' for n in jogo)}")

with tabs[1]:
    st.subheader("Análise de Ciclo")
    st.write(f"**FASE: {ciclo['fase']}** | Ciclo atual: {ciclo['ciclo_atual']} concursos")
    c1,c2,c3 = st.columns(3)
    with c1: st.write("**QUENTES**"); st.write(", ".join(f"{n:02d}" for n in ciclo["q"][:12]))
    with c2: st.write("**FRIOS**"); st.write(", ".join(f"{n:02d}" for n in ciclo["f"][:12]))
    with c3: st.write("**NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in ciclo["n"][:12]))

with tabs[2]:
    st.subheader("💰 PREÇOS OFICIAIS")
    df = pd.DataFrame([
        {"Loteria":"Lotofácil","Preço":"R$ 3,50"},{"Loteria":"Mega-Sena","Preço":"R$ 6,00"},
        {"Loteria":"Quina","Preço":"R$ 3,00"},{"Loteria":"Dupla Sena","Preço":"R$ 3,00"},
        {"Loteria":"Timemania","Preço":"R$ 3,50"},{"Loteria":"+Milionária","Preço":"R$ 6,00"},
    ])
    st.dataframe(df, hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("🔴 AO VIVO - Edite os valores")
    st.info("Os valores abaixo são editáveis. Atualize conforme o site da Caixa.")
    
    if 'aovivo_df' not in st.session_state:
        st.session_state.aovivo_df = pd.DataFrame([
            {"Loteria":"Mega-Sena","Concurso":2996,"Acumulou":"SIM","Prêmio":"R$ 52.000.000,00","Próximo":"19/04/2026"},
            {"Loteria":"Quina","Concurso":7003,"Acumulou":"SIM","Prêmio":"R$ 17.000.000,00","Próximo":"17/04/2026"},
            {"Loteria":"Lotofácil","Concurso":3368,"Acumulou":"NÃO","Prêmio":"R$ 1.700.000,00","Próximo":"18/04/2026"},
            {"Loteria":"+Milionária","Concurso":187,"Acumulou":"SIM","Prêmio":"R$ 120.000.000,00","Próximo":"19/04/2026"},
        ])
    
    edited = st.data_editor(st.session_state.aovivo_df, use_container_width=True, num_rows="dynamic")
    st.session_state.aovivo_df = edited
    
    acumuladas = edited[edited["Acumulou"]=="SIM"]
    st.markdown("### 🔥 ACUMULADAS")
    for _,row in acumuladas.iterrows():
        st.markdown(f'<div class="acumulada"><b>{row["Loteria"]}</b> - {row["Prêmio"]} | Concurso {row["Concurso"]}</div>', unsafe_allow_html=True)

with tabs[4]:
    st.subheader("FECHAMENTO")
    if st.button("➕"): st.session_state.qtd_fechamento+=1
    if st.button("➖"): st.session_state.qtd_fechamento=max(1, st.session_state.qtd_fechamento-1)
    st.write(f"{st.session_state.qtd_fechamento} jogos")
    if st.button("GERAR"):
        for i in range(st.session_state.qtd_fechamento):
            st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in gerar())}")
