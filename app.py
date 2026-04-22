import streamlit as st
import pandas as pd
import numpy as np
import random
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt

# IA PESADA
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except:
    XGB_AVAILABLE = False

st.set_page_config(page_title="LOTOELITE V91 TURBO ETAPA2", layout="wide", page_icon="🧠")
st.markdown('<h1 style="text-align:center;color:#7b1fa2">🧠 LOTOELITE V91 TURBO - IA PESADA</h1>', unsafe_allow_html=True)

LOTERIAS = {
    "Lotofácil":{"max":25,"qtd":15,"preco":3.0,"api":"lotofacil"},
    "Mega-Sena":{"max":60,"qtd":6,"preco":5.0,"api":"megasena"},
    "Quina":{"max":80,"qtd":5,"preco":2.5,"api":"quina"},
}
lot = st.sidebar.selectbox("Loteria", list(LOTERIAS.keys()))
cfg = LOTERIAS[lot]

@st.cache_data(ttl=3600, show_spinner="Carregando 50 concursos...")
def carrega_50(api):
    try:
        latest = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api}/latest", timeout=10).json()
        ultimo = int(latest.get("concurso", 100))
        concursos = list(range(max(1, ultimo-49), ultimo+1))
        def fetch(c):
            try:
                r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api}/{c}", timeout=5).json()
                return {"concurso":c,"dezenas":[int(d) for d in r.get("dezenas",[])]}
            except: return None
        resultados=[]
        with ThreadPoolExecutor(max_workers=10) as ex:
            for f in as_completed([ex.submit(fetch,c) for c in concursos]):
                if f.result(): resultados.append(f.result())
        return sorted(resultados, key=lambda x: x["concurso"], reverse=True)
    except: return []

dados = carrega_50(cfg["api"])
st.sidebar.success(f"✅ {len(dados)} concursos | XGB: {'OK' if XGB_AVAILABLE else 'Instalando...'}")

# PREPARA DADOS IA
todos = list(range(1, cfg["max"]+1))
freq = {n: sum(n in d["dezenas"] for d in dados) for n in todos}

# TREINA XGBOOST
@st.cache_resource
def treina_xgb(_dados, max_num):
    if not XGB_AVAILABLE or len(_dados)<20: return None, {}
    X, y = [], []
    for i in range(len(_dados)-5):
        historico = _dados[i+1:i+6]
        proximo = set(_dados[i]["dezenas"])
        for n in range(1, max_num+1):
            atraso = next((j for j,h in enumerate(historico) if n in h["dezenas"]), 5)
            freq5 = sum(n in h["dezenas"] for h in historico)
            X.append([atraso, freq5, n/max_num, freq.get(n,0)/50])
            y.append(1 if n in proximo else 0)
    model = XGBClassifier(n_estimators=100, max_depth=4, verbosity=0)
    model.fit(np.array(X), np.array(y))
    # prediz próximo
    probs = {}
    for n in range(1, max_num+1):
        atraso = next((j for j,h in enumerate(_dados[:5]) if n in h["dezenas"]), 5)
        freq5 = sum(n in h["dezenas"] for h in _dados[:5])
        prob = model.predict_proba([[atraso, freq5, n/max_num, freq.get(n,0)/50]])[0][1]
        probs[n] = prob
    return model, probs

model, probs = treina_xgb(dados, cfg["max"])

# ALGORITMO GENÉTICO
def genetico(probs, qtd, geracoes=50):
    def fitness(jogo): return sum(probs.get(n,0) for n in jogo)
    populacao = [random.sample(todos, qtd) for _ in range(100)]
    for _ in range(geracoes):
        populacao = sorted(populacao, key=fitness, reverse=True)[:50]
        nova = []
        for _ in range(50):
            p1,p2 = random.sample(populacao[:20],2)
            filho = list(set(p1[:qtd//2] + p2[qtd//2:]))
            while len(filho)<qtd: filho.append(random.choice(todos))
            if random.random()<0.1: filho[random.randint(0,qtd-1)]=random.choice(todos)
            nova.append(filho[:qtd])
        populacao += nova
    return sorted(populacao, key=fitness, reverse=True)[0]

def render_color(nums, probs_dict):
    html=""
    for n in sorted(nums):
        p = probs_dict.get(n,0)
        cor = "#4caf50" if p>0.6 else "#2196f3" if p<0.4 else "#ff9800"
        html+=f'<span style="background:{cor};color:white;padding:6px 10px;border-radius:50%;margin:2px;display:inline-block;min-width:36px;text-align:center" title="Prob:{p:.2f}">{n:02d}</span>'
    return html

tabs = st.tabs(["🎲 GERADOR","🧠 IA XGBOOST","🧬 GENÉTICO","📈 ESTATÍSTICAS","🔬 BACKTEST","🎯 DNA","📊 RESULTADOS"])

with tabs[0]:
    st.subheader("Gerador Clássico")
    if st.button("Gerar 3"):
        for t in ["Conservador","Equilibrado","Agressivo"]:
            jogo = sorted(random.sample(todos, cfg["qtd"]))
            st.markdown(f"**{t}:** {render_color(jogo, probs)}", unsafe_allow_html=True)

with tabs[1]:
    st.subheader("🧠 XGBoost - Probabilidades IA")
    if model:
        df_prob = pd.DataFrame([{"Dezena":n,"Probabilidade":probs[n]} for n in todos]).sort_values("Probabilidade",ascending=False)
        st.dataframe(df_prob.head(15), hide_index=True)
        top_jogo = sorted(df_prob.head(cfg["qtd"])["Dezena"].tolist())
        st.success("Jogo XGBoost (top probabilidades):")
        st.markdown(render_color(top_jogo, probs), unsafe_allow_html=True)
        st.bar_chart(df_prob.set_index("Dezena")["Probabilidade"])
    else:
        st.warning("Treinando modelo...")

with tabs[2]:
    st.subheader("🧬 Algoritmo Genético")
    if st.button("Evoluir 50 gerações"):
        if probs:
            melhor = genetico(probs, cfg["qtd"])
            st.success("Melhor indivíduo após evolução:")
            st.markdown(render_color(sorted(melhor), probs), unsafe_allow_html=True)
            st.metric("Fitness", f"{sum(probs.get(n,0) for n in melhor):.3f}")
        else:
            st.error("Aguarde XGBoost")

with tabs[3]:
    st.subheader("Estatísticas 50 concursos")
    df = pd.DataFrame([{"Dezena":n,"Freq":freq[n]} for n in todos])
    st.bar_chart(df.set_index("Dezena"))

with tabs[4]:
    st.subheader("🔬 Backtest XGBoost")
    if model and len(dados)>10:
        acertos=[]
        for i in range(10):
            teste = dados[i+1:i+6]
            real = set(dados[i]["dezenas"])
            # prediz
            probs_teste = {}
            for n in todos:
                atraso = next((j for j,h in enumerate(teste) if n in h["dezenas"]),5)
                freq5 = sum(n in h["dezenas"] for h in teste)
                p = model.predict_proba([[atraso,freq5,n/cfg["max"],freq.get(n,0)/50]])[0][1]
                probs_teste[n]=p
            pred = set(sorted(probs_teste, key=probs_teste.get, reverse=True)[:cfg["qtd"]])
            acertos.append(len(pred & real))
        st.metric("Média acertos (últimos 10)", f"{np.mean(acertos):.2f}")
        st.line_chart(acertos)
    else:
        st.info("Coletando dados...")

with tabs[5]:
    st.subheader("DNA + Probabilidades")
    dna_df = pd.DataFrame([{"Dezena":n,"Prob_XGB":f"{probs.get(n,0):.3f}","Freq_50":freq[n]} for n in todos])
    st.dataframe(dna_df, hide_index=True, height=400)

with tabs[6]:
    st.subheader("Últimos resultados")
    for d in dados[:10]:
        st.markdown(f"**{d['concurso']}**: {render_color(d['dezenas'], probs)}", unsafe_allow_html=True)
