import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb
import matplotlib.pyplot as plt
import os

# ─── CONFIGURAÇÃO V89 ─────────────────────────────────────────────────────────
USAR_FILTRO_POOL = False # Mude para True amanhã 22/04 para ativar o teste
PESO_PERSONAL_REINFORCEMENT = 0.15

# Suprimir warnings do TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from deap import base, creator, tools, algorithms

st.set_page_config(page_title="LOTOELITE ULTIMATE AI V89", layout="wide", page_icon="🎯")

# CSS customizado
st.markdown("""
<style>
   .main-title {
        text-align: center;
        color: #d32f2f;
        font-size: 2.8rem;
        font-weight: 900;
        padding: 10px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
   .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 20px;
    }
   .numero-quente {
        background-color: #ff4444;
        color: white;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        margin: 2px;
        display: inline-block;
        min-width: 32px;
        text-align: center;
    }
   .numero-frio {
        background-color: #4488ff;
        color: white;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        margin: 2px;
        display: inline-block;
        min-width: 32px;
        text-align: center;
    }
   .numero-neutro {
        background-color: #888;
        color: white;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        margin: 2px;
        display: inline-block;
        min-width: 32px;
        text-align: center;
    }
   .numero-jogo {
        background-color: #2e7d32;
        color: white;
        padding: 6px 10px;
        border-radius: 50%;
        font-weight: bold;
        margin: 3px;
        display: inline-block;
        min-width: 36px;
        text-align: center;
        font-size: 1.1rem;
    }
   .ciclo-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎯 LOTOELITE ULTIMATE AI V89</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sistema com IA Preditiva + Ciclos + Pool Duplo</div>', unsafe_allow_html=True)

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
                fase_num, # V89: fase do ciclo
                ciclo_norm, # V89: posição normalizada no ciclo
                freq[num] * (1 + fase_num * 0.2) # V89: peso adaptativo
            ]
            features.append(f)
            labels.append(1 if num in current_draw["dezenas"] else 0)
    return np.array(features), np.array(labels)

def create_sequences_lstm(draws, maxn, sequence_length=10):
    sequences, next_numbers = [], []
    draws_sorted = sorted(draws, key=lambda x: x["concurso"])
    for i in range(len(draws_sorted) - sequence_length):
        sequence = []
        for j in range(sequence_length):
            draw_data = draws_sorted[i + j]["dezenas"]
            draw_vector = [1 if n in draw_data else 0 for n in range(1, maxn + 1)]
            sequence.append(draw_vector)
        next_draw_data = draws_sorted[i + sequence_length]["dezenas"]
        next_draw_vector = [1 if n in next_draw_data else 0 for n in range(1, maxn + 1)]
        sequences.append(sequence)
        next_numbers.append(next_draw_vector)
    return np.array(sequences), np.array(next_numbers)

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

@st.cache_resource
def train_lstm_model(sequences_tuple, next_numbers_tuple, maxn, sequence_length=10):
    sequences = np.array(sequences_tuple)
    next_numbers = np.array(next_numbers_tuple)
    if len(sequences) == 0 or len(next_numbers) == 0:
        return None
    X_train, X_test, y_train, y_test = train_test_split(sequences, next_numbers, test_size=0.2, random_state=42)
    model = Sequential([
        LSTM(50, activation='relu', input_shape=(sequence_length, maxn)),
        Dense(maxn, activation='sigmoid'),
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)
    return model

# ─── Algoritmos Genéticos ─────────────────────────────────────────────────────
if "FitnessMax" not in creator.__dict__:
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
if "Individual" not in creator.__dict__:
    creator.create("Individual", list, fitness=creator.FitnessMax)

def eval_game(individual, model_xgboost, draws, maxn, lot, analise_atual):
    if not valida_jogo(individual, lot):
        return (-1000000,)
    latest_draws = sorted(draws, key=lambda x: x["concurso"], reverse=True)[:5]
    freq = {n: 0 for n in range(1, maxn + 1)}
    atraso = {n: 999 for n in range(1, maxn + 1)}
    last_seen = {n: -1 for n in range(1, maxn + 1)}
    for idx_hist, d_hist in enumerate(latest_draws):
        for n_hist in d_hist["dezenas"]:
            freq[n_hist] += 1
            if atraso[n_hist] == 999:
                atraso[n_hist] = len(latest_draws) - 1 - idx_hist
            last_seen[n_hist] = len(latest_draws) - 1 - idx_hist

    fase_num = {"Início": 0, "Meio": 1, "Fim": 2}.get(analise_atual["fase"], 1)
    ciclo_norm = analise_atual["ciclo"] / CICLOS_INFO.get(lot, {}).get("max", 11)

    prediction_features = []
    for num in individual:
        f = [freq[num], atraso[num], last_seen[num], num % 2, 1 if num in PRIMOS else 0, fase_num, ciclo_norm, freq[num] * (1 + fase_num * 0.2)]
        prediction_features.append(f)
    if model_xgboost is None or len(prediction_features) == 0:
        return (0,)
    probabilities = model_xgboost.predict_proba(np.array(prediction_features))[:, 1]
    return (float(sum(probabilities)),)

def generate_game_genetic_algorithm(lot, model_xgboost, draws, maxn, analise_atual):
    q = configs[lot]["qtd"]
    toolbox = base.Toolbox()
    toolbox.register("attr_num", random.randint, 1, maxn)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_num, q)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", eval_game, model_xgboost=model_xgboost, draws=draws, maxn=maxn, lot=lot, analise_atual=analise_atual)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=1, up=maxn, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)
    population = toolbox.population(n=50)
    NGEN = 20
    for gen in range(NGEN):
        offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
        fits = list(map(toolbox.evaluate, offspring))
        for ind, fit in zip(offspring, fits):
            ind.fitness.values = fit
        population = toolbox.select(offspring, k=len(population))
    top_individual = tools.selBest(population, k=1)[0]
    result = sorted(list(set(top_individual)))[:q]
    while len(result) < q:
        n = random.randint(1, maxn)
        if n not in result:
            result.append(n)
    return sorted(result[:q])

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
    """Retorna núcleo 10 + zebra 6 para Lotofácil"""
    quentes = analise["quentes"][:10] # núcleo
    frios = analise["frios"][:6] # zebras
    neutros = analise["neutros"][:4]

    # mistura adaptativa por fase
    if analise["fase"] == "Início":
        nucleo = frios[:5] + neutros[:5]
        zebras = quentes[:6]
    elif analise["fase"] == "Fim":
        nucleo = quentes[:10]
        zebras = frios[:6]
    else:
        nucleo = quentes[:7] + neutros[:3]
        zebras = frios[:4] + neutros[3:5]

    return list(dict.fromkeys(nucleo))[:10], list(dict.fromkeys(zebras))[:6]

# ─── Geração por Estratégia COM POOL ADAPTATIVO V89 ───────────────────────────
def gerar_por_estrategia(lot, analise, estrategia):
    q = configs[lot]["qtd"]
    maxn = configs[lot]["max"]

    # V89: USA POOL DUPLO SE ATIVADO E LOTOFÁCIL
    if USAR_FILTRO_POOL and lot == "Lotofácil":
        nucleo, zebras = aplicar_pool_duplo(analise, maxn)
        if estrategia == "conservador":
            pool = nucleo[:8] + zebras[:2]
        elif estrategia == "equilibrado":
            pool = nucleo[:7] + zebras[:3]
        else:
            pool = zebras + nucleo[:4]
    else:
        # Lógica original adaptativa por fase
        quentes = analise["quentes"]
        frios = analise["frios"]
        neutros = analise["neutros"]

        if analise["fase"] == "Início":
            base_pool = frios[:int(len(frios)*0.6)] + neutros + quentes[:int(len(quentes)*0.3)]
        elif analise["fase"] == "Fim":
            base_pool = quentes[:int(len(quentes)*0.7)] + neutros + frios[:int(len(frios)*0.2)]
        else:
            base_pool = quentes[:int(len(quentes)*0.5)] + neutros + frios[:int(len(frios)*0.4)]

        if estrategia == "conservador":
            pool = base_pool[:int(len(base_pool)*0.7)]
        elif estrategia == "equilibrado":
            pool = base_pool
        else:
            atrasados = sorted(analise["atraso"], key=analise["atraso"].get, reverse=True)[:int(maxn * 0.3)]
            pool = list(dict.fromkeys(atrasados + base_pool))

    pool = list(dict.fromkeys(pool))
    if len(pool) < q:
        pool = list(range(1, maxn + 1))

    # V89: Personal Reinforcement
    if st.session_state.historico:
        meus_nums = [n for h in st.session_state.historico[-10:] for n in h["jogo"]]
        freq_pessoal = {n: meus_nums.count(n) for n in set(meus_nums)}
        pool = sorted(pool, key=lambda x: freq_pessoal.get(x, 0), reverse=True) + pool
        pool = list(dict.fromkeys(pool))

    for _ in range(200):
        jogo = sorted(random.sample(pool, min(q, len(pool))))
        while len(jogo) < q:
            n = random.randint(1, maxn)
            if n not in jogo:
                jogo.append(n)
        jogo = sorted(jogo[:q])
        if valida_jogo(jogo, lot):
            return jogo
    return sorted(random.sample(range(1, maxn + 1), q))

# ─── Geração por XGBoost ──────────────────────────────────────────────────────
def gerar_por_xgboost(lot, model, draws, maxn, analise_atual):
    q = configs[lot]["qtd"]
    latest_draws = sorted(draws, key=lambda x: x["concurso"], reverse=True)[:5]
    freq = {n: 0 for n in range(1, maxn + 1)}
    atraso = {n: 999 for n in range(1, maxn + 1)}
    last_seen = {n: -1 for n in range(1, maxn + 1)}
    for idx_hist, d_hist in enumerate(latest_draws):
        for n_hist in d_hist["dezenas"]:
            freq[n_hist] += 1
            if atraso[n_hist] == 999:
                atraso[n_hist] = len(latest_draws) - 1 - idx_hist
            last_seen[n_hist] = len(latest_draws) - 1 - idx_hist

    fase_num = {"Início": 0, "Meio": 1, "Fim": 2}.get(analise_atual["fase"], 1)
    ciclo_norm = analise_atual["ciclo"] / CICLOS_INFO.get(lot, {}).get("max", 11)

    prediction_features = []
    for num in range(1, maxn + 1):
        f = [freq[num], atraso[num], last_seen[num], num % 2, 1 if num in PRIMOS else 0, fase_num, ciclo_norm, freq[num] * (1 + fase_num * 0.2)]
        prediction_features.append(f)
    if model is None:
        return sorted(random.sample(range(1, maxn + 1), q))
    probabilities = model.predict_proba(np.array(prediction_features))[:, 1]

    # V89: Personal Reinforcement
    if st.session_state.historico:
        meus_nums = [n for h in st.session_state.historico[-10:] for n in h["jogo"]]
        for i, num in enumerate(range(1, maxn + 1)):
            if num in meus_nums:
                probabilities[i] *= (1 + PESO_PERSONAL_REINFORCEMENT)

    numbers_with_prob = sorted(zip(range(1, maxn + 1), probabilities), key=lambda x: x[1], reverse=True)
    for _ in range(200):
        top_numbers_pool = [n for n, prob in numbers_with_prob[:int(maxn * 0.5)]]
        if len(top_numbers_pool) < q:
            top_numbers_pool = list(range(1, maxn + 1))
        jogo = sorted(random.sample(top_numbers_pool, min(q, len(top_numbers_pool))))
        while len(jogo) < q:
            n = random.randint(1, maxn)
            if n not in jogo:
                jogo.append(n)
        jogo = sorted(jogo[:q])
        if valida_jogo(jogo, lot):
            return jogo
    return sorted(random.sample(range(1, maxn + 1), q))

# ─── Geração por LSTM ─────────────────────────────────────────────────────────
def gerar_por_lstm(lot, model_lstm, draws, maxn, sequence_length=10):
    q = configs[lot]["qtd"]
    if model_lstm is None:
        return sorted(random.sample(range(1, maxn + 1), q))
    latest_draws_for_lstm = sorted(draws, key=lambda x: x["concurso"], reverse=True)
    latest_sequence_raw = latest_draws_for_lstm[:sequence_length]
 
