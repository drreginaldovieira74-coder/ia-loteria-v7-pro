import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb
import matplotlib.pyplot as plt

# Importações para IA avançada
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from deap import base, creator, tools, algorithms
import shap

st.set_page_config(page_title="LOTOELITE ULTIMATE AI", layout="wide", page_icon="🚀")
st.markdown("<h1 style=\'text-align:center;color:#d32f2f;font-size:3.2rem;font-weight:900\'>🎯 LOTOELITE ULTIMATE AI</h1>", unsafe_allow_html=True)

# Configurações das Loterias
configs = {
    "Lotofácil": {"max": 25, "qtd": 15},
    "Mega-Sena": {"max": 60, "qtd": 6},
    "Quina": {"max": 80, "qtd": 5},
    "Dupla Sena": {"max": 50, "qtd": 6},
    "Timemania": {"max": 80, "qtd": 10},
    "Lotomania": {"max": 100, "qtd": 50},
    "Dia de Sorte": {"max": 31, "qtd": 7},
    "Super Sete": {"max": 9, "qtd": 7},
    "+Milionária": {"max": 50, "qtd": 6}
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
    "+Milionária": "maismilionaria"
}

# Cache para dados da API
@st.cache_data(ttl=3600) # Cache por 1 hora
def busca(lot):
    try:
        base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{API[lot]}"
        r = requests.get(base, timeout=6).json()
        draws = []
        # Buscar mais concursos para treinamento da IA (ex: 200 concursos para LSTM)
        for i in range(r.get("numero", 0), max(r.get("numero", 0) - 200, 0), -1):
            try:
                d = requests.get(f"{base}/{i}", timeout=3).json()
                draws.append({"concurso": i, "dezenas": [int(x) for x in d.get("listaDezenas", [])], "data": d.get("dataApuracao")})
            except: pass
        return {"ok": True, "latest": r, "draws": draws}
    except: return {"ok": False, "draws": []}

# --- Funções de Feature Engineering para IA --- 
def create_features_xgboost(draws, maxn):
    features = []
    labels = []
    draws_sorted = sorted(draws, key=lambda x: x["concurso"])

    for i in range(len(draws_sorted)):
        current_draw = draws_sorted[i]
        if i < 5: continue 

        past_draws = draws_sorted[max(0, i-5):i]
        
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
                1 if num in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97] else 0
            ]
            features.append(f)
            labels.append(1 if num in current_draw["dezenas"] else 0)
            
    return np.array(features), np.array(labels)

def create_sequences_lstm(draws, maxn, sequence_length=10):
    sequences = []
    next_numbers = []
    draws_sorted = sorted(draws, key=lambda x: x["concurso"])

    for i in range(len(draws_sorted) - sequence_length):
        sequence = []
        for j in range(sequence_length):
            draw_data = draws_sorted[i+j]["dezenas"]
            draw_vector = [1 if n in draw_data else 0 for n in range(1, maxn + 1)]
            sequence.append(draw_vector)
        
        next_draw_data = draws_sorted[i + sequence_length]["dezenas"]
        next_draw_vector = [1 if n in next_draw_data else 0 for n in range(1, maxn + 1)]
        
        sequences.append(sequence)
        next_numbers.append(next_draw_vector)
        
    return np.array(sequences), np.array(next_numbers)

# --- Treinamento de Modelos de IA --- 
@st.cache_resource
def train_xgboost_model(features, labels):
    if len(features) == 0 or len(labels) == 0: return None
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = xgb.XGBClassifier(objective=\'binary:logistic\', eval_metric=\'logloss\', use_label_encoder=False, n_estimators=100)
    model.fit(X_train, y_train)
    return model

@st.cache_resource
def train_lstm_model(sequences, next_numbers, maxn, sequence_length=10):
    if len(sequences) == 0 or len(next_numbers) == 0: return None
    
    X_train, X_test, y_train, y_test = train_test_split(sequences, next_numbers, test_size=0.2, random_state=42)

    model = Sequential([
        LSTM(50, activation=\'relu\', input_shape=(sequence_length, maxn)),
        Dense(maxn, activation=\'sigmoid\') # Saída para cada número possível
    ])
    model.compile(optimizer=\'adam\', loss=\'binary_crossentropy\', metrics=[\'accuracy\'])
    
    # Treinamento simplificado para Streamlit, pode ser mais longo em produção
    model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=0)
    return model

# --- Funções de Geração de Jogos com IA --- 
def gerar_por_xgboost(lot, model, draws, maxn):
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

    prediction_features = []
    for num in range(1, maxn + 1):
        f = [
            freq[num],
            atraso[num],
            last_seen[num],
            num % 2,
            1 if num in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97] else 0
        ]
        prediction_features.append(f)
    
    if model is None: 
        return sorted(random.sample(range(1, maxn + 1), q))

    probabilities = model.predict_proba(np.array(prediction_features))[:, 1]
    
    numbers_with_prob = list(zip(range(1, maxn + 1), probabilities))
    numbers_with_prob.sort(key=lambda x: x[1], reverse=True)
    
    for _ in range(200):
        top_numbers_pool = [n for n, prob in numbers_with_prob[:int(maxn * 0.5)]]
        if len(top_numbers_pool) < q: 
            top_numbers_pool = list(range(1, maxn + 1))

        jogo = sorted(random.sample(top_numbers_pool, min(q, len(top_numbers_pool))))
        
        while len(jogo) < q:
            n = random.randint(1, maxn)
            if n not in jogo: jogo.append(n)
        jogo = sorted(jogo[:q])

        if valida_jogo(jogo, lot): 
            return jogo
            
    return sorted(random.sample(range(1, maxn + 1), q))

def gerar_por_lstm(lot, model_lstm, draws, maxn, sequence_length=10):
    q = configs[lot]["qtd"]
    if model_lstm is None: 
        return sorted(random.sample(range(1, maxn + 1), q))

    # Preparar a última sequência para predição
    latest_draws_for_lstm = sorted(draws, key=lambda x: x["concurso"], reverse=True)
    latest_sequence_raw = latest_draws_for_lstm[:sequence_length]
    latest_sequence_raw.reverse() # Ordenar do mais antigo para o mais recente

    if len(latest_sequence_raw) < sequence_length: # Não há dados suficientes para uma sequência completa
        return sorted(random.sample(range(1, maxn + 1), q))

    input_sequence = []
    for d in latest_sequence_raw:
        draw_vector = [1 if n in d["dezenas"] else 0 for n in range(1, maxn + 1)]
        input_sequence.append(draw_vector)
    
    input_sequence = np.array(input_sequence).reshape(1, sequence_length, maxn)
    
    predicted_probabilities = model_lstm.predict(input_sequence)[0]
    
    numbers_with_prob = list(zip(range(1, maxn + 1), predicted_probabilities))
    numbers_with_prob.sort(key=lambda x: x[1], reverse=True)

    for _ in range(200):
        top_numbers_pool = [n for n, prob in numbers_with_prob[:int(maxn * 0.5)]]
        
        if len(top_numbers_pool) < q: 
            top_numbers_pool = list(range(1, maxn + 1))

        jogo = sorted(random.sample(top_numbers_pool, min(q, len(top_numbers_pool))))
        
        while len(jogo) < q:
            n = random.randint(1, maxn)
            if n not in jogo: jogo.append(n)
        jogo = sorted(jogo[:q])

        if valida_jogo(jogo, lot): 
            return jogo
            
    return sorted(random.sample(range(1, maxn + 1), q))

# --- Algoritmos Genéticos para Otimização de Jogos ---
# Definir o tipo de problema: maximizar a aptidão (fitness)
if "FitnessMax" not in creator.__dict__:
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
if "Individual" not in creator.__dict__:
    creator.create("Individual", list, fitness=creator.FitnessMax)

def eval_game(individual, model_xgboost, draws, maxn, lot):
    # Avaliar a aptidão de um jogo (individual)
    
    if not valida_jogo(individual, lot): # Jogos inválidos têm aptidão muito baixa
        return -1000000, # A vírgula é importante para retornar uma tupla

    # Gerar features para cada número no individual (como se fosse o próximo sorteio)
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

    prediction_features = []
    for num in individual:
        f = [
            freq[num],
            atraso[num],
            last_seen[num],
            num % 2,
            1 if num in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97] else 0
        ]
        prediction_features.append(f)
    
    if model_xgboost is None or len(prediction_features) == 0:
        return 0, # Aptidão neutra se o modelo não estiver disponível

    probabilities = model_xgboost.predict_proba(np.array(prediction_features))[:, 1]
    fitness = sum(probabilities) # Soma das probabilidades dos números no jogo
    
    return fitness, 

def generate_game_genetic_algorithm(lot, model_xgboost, draws, maxn):
    q = configs[lot]["qtd"]

    toolbox = base.Toolbox()
    # Atributo: um número aleatório dentro do range da loteria
    toolbox.register("attr_num", random.randint, 1, maxn)
    # Indivíduo: um jogo (lista de \'q\' números únicos)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_num, q)
    # População: uma lista de indivíduos
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", eval_game, model_xgboost=model_xgboost, draws=draws, maxn=maxn, lot=lot)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=1, up=maxn, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=50) # População inicial de 50 jogos
    NGEN = 20 # Número de gerações

    for gen in range(NGEN):
        offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
        fits = toolbox.map(toolbox.evaluate, offspring)
        for ind, fit in zip(offspring, fits):
            ind.fitness.values = fit
        population = toolbox.select(offspring, k=len(population))

    top_individual = tools.selBest(population, k=1)[0]
    return sorted(list(set(top_individual)))[:q] # Garantir números únicos e quantidade correta

# --- Funções existentes (analisar_ciclo, valida_jogo, gerar_por_estrategia) --- 
def analisar_ciclo(draws, maxn):
    freq = {i: 0 for i in range(1, maxn + 1)}
    atraso = {i: 99 for i in range(1, maxn + 1)}
    for idx, d in enumerate(draws[:30]): 
        for n in d["dezenas"]:
            freq[n] += 1
            if atraso[n] == 99: atraso[n] = idx
    quentes = sorted(freq, key=freq.get, reverse=True)[:max(5, int(maxn * 0.35))]
    frios = sorted(freq, key=freq.get)[:max(5, int(maxn * 0.30))]
    neutros = [n for n in range(1, maxn + 1) if n not in quentes and n not in frios]
    seen = set(); ciclo = 0
    for d in draws:
        seen.update(d["dezenas"]); ciclo += 1
        if len(seen) >= maxn: break
    fase = "Início" if ciclo <= 4 else "Meio" if ciclo <= 8 else "Fim"
    return {"quentes": quentes, "frios": frios, "neutros": neutros, "atraso": atraso, "fase": fase, "ciclo": ciclo, "freq": freq}

def valida_jogo(jogo, lot):
    jogo = sorted(jogo)
    if lot == "Mega-Sena":
        baixo = len([n for n in jogo if n <= 20]); meio = len([n for n in jogo if 21 <= n <= 40]); alto = len([n for n in jogo if n > 40])
        return baixo >= 1 and meio >= 1 and alto >= 1
    if lot == "Quina":
        baixo = len([n for n in jogo if n <= 26]); meio = len([n for n in jogo if 27 <= n <= 53]); alto = len([n for n in jogo if n > 53])
        return baixo >= 1 and alto >= 1
    if lot == "Lotofácil":
        pares = len([n for n in jogo if n % 2 == 0]); return 6 <= pares <= 9
    if lot == "Dupla Sena":
        return len([n for n in jogo if n <= 25]) >= 2
    return True

def gerar_por_estrategia(lot, analise, estrategia):
    q = configs[lot]["qtd"]; maxn = configs[lot]["max"]
    quentes = analise["quentes"]; frios = analise["frios"]; neutros = analise["neutros"]; atraso = analise["atraso"]
    if estrategia == "conservador":
        pool = quentes[:int(len(quentes) * 0.7)] + neutros[:int(len(neutros) * 0.5)]
    elif estrategia == "equilibrado":
        pool = quentes[:int(len(quentes) * 0.5)] + neutros[:int(len(neutros) * 0.6)] + frios[:int(len(frios) * 0.4)]
    else:
        atrasados = sorted(atraso, key=atraso.get, reverse=True)[:int(maxn * 0.3)]
        pool = atrasados + frios[:int(len(frios) * 0.6)] + quentes[:int(len(quentes) * 0.3)]
    pool = list(dict.fromkeys(pool))
    if len(pool) < q: pool = list(range(1, maxn + 1))
    for _ in range(200):
        jogo = sorted(random.sample(pool, min(q, len(pool))))
        while len(jogo) < q:
            n = random.randint(1, maxn)
            if n not in jogo: jogo.append(n)
        jogo = sorted(jogo[:q])
        if valida_jogo(jogo, lot): return jogo
    return sorted(random.sample(range(1, maxn + 1), q))

# --- Streamlit UI --- 
if \'historico\' not in st.session_state: st.session_state.historico = []
if \'qtd_fech\' not in st.session_state: st.session_state.qtd_fech = 21

with st.sidebar:
    lot = st.selectbox("Loteria", list(configs.keys()))
    dados = busca(lot)
    if dados["ok"]: st.success("🟢 ONLINE")
    else: st.warning("🟡 OFFLINE")
    maxn = configs[lot]["max"]
    analise = analisar_ciclo(dados["draws"], maxn) if dados["draws"] else None

    # Treinar modelos de IA na sidebar para reuso
    # XGBoost
    features_xgb, labels_xgb = create_features_xgboost(dados["draws"], maxn) if dados["draws"] else (np.array([]), np.array([]))
    xgboost_model = train_xgboost_model(features_xgb, labels_xgb)
    if xgboost_model: st.sidebar.success("🧠 Modelo XGBoost treinado!")
    else: st.sidebar.warning("🧠 Não foi possível treinar o modelo XGBoost.")

    # LSTM
    sequences_lstm, next_numbers_lstm = create_sequences_lstm(dados["draws"], maxn) if dados["draws"] else (np.array([]), np.array([]))
    lstm_model = train_lstm_model(sequences_lstm, next_numbers_lstm, maxn) if len(sequences_lstm) > 0 else None
    if lstm_model: st.sidebar.success("🧠 Modelo LSTM treinado!")
    else: st.sidebar.warning("🧠 Não foi possível treinar o modelo LSTM.")

tabs = st.tabs(["🎲 GERADOR", "📊 MEUS JOGOS", "🔢 FECHAMENTO", "🔄 CICLO", "📈 ESTATÍSTICAS", "🧠 IA AVANÇADA", "💡 DICAS", "🎯 DNA", "📊 RESULTADOS", "🔬 BACKTEST", "💰 PREÇOS", "🔴 AO VIVO", "🎯 ESPECIAIS"])

with tabs[0]:
    st.subheader("Gerador Inteligente v100 ULTIMATE")
    if analise:
        st.info(f"Ciclo automático: {analise["fase"]} - {analise["ciclo"]} concursos | Quentes: {len(analise["quentes"])} | Frios: {len(analise["frios"])}")
    
    st.markdown("--- ")
    st.subheader("Gerador com Estratégias Tradicionais")
    if st.button("GERAR 3 JOGOS INTELIGENTES (Estratégias Antigas)", type="primary", use_container_width=True):
        if analise:
            for nome, est in [("Conservador", "conservador"), ("Equilibrado", "equilibrado"), ("Agressivo", "agressivo")]:
                j = gerar_por_estrategia(lot, analise, est); st.session_state.historico.append({"j": j})
                st.success(f"{nome.upper()}: {\' - \'.join(f\'\\{n:02d}\' for n in j)}")
        else: st.warning("Sem dados para gerar jogos.")

with tabs[5]: # Aba de IA Avançada
    st.subheader("IA v100 ULTIMATE - Geração de Jogos com Machine Learning e Otimização")

    if st.button("GERAR JOGO com XGBoost", type="secondary", use_container_width=True):
        if xgboost_model is not None and dados["draws"]:
            jogo_ia = gerar_por_xgboost(lot, xgboost_model, dados["draws"], maxn)
            st.session_state.historico.append({"j": jogo_ia})
            st.success(f"JOGO XGBoost: {\' - \'.join(f\'\\{n:02d}\' for n in jogo_ia)}")

            # XAI com SHAP para XGBoost
            st.subheader("Explicação da IA (XGBoost)")
            if features_xgb.shape[0] > 0:
                try:
                    # A visualização SHAP pode ser computacionalmente intensiva para Streamlit.
                    # Em vez de plotar, vamos fornecer uma explicação textual simplificada.
                    feature_names = ["Frequência", "Atraso", "Última Vez", "Par/Ímpar", "Primo"]
                    feature_importances = xgboost_model.feature_importances_
                    sorted_features = sorted(zip(feature_names, feature_importances), key=lambda x: x[1], reverse=True)
                    st.write("**Fatores mais influentes na escolha dos números (XGBoost):**")
                    for name, importance in sorted_features:
                        st.write(f"- {name}: {importance:.4f}")
                    st.info("Para uma análise mais aprofundada com gráficos SHAP, considere executar o SHAP em um ambiente local ou com menos dados.")

                except Exception as e:
                    st.error(f"Erro ao gerar explicação SHAP: {e}")
            else:
                st.info("Não há dados suficientes para gerar explicações SHAP.")

        else: st.warning("Modelo XGBoost não treinado ou sem dados.")

    if st.button("GERAR JOGO com LSTM", type="secondary", use_container_width=True):
        if lstm_model is not None and dados["draws"]:
            jogo_lstm = gerar_por_lstm(lot, lstm_model, dados["draws"], maxn)
            st.session_state.historico.append({"j": jogo_lstm})
            st.success(f"JOGO LSTM: {\' - \'.join(f\'\\{n:02d}\' for n in jogo_lstm)}")
        else: st.warning("Modelo LSTM não treinado ou sem dados.")

    if st.button("GERAR JOGO com Algoritmo Genético", type="secondary", use_container_width=True):
        if xgboost_model is not None and dados["draws"]:
            # DEAP creator.create pode dar erro se chamado múltiplas vezes
            # Verificar se já foi criado
            if "FitnessMax" not in creator.__dict__:
                creator.create("FitnessMax", base.Fitness, weights=(1.0,))
            if "Individual" not in creator.__dict__:
                creator.create("Individual", list, fitness=creator.FitnessMax)

            jogo_ag = generate_game_genetic_algorithm(lot, xgboost_model, dados["draws"], maxn)
            st.session_state.historico.append({"j": jogo_ag})
            st.success(f"JOGO AG: {\' - \'.join(f\'\\{n:02d}\' for n in jogo_ag)}")
        else: st.warning("Modelo XGBoost não treinado ou sem dados para Algoritmo Genético.")

with tabs[9]: # Aba de Backtest
    st.subheader("🔬 Backtest Avançado")
    st.info("Esta seção permitirá avaliar o desempenho dos modelos de IA e estratégias ao longo do tempo.")
    
    backtest_period = st.slider("Período de Backtest (número de sorteios passados)", min_value=10, max_value=min(len(dados["draws"]) if dados["draws"] else 10, 100), value=20)
    min_train_draws = st.slider("Mínimo de sorteios para treinamento", min_value=5, max_value=backtest_period - 1, value=10)

    if st.button("Executar Backtest Completo"):
        if xgboost_model is not None and dados["draws"] and len(dados["draws"]) >= backtest_period:
            st.write(f"Executando backtest para o modelo XGBoost nos últimos {backtest_period} sorteios...")
            
            total_draws = len(dados["draws"])
            test_period_draws = dados["draws"][-backtest_period:] 
            
            results = [] # Para armazenar os resultados de cada sorteio no backtest

            for i in range(backtest_period - 1):
                # Treinar o modelo com dados até o sorteio atual - 1
                train_data_for_backtest = dados["draws"][:total_draws - backtest_period + i]
                
                if len(train_data_for_backtest) < min_train_draws: 
                    st.warning(f"Pulando sorteio {i+1}: dados insuficientes para treinamento ({len(train_data_for_backtest)} < {min_train_draws}).")
                    continue 

                features_bt, labels_bt = create_features_xgboost(train_data_for_backtest, maxn)
                model_bt = train_xgboost_model(features_bt, labels_bt)

                if model_bt:
                    predicted_game = gerar_por_xgboost(lot, model_bt, train_data_for_backtest, maxn)
                    actual_draw = test_period_draws[i+1]["dezenas"]
                    
                    hits = len(set(predicted_game).intersection(set(actual_draw)))
                    results.append({"Concurso": test_period_draws[i+1]["concurso"], "Jogo Previsto": predicted_game, "Sorteio Real": actual_draw, "Acertos": hits})
            
            if results:
                df_results = pd.DataFrame(results)
                st.dataframe(df_results)
                st.success(f"Backtest XGBoost concluído. Média de acertos: {df_results[\"Acertos\"].mean():.2f}")
                st.line_chart(df_results.set_index("Concurso")["Acertos"])
            else:
                st.warning("Nenhum resultado de backtest gerado. Verifique os parâmetros e dados.")
        else:
            st.warning("Modelo XGBoost não treinado ou dados insuficientes para backtest.")


# --- Outras abas (mantidas do v90_AI) ---
with tabs[1]: st.write(f"Total jogos: {len(st.session_state.historico)}")
with tabs[2]:
    st.subheader("FECHAMENTO - baseado no ciclo")
    c1, c2 = st.columns(2)
    if c1.button("➕"): st.session_state.qtd_fech += 1
    if c2.button("➖"): st.session_state.qtd_fech = max(1, st.session_state.qtd_fech - 1)
    st.metric("Quantidade", st.session_state.qtd_fech)
    if st.button("GERAR FECHAMENTO INTELIGENTE"):
        if analise:
            pool = list(dict.fromkeys(analise["quentes"][:12] + analise["neutros"][:8] + analise["frios"][:5]))
            q = configs[lot]["qtd"]
            for i in range(st.session_state.qtd_fech):
                for _ in range(100):
                    j = sorted(random.sample(pool, min(q, len(pool))))
                    if valida_jogo(j, lot): break
                st.text(f"{i + 1:02d}: {\' - \'.join(f\'\\{n:02d}\' for n in j)}")
        else: st.warning("Sem dados para gerar fechamento.")

with tabs[3]:
    st.subheader("CICLO - análise automática")
    if st.button("🔄 Atualizar Ciclo"): st.rerun()
    if analise:
        df = pd.DataFrame([{"Concurso": d["concurso"], "Qtd": len(d["dezenas"])} for d in dados["draws"][:12]])
        st.bar_chart(df.set_index("Concurso"))
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in sorted(analise["quentes"])))
        with c2: st.markdown("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in sorted(analise["frios"])))
        with c3: st.markdown("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in sorted(analise["neutros"][:30])))

with tabs[4]: st.write("Estatísticas via ciclo")

with tabs[6]:
    st.subheader("DICAS")
    st.success("Dica 1: Equilibre pares e ímpares")
    st.info("Dica 2: Use ciclo - Início=frios, Fim=quentes")
    st.warning("Dica 3: Sempre cubra 3 faixas de números")
    st.markdown("--- ")
    st.subheader("Dicas da IA")
    st.info("A IA analisa padrões complexos e probabilidades para sugerir números. Considere a combinação de números com maior probabilidade de ocorrência com base no histórico.")

with tabs[7]: st.write("DNA ativo")
with tabs[8]:
    if dados["draws"]:
        for d in dados["draws"][:5]: st.code(f"{d["concurso"]}: {\'-\'.join(f\'\\{int(x):02d}\' for x in d["dezenas"])})

with tabs[10]:
    tabela = [{"Loteria": "Lotofácil", "Mínimo": "R$ 3,50", "Máximo": "R$ 46.512"},
              {"Loteria": "Mega-Sena", "Mínimo": "R$ 6,00", "Máximo": "R$ 232.560"},
              {"Loteria": "Quina", "Mínimo": "R$ 3,00", "Máximo": "R$ 9.009"},
              {"Loteria": "Dupla Sena", "Mínimo": "R$ 3,00", "Máximo": "R$ 15.015"},
              {"Loteria": "Timemania", "Mínimo": "R$ 3,50", "Máximo": "R$ 3,50"},
              {"Loteria": "Lotomania", "Mínimo": "R$ 3,00", "Máximo": "R$ 3,00"},
              {"Loteria": "Dia de Sorte", "Mínimo": "R$ 2,50", "Máximo": "R$ 8.037,50"},
              {"Loteria": "Super Sete", "Mínimo": "R$ 3,00", "Máximo": "R$ 26.460"},
              {"Loteria": "+Milionária", "Mínimo": "R$ 6,00", "Máximo": "R$ 83.160"}]
    st.dataframe(pd.DataFrame(tabela), hide_index=True, use_container_width=True)

with tabs[11]:
    vivos = [{"Loteria": "Mega-Sena", "C": 2998, "P": "R$ 60.000.000"},
             {"Loteria": "Quina", "C": 7004, "P": "R$ 20.000.000"},
             {"Loteria": "+Milionária", "C": 347, "P": "R$ 36.000.000"},
             {"Loteria": "Lotofácil", "C": 3664, "P": "R$ 2.000.000"},
             {"Loteria": "Dupla Sena", "C": 2946, "P": "R$ 1.200.000"},
             {"Loteria": "Timemania", "C": 2180, "P": "R$ 3.200.000"},
             {"Loteria": "Lotomania", "C": 2750, "P": "R$ 1.800.000"},
             {"Loteria": "Dia de Sorte", "C": 1025, "P": "R$ 800.000"},
             {"Loteria": "Super Sete", "C": 836, "P": "R$ 6.300.000"}]
    for v in vivos: st.error(f"🔥 {v["Loteria"]} {v["C"]} - {v["P"]}")

with tabs[12]:
    st.subheader("ESPECIAIS - 3 jogos cada")
    for nome, total, qtd in [("Mega da Virada", 60, 6), ("Quina São João", 80, 5), ("Lotofácil Independência", 25, 15), ("Dupla de Páscoa", 50, 6), ("+Milionária Especial", 50, 6)]:
        st.markdown(f"**{nome}**")
        if st.button(f"Gerar {nome}", key=nome):
            for tipo in ["Conservador", "Equilibrado", "Agressivo"]:
                jogo = sorted(random.sample(range(1, total + 1), qtd))
                st.success(f"{tipo}: {\' - \'.join(f\'\\{n:02d}\' for n in jogo)}")
