import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests

st.set_page_config(page_title="LOTOELITE v85.5", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:3.5rem; font-weight:900; text-align:center; margin:10px 0 20px 0; letter-spacing:2px;}
.focus-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #2e7d32;}
.ia-box {background:#e3f2fd; padding:5px; border-radius:5px; font-size:0.75em;}
.real-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #388e3c;}
.acumulada {background:#ffebee; padding:10px; border-radius:8px; border-left:5px solid #d32f2f; margin:5px 0;}
</style>
""", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
if 'perfil' not in st.session_state: st.session_state.perfil = {"focus":40}
if 'ciclos' not in st.session_state: st.session_state.ciclos = {}
if 'sugestoes_por_loteria' not in st.session_state: st.session_state.sugestoes_por_loteria = {}
if 'dados_caixa' not in st.session_state: st.session_state.dados_caixa = {}
if 'ao_vivo' not in st.session_state: st.session_state.ao_vivo = []
if 'historico_ciclos' not in st.session_state: st.session_state.historico_ciclos = {}

ciclos_ideais = {
    "Lotofácil": (4,6),
    "Mega-Sena": (9,11),
    "Quina": (14,18),
    "Dupla Sena": (8,10),
    "Timemania": (12,15),
    "Lotomania": (8,12),
    "Dia de Sorte": (4,5),
    "Super Sete": (3,4),
    "+Milionária": (9,12),
}

configs = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50, "api":"lotofacil"},
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00, "api":"megasena"},
    "Quina": {"max":80,"qtd":5,"preco":3.00, "api":"quina"},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00, "api":"duplasena"},
    "Timemania": {"max":80,"qtd":10,"preco":3.50, "api":"timemania"},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00, "api":"lotomania"},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50, "api":"diadesorte"},
    "Super Sete": {"max":9,"qtd":7,"preco":3.00, "api":"supersete"},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00, "api":"maismilionaria"},
}

DNAS = {
    "Lotofácil": [4,6,10,14,17,19,20,24,25],
    "Mega-Sena": [14,32,37,39,42],
    "Quina": [4,10,14,19,20,25,32,37],
    "Dupla Sena": [14,19,25,32,37,42],
    "Timemania": [4,10,14,20,25,32,44],
    "Lotomania": [4,6,10,14,17,19,20,24,25,32,37,39],
    "Dia de Sorte": [4,6,10,14,17,19,20],
    "Super Sete": [4,6,10,14,17,19,20],
    "+Milionária": [14,19,25,32,37,42],
}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v85.5")
    st.markdown('<div class="ia-box">🧠 v85.5 RADAR FIX</div>', unsafe_allow_html=True)
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, st.session_state.perfil["focus"], 5)
    st.session_state.perfil["focus"] = focus
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel}</b> {focus}%</div>', unsafe_allow_html=True)

cfg = configs[lot]

def buscar_ciclo_real(loteria):
    try:
        api_nome = configs[loteria]["api"]; max_n = configs[loteria]["max"]
        base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api_nome}"
        latest = requests.get(base, timeout=10).json()
        num_atual = latest.get("numero", 0) or latest.get("numeroDoConcurso",0)
        freq = {i:0 for i in range(1, max_n+1)}; buscados = 0; draws=[]
        for i in range(num_atual, max(num_atual-80, 0), -1):
            try:
                r = requests.get(f"{base}/{i}", timeout=3)
                if r.status_code!= 200: continue
                d = r.json(); dezenas = d.get("listaDezenas") or d.get("dezenas") or []
                nums=[]
                for dz in dezenas:
                    try:
                        n=int(dz)
                        if 1 <= n <= max_n:
                            freq[n]+=1; nums.append(n)
                    except: pass
                if nums: draws.append(nums)
                buscados+=1
                if buscados>=80: break
            except: continue
        seen=set(); ciclo_atual=0
        for dr in draws:
            seen.update(dr); ciclo_atual+=1
            if len(seen)>=max_n: break
        ordenados = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        q_q=int(max_n*0.35); q_f=int(max_n*0.3)
        quentes=sorted([n for n,_ in ordenados[:q_q]]); frios=sorted([n for n,_ in ordenados[-q_f:]])
        neutros=sorted([n for n in range(1,max_n+1) if n not in quentes and n not in frios])
        resultado = {"q":quentes,"f":frios,"n":neutros,"fase":"REAL","h":f"{buscados} concursos","freq":freq,"atualizado":datetime.now().strftime("%H:%M"),"ciclo_atual":ciclo_atual}
        # Guarda histórico de ciclos - v84.2
        if loteria not in st.session_state.historico_ciclos:
            st.session_state.historico_ciclos[loteria] = []
        hist = st.session_state.historico_ciclos[loteria]
        # Adiciona só se mudou ou é o primeiro
        if not hist or hist[-1]["ciclo_atual"]!= ciclo_atual:
            hist.append({"data": datetime.now().strftime("%d/%m %H:%M"), "ciclo_atual": ciclo_atual, "concurso": num_atual})
            # Mantém só os últimos 20
            st.session_state.historico_ciclos[loteria] = hist[-20:]
        return resultado
    except:
        max_n=configs[loteria]["max"]; quentes=sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
        resto=[x for x in range(1,max_n+1) if x not in quentes]; frios=sorted(random.sample(resto, int(max_n*0.3)))
        neutros=sorted([x for x in resto if x not in frios]); return {"q":quentes,"f":frios,"n":neutros,"fase":"OFFLINE","h":"Random","freq":{},"ciclo_atual":0}

# [O RESTO DO SEU CÓDIGO CONTINUA IGUAL... COLE AQUI DO ARQUIVO ORIGINAL A PARTIR DA LINHA 121 ATÉ O FINAL]
# Para não ficar gigante aqui, mantenha tudo igual da sua v85.3

# === IMPORTANTE: NA ABA CICLO, SUBSTITUA O BLOCO DOS QUENTES/FRIOS POR ESTE: ===

# Dentro de "with tabs[2]:" ou onde mostra o ciclo, após mostrar quentes/frios/neutros, adicione:

# --- ITEM 7 INÍCIO ---
hist = st.session_state.historico_ciclos.get(lot, [])
valores = [h["ciclo_atual"] for h in hist]

if len(valores) >= 2:
    ult = valores[-2:]
    if ult[1] < ult[0]:
        tendencia = "🚀 ACELERANDO"
    elif ult[1] > ult[0]:
        tendencia = "🐢 DESACELERANDO"
    else:
        tendencia = "➡️ ESTÁVEL"
    st.markdown(f"**Radar Velocidade:** {tendencia} | Histórico: {len(valores)} ciclos")
else:
    st.markdown(f"**Radar Velocidade:** Coletando dados... ({len(valores)}/2)")

if hist:
    media_hist = sum(valores)/len(valores)
    ca = ciclo.get("ciclo_atual",0)
    falta = int(media_hist - ca)
    if falta > 0:
        st.info(f"🔮 Previsão: faltam ~{falta} concurso(s) para virada (média {media_hist:.1f})")
    elif falta == 0:
        st.warning("🔮 Previsão: PONTO DE VIRADA AGORA")
    else:
        st.error(f"⚠️ Ciclo estendido! Atrasado em {abs(falta)} concurso(s)")
# --- ITEM 7 FIM ---
