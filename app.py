import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb

st.set_page_config(page_title="LOTOELITE AI", layout="wide", page_icon="🎯")
st.markdown("<h1 style=\'text-align:center;color:#d32f2f;font-size:3.2rem;font-weight:900\'>🎯 LOTOELITE AI</h1>", unsafe_allow_html=True)

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
        # Buscar mais concursos para treinamento da IA (ex: 100 concursos)
        for i in range(r.get("numero", 0), max(r.get("numero", 0) - 100, 0), -1):
            try:
                d = requests.get(f"{base}/{i}", timeout=3).json()
                draws.append({"concurso": i, "dezenas": [int(x) for x in d.get("listaDezenas", [])], "data": d.get("dataApuracao")})
            except: pass
        return {"ok": True, "latest": r, "draws": draws}
    except: return {"ok": False, "draws": []}

# Função de Feature Engineering para IA
def create_features(draws, maxn):
    features = []
    labels = []
    
    # Inverter a ordem para processar do mais antigo para o mais recente
    draws_sorted = sorted(draws, key=lambda x: x['concurso'])

    for i in range(len(draws_sorted)):
        current_draw = draws_sorted[i]
        
        # Ignorar os primeiros sorteios para ter histórico suficiente
        if i < 5: continue 

        # Histórico dos últimos 5 sorteios para features
        past_draws = draws_sorted[max(0, i-5):i]
        
        # Frequência e Atraso
        freq = {n: 0 for n in range(1, maxn + 1)}
        atraso = {n: 999 for n in range(1, maxn + 1)}
        last_seen = {n: -1 for n in range(1, maxn + 1)}

        for idx_hist, d_hist in enumerate(past_draws):
            for n_hist in d_hist['dezenas']:
                freq[n_hist] += 1
                if atraso[n_hist] == 999: # Primeira vez que aparece no histórico recente
                    atraso[n_hist] = len(past_draws) - 1 - idx_hist
                last_seen[n_hist] = len(past_draws) - 1 - idx_hist

        # Features para cada número possível
        for num in range(1, maxn + 1):
            f = [
                freq[num], # Frequência nos últimos 5 sorteios
                atraso[num], # Atraso atual
                last_seen[num], # Última vez que apareceu
                num % 2, # Par ou ímpar
                1 if num in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97] else 0 # É primo
            ]
            features.append(f)
            labels.append(1 if num in current_draw['dezenas'] else 0)
            
    return np.array(features), np.array(labels)

# Treinar Modelo de IA
@st.cache_resource
def train_model(features, labels):
    if len(features) == 0 or len(labels) == 0: return None
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    
    # Usando XGBoost para classificação
    model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, n_estimators=100)
    model.fit(X_train, y_train)
    
    # Avaliação (opcional, para debug)
    # y_pred = model.predict(X_test)
    # st.write(f"Acurácia do modelo: {accuracy_score(y_test, y_pred):.2f}")
    
    return model

# Função para gerar jogos com IA
def gerar_por_ia(lot, model, draws, maxn):
    q = configs[lot]["qtd"]
    
    # Criar features para o próximo sorteio (usando os últimos 5 sorteios disponíveis)
    latest_draws = sorted(draws, key=lambda x: x['concurso'], reverse=True)[:5]
    
    freq = {n: 0 for n in range(1, maxn + 1)}
    atraso = {n: 999 for n in range(1, maxn + 1)}
    last_seen = {n: -1 for n in range(1, maxn + 1)}

    for idx_hist, d_hist in enumerate(latest_draws):
        for n_hist in d_hist['dezenas']:
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
    
    if model is None: # Fallback se o modelo não foi treinado
        return sorted(random.sample(range(1, maxn + 1), q))

    # Prever probabilidades para cada número
    probabilities = model.predict_proba(np.array(prediction_features))[:, 1] # Probabilidade de ser sorteado
    
    # Selecionar números com base nas probabilidades
    # Usar uma abordagem ponderada para seleção
    numbers_with_prob = list(zip(range(1, maxn + 1), probabilities))
    numbers_with_prob.sort(key=lambda x: x[1], reverse=True)
    
    # Tentar gerar um jogo válido com os números mais prováveis
    for _ in range(200): # Tentar 200 vezes para encontrar um jogo válido
        # Selecionar um pool maior de números prováveis para amostrar
        # Por exemplo, os top 50% dos números com maior probabilidade
        top_numbers_pool = [n for n, prob in numbers_with_prob[:int(maxn * 0.5)]]
        
        if len(top_numbers_pool) < q: # Se não houver números suficientes, usar todos
            top_numbers_pool = list(range(1, maxn + 1))

        jogo = sorted(random.sample(top_numbers_pool, min(q, len(top_numbers_pool))))
        
        # Preencher se o jogo for menor que 'q' (pode acontecer se top_numbers_pool for pequeno)
        while len(jogo) < q:
            n = random.randint(1, maxn)
            if n not in jogo: jogo.append(n)
        jogo = sorted(jogo[:q])

        if valida_jogo(jogo, lot): 
            return jogo
            
    # Se não conseguir gerar um jogo válido após 200 tentativas, retorna um jogo aleatório
    return sorted(random.sample(range(1, maxn + 1), q))

# Funções existentes (analisar_ciclo, valida_jogo, gerar_por_estrategia) - adaptadas ou mantidas
def analisar_ciclo(draws, maxn):
    freq = {i: 0 for i in range(1, maxn + 1)}
    atraso = {i: 99 for i in range(1, maxn + 1)}
    for idx, d in enumerate(draws[:30]): # Analisa os últimos 30 concursos
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

# Streamlit UI
if 'historico' not in st.session_state: st.session_state.historico = []
if 'qtd_fech' not in st.session_state: st.session_state.qtd_fech = 21

with st.sidebar:
    lot = st.selectbox("Loteria", list(configs.keys()))
    dados = busca(lot)
    if dados["ok"]: st.success("🟢 ONLINE")
    else: st.warning("🟡 OFFLINE")
    maxn = configs[lot]["max"]
    analise = analisar_ciclo(dados["draws"], maxn) if dados["draws"] else None

    # Treinar modelo de IA na sidebar para reuso
    features, labels = create_features(dados["draws"], maxn) if dados["draws"] else ([], [])
    ai_model = train_model(features, labels)
    if ai_model: st.sidebar.success("🧠 Modelo de IA treinado!")
    else: st.sidebar.warning("🧠 Não foi possível treinar o modelo de IA.")

tabs = st.tabs(["🎲 GERADOR", "📊 MEUS JOGOS", "🔢 FECHAMENTO", "🔄 CICLO", "📈 ESTATÍSTICAS", "🧠 IA", "💡 DICAS", "🎯 DNA", "📊 RESULTADOS", "🔬 BACKTEST", "💰 PREÇOS", "🔴 AO VIVO", "🎯 ESPECIAIS"])

with tabs[0]:
    st.subheader("Gerador Inteligente v90 AI")
    if analise:
        st.info(f"Ciclo automático: {analise['fase']} - {analise['ciclo']} concursos | Quentes: {len(analise['quentes'])} | Frios: {len(analise['frios'])}")
    if st.button("GERAR 3 JOGOS INTELIGENTES (Estratégias Antigas)", type="primary", use_container_width=True):
        if analise:
            for nome, est in [("Conservador", "conservador"), ("Equilibrado", "equilibrado"), ("Agressivo", "agressivo")]:
                j = gerar_por_estrategia(lot, analise, est); st.session_state.historico.append({"j": j})
                st.success(f"{nome.upper()}: {' - '.join(f'{n:02d}' for n in j)}")
        else: st.warning("Sem dados para gerar jogos.")

    st.markdown("--- ")
    st.subheader("Gerador com IA (v90)")
    if st.button("GERAR JOGO COM IA", type="secondary", use_container_width=True):
        if ai_model and dados["draws"]:
            jogo_ia = gerar_por_ia(lot, ai_model, dados["draws"], maxn)
            st.session_state.historico.append({"j": jogo_ia})
            st.success(f"JOGO IA: {' - '.join(f'{n:02d}' for n in jogo_ia)}")
        else: st.warning("Modelo de IA não treinado ou sem dados.")

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
                st.text(f"{i + 1:02d}: {' - '.join(f'{n:02d}' for n in j)}")
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

with tabs[5]:
    st.subheader("IA v90 - Geração de Jogos com Machine Learning")
    if st.button("Gerar Jogo com IA (XGBoost)"):
        if ai_model and dados["draws"]:
            jogo_ia = gerar_por_ia(lot, ai_model, dados["draws"], maxn)
            st.session_state.historico.append({"j": jogo_ia})
            st.success(f"JOGO IA: {' - '.join(f'{n:02d}' for n in jogo_ia)}")
        else: st.warning("Modelo de IA não treinado ou sem dados.")

with tabs[6]:
    st.subheader("DICAS")
    st.success("Dica 1: Equilibre pares e ímpares")
    st.info("Dica 2: Use ciclo - Início=frios, Fim=quentes")
    st.warning("Dica 3: Sempre cubra 3 faixas de números")
    st.markdown("--- ")
    st.subheader("Dicas da IA")
    st.info("A IA analisa padrões complexos e probabilidades para sugerir números. Considere a combinação de números com maior probabilidade de ocorrência com base no histórico.")

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
    for v in vivos: st.error(f"🔥 {v['Loteria']} {v['C']} - {v['P']}")

with tabs[12]:
    st.subheader("ESPECIAIS - 3 jogos cada")
    for nome, total, qtd in [("Mega da Virada", 60, 6), ("Quina São João", 80, 5), ("Lotofácil Independência", 25, 15), ("Dupla de Páscoa", 50, 6), ("+Milionária Especial", 50, 6)]:
        st.markdown(f"**{nome}**")
        if st.button(f"Gerar {nome}", key=nome):
            for tipo in ["Conservador", "Equilibrado", "Agressivo"]:
                jogo = sorted(random.sample(range(1, total + 1), qtd))
                st.success(f"{tipo}: {' - '.join(f'{n:02d}' for n in jogo)}")

with tabs[1]: st.write(f"Total jogos: {len(st.session_state.historico)}")
with tabs[4]: st.write("Estatísticas via ciclo")
with tabs[7]: st.write("DNA ativo")
with tabs[8]:
    if dados["draws"]:
        for d in dados["draws"][:5]: st.code(f"{d['concurso']}: {'-'.join(f'{int(x):02d}' for x in d['dezenas'])}")
with tabs[9]: st.write("Backtest")
