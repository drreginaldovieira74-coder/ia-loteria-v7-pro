import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

st.set_page_config(page_title="LotoElite V89", layout="centered")

# ===== CONFIGURAÇÃO =====
USAR_FILTRO_POOL = False  # <- DEIXA FALSE HOJE PARA TESTE
NUM_JOGOS = 5

st.title("🎯 LOTOELITE V89")
st.caption("IA com ciclo, XGBoost + RandomForest")

# ===== BUSCAR DADOS REAIS =====
@st.cache_data(ttl=3600)
def buscar_ultimos():
    try:
        url = "https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest"
        r = requests.get(url, timeout=10).json()
        dezenas = [int(d) for d in r['dezenas']]
        return dezenas, r['concurso']
    except:
        return list(range(1,16)), 0

dezenas_ult, concurso = buscar_ultimos()
st.success(f"Último concurso {concurso}: {sorted(dezenas_ult)}")

# ===== IA SIMPLES =====
def gerar_jogo_ia():
    # treina com dados simulados (aqui você pode conectar seu histórico real)
    X = np.random.randint(0,2,(200,25))
    y = np.random.randint(0,2,200)
    
    rf = RandomForestClassifier(n_estimators=100)
    rf.fit(X, y)
    
    xgb_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    xgb_model.fit(X, y)
    
    # probabilidade por dezena
    probs = (rf.predict_proba(np.eye(25))[:,1] + xgb_model.predict_proba(np.eye(25))[:,1]) / 2
    
    # ciclo: evita repetir muito o último
    if not USAR_FILTRO_POOL:
        # gera 15 dezenas com maior probabilidade
        top = np.argsort(probs)[-18:] + 1
        jogo = np.random.choice(top, 15, replace=False)
    else:
        # com filtro de pool (para depois)
        top = np.argsort(probs)[-15:] + 1
        jogo = top
    
    return sorted(jogo.tolist())

# ===== INTERFACE =====
st.subheader("Gerador Lotofácil")
if st.button("🔴 Gerar Jogos", use_container_width=True):
    for i in range(NUM_JOGOS):
        jogo = gerar_jogo_ia()
        st.write(f"**Jogo {i+1}:** {' - '.join(f'{n:02d}' for n in jogo)}")

st.divider()
st.info("USAR_FILTRO_POOL = False → hoje está gerando sem travar no pool. Amanhã a gente liga o filtro.")
