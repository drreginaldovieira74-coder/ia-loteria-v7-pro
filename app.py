import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

# ─── TENTA IMPORTAR XGBOOST, SE NÃO TIVER USA RANDOMFOREST ───
try:
    import xgboost as xgb
    HAS_XGB = True
except ModuleNotFoundError:
    HAS_XGB = False
    st.warning("⚠️ XGBoost não encontrado — usando RandomForest como backup")

# ─── CONFIG V89 ───
USAR_FILTRO_POOL = False  # <<<< DEIXE FALSE HOJE, amanhã muda para True
PESO_PERSONAL = 0.15

st.set_page_config(page_title="LOTOELITE V89", layout="wide", page_icon="🎯")
# ... (cole todo o resto do código que te mandei, só troque a parte do train_xgboost por esta)

@st.cache_resource
def train_model(features_tuple, labels_tuple):
    features = np.array(features_tuple)
    labels = np.array(labels_tuple)
    if len(features) == 0:
        return None
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    
    if HAS_XGB:
        model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', n_estimators=100, verbosity=0)
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    model.fit(X_train, y_train)
    return model

# ─── Configurações das Loterias ───────────────────────────────────────────────
configs = {
    "Lotofácil": {"max": 25, "qtd": 15},
    "Mega-Sena": {"max": 60, "qtd": 6},
    "Quina": {"max": 80, "qtd": 5},
    "Dupla Sena": {"max": 50, "qtd": 6},
    "Timemania": {"max": 80, "qtd": 10},
    "Lotomania": {"max": 100, "qtd": 50},
    "Dia de Sorte": {"max": 31, "qtd": 7},
    "Super Sete": {"max": 9, "qtd": 7},
    "+Milionária": {"max": 50, "qtd": 6},
}

API = {
    "Lotofácil": "lotofacil",
    "Mega-Sena": "megasena",
    "Quina": "quina",
    "Dupla Sena": "duplasena",
    "Timemania": "timemania",
    "Lotomania": "lotomania",
    "Dia de Sorte": "diadesorte",
    "Super Sete": "supersete",
    "+Milionária": "maismilionaria",
}

API_BASE = "https://loteriascaixa-api.herokuapp.com/api"

# CICLOS_INFO CORRIGIDO - V89
CICLOS_INFO = {
    "Lotofácil": {"media": 4.72, "min": 3, "max": 11, "janela": "4-6"},
    "Mega-Sena": {"media": 10.3, "min": 7, "max": 17, "janela": "7-17"},
    "Quina": {"media": 19.5, "min": 15, "max": 30, "janela": "15-30"},
    "Lotomania": {"media": 7.1, "min": 5, "max": 10, "janela": "5-10"},
    "Dupla Sena": {"media": 9.2, "min": 6, "max": 13, "janela": "6-13"},
    "Dia de Sorte": {"media": 6.0, "min": 4, "max": 9, "janela": "4-9"},
    "Timemania": {"media": 18.0, "min": 12, "max": 25, "janela": "12-25"},
    "Super Sete": {"media": 5.2, "min": 3, "max": 8, "janela": "3-8"},
    "+Milionária": {"media": 9.0, "min": 6, "max": 13, "janela": "6-13"},
}

# ─── Busca de dados da API ────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def busca(lot, n_concursos=50):
    import concurrent.futures
    slug = API[lot]
    try:
        latest_url = f"{API_BASE}/{slug}/latest"
        r = requests.get(latest_url, timeout=10).json()
        ultimo = r.get("concurso", 0)
        if not ultimo:
            return {"ok": False, "draws": []}

        def fetch_draw(i):
            try:
                d = requests.get(f"{API_BASE}/{slug}/{i}", timeout=8).json()
                dezenas = [int(x) for x in d.get("dezenas", [])]
                if dezenas:
                    return {"concurso": i, "dezenas": dezenas, "data": d.get("data", "")}
            except:
                pass
            return None

        indices = list(range(ultimo, max(ultimo - n_concursos, 0), -1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = list(executor.map(fetch_draw, indices))
        draws = [x for x in results if x is not None]
        draws.sort(key=lambda x: x["concurso"], reverse=True)

        latest_compat = {
            "numero": r.get("concurso"),
            "dataApuracao": r.get("data"),
            "listaDezenas": r.get("dezenas", []),
            "acumulado": r.get("acumulado", False),
            "valorEstimadoProximoConcurso": r.get("valorEstimadoProximoConcurso", 0),
        }
        return {"ok": True, "latest": latest_compat, "draws": draws}
    except Exception as e:
        return {"ok": False, "draws": [], "erro": str(e)}

# ─── Feature Engineering COM CICLO - V89 ──────────────────────────────────────
PRIMOS = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97}

def create_features_xgboost(draws, maxn, analise_atual=None, lot="Lotofácil"):
    features, labels = [], []
    draws_sorted = sorted(draws, key=lambda x: x["concurso"])

    fase_num = 1
    ciclo_norm = 0.5
    if analise_atual:
        fase_map = {"Início": 0, "Meio": 1, "Fim": 2}
        fase_num = fase_map.get(analise_atual["fase"], 1)
        max_ciclo = CICLOS_INFO.get(lot, {}).get("max", 11)
        ciclo_norm = analise_atual["ciclo"] / max_ciclo if max_ciclo > 0 else 0.5

    for i in range(5, len(draws_sorted)):
        current_draw = draws_sorted[i]
        past_draws = draws_sorted[max(0, i - 5):i]
        freq = {n: 0 for n in range(1, maxn + 1)}
        atraso = {n: 999 for n in range(1, maxn + 1)}
        last_seen = {n: -1 for n in range(1, maxn + 1)}
        for idx_hist, d_hist in enumerate(past_draws):
            for n_hist in d_hist["dezenas"]:
                freq[n_hist] += 1
                if atraso[n_hist] == 999:
                    atraso[n_hist] = len(past_draws) - 1 - idx_hist
                last_seen[n_hist] = len(past_draws) - 1 - idx_hist
        for num in range(1, maxn + 1):
            f = [
                freq[num],
                atraso[num],
                last_seen[num],
                num % 2,
                1 if num in PRIMOS else 0,
                fase_num,
                ciclo_norm,
                freq[num] * (1 + fase_num * 0.2)
            ]
            features.append(f)
            labels.append(1 if num in current_draw["dezenas"] else 0)
    return np.array(features), np.array(labels)

# ─── Treinamento de Modelos ───────────────────────────────────────────────────
@st.cache_resource
def train_xgboost_model(features_tuple, labels_tuple):
    features = np.array(features_tuple)
    labels = np.array(labels_tuple)
    if len(features) == 0 or len(labels) == 0:
        return None
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        n_estimators=100,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    return model

# ─── Análise de Ciclo ─────────────────────────────────────────────────────────
def analisar_ciclo(draws, maxn):
    freq = {i: 0 for i in range(1, maxn + 1)}
    atraso = {i: 99 for i in range(1, maxn + 1)}
    for idx, d in enumerate(draws[:30]):
        for n in d["dezenas"]:
            freq[n] += 1
            if atraso[n] == 99:
                atraso[n] = idx
    quentes = sorted(freq, key=freq.get, reverse=True)[:max(5, int(maxn * 0.35))]
    frios = sorted(freq, key=freq.get)[:max(5, int(maxn * 0.30))]
    neutros = [n for n in range(1, maxn + 1) if n not in quentes and n not in frios]
    seen = set()
    ciclo = 0
    for d in draws:
        seen.update(d["dezenas"])
        ciclo += 1
        if len(seen) >= maxn:
            break
    fase = "Início" if ciclo <= 4 else "Meio" if ciclo <= 8 else "Fim"
    return {
        "quentes": quentes,
        "frios": frios,
        "neutros": neutros,
        "atraso": atraso,
        "fase": fase,
        "ciclo": ciclo,
        "freq": freq,
    }

# ─── Validação de Jogos ───────────────────────────────────────────────────────
def valida_jogo(jogo, lot):
    jogo = sorted(jogo)
    if lot == "Mega-Sena":
        baixo = len([n for n in jogo if n <= 20])
        meio = len([n for n in jogo if 21 <= n <= 40])
        alto = len([n for n in jogo if n > 40])
        return baixo >= 1 and meio >= 1 and alto >= 1
    if lot == "Quina":
        baixo = len([n for n in jogo if n <= 26])
        alto = len([n for n in jogo if n > 53])
        return baixo >= 1 and alto >= 1
    if lot == "Lotofácil":
        pares = len([n for n in jogo if n % 2 == 0])
        return 6 <= pares <= 9
    if lot == "Dupla Sena":
        return len([n for n in jogo if n <= 25]) >= 2
    return True

# ─── FILTRO POOL DUPLO V89 ────────────────────────────────────────────────────
def aplicar_pool_duplo(analise, maxn):
    quentes = analise["quentes"][:10]
    frios = analise["frios"][:6]
    neutros = analise["neutros"][:4]

    if analise["fase"] == "Início":
        nucleo = frios[:5] + neutros[:5]
        zebras = quentes[:6]
    elif analise["fase"]
