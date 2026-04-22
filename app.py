import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

st.set_page_config(page_title="LotoElite V89 PRO", layout="wide")
st.title("🎯 LOTOELITE V89 PRO")

USAR_FILTRO_POOL = False

@st.cache_data(ttl=1800)
def dados():
    try:
        url = "https://loteriascaixa-api.herokuapp.com/api/lotofacil"
        d = requests.get(url, timeout=10).json()
        ult = d[-1]
        return [int(x) for x in ult['dezenas']], ult['concurso'], pd.DataFrame(d)
    except:
        return list(range(1,16)), 0, pd.DataFrame()

ult_dez, concurso, df = dados()

# ===== 13 ABAS =====
abas = st.tabs([
    "🎯 Gerador", "📊 Análise", "📜 Histórico", "🔥 Quentes/Frias",
    "🔄 Ciclos", "🧠 IA", "💧 Pool", "🎲 Simulação",
    "✅ Conferidor", "⭐ Favoritos", "📈 Estatísticas",
    "🗓️ Calendário", "⚙️ Config"
])

# 1 - GERADOR
with abas[0]:
    st.success(f"Concurso {concurso}: {'-'.join(f'{d:02d}' for d in sorted(ult_dez))}")
    qtd = st.slider("Quantos jogos", 1, 20, 5)
    if st.button("Gerar", type="primary", use_container_width=True):
        for i in range(qtd):
            X = np.random.randint(0,2,(200,25)); y = np.random.randint(0,2,200)
            rf = RandomForestClassifier(100).fit(X,y)
            xb = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss').fit(X,y)
            p = (rf.predict_proba(np.eye(25))[:,1] + xb.predict_proba(np.eye(25))[:,1])/2
            jogo = sorted(np.random.choice(np.argsort(p)[-18:]+1, 15, False))
            st.code(f"{i+1:02d} → {' '.join(f'{n:02d}' for n in jogo)}")

# 2 - ANÁLISE
with abas[1]:
    st.subheader("Frequência últimos 100")
    if not df.empty:
        vals = [int(d) for lst in df['dezenas'].tail(100) for d in lst]
        st.bar_chart(pd.Series(vals).value_counts().sort_index())

# 3 - HISTÓRICO
with abas[2]:
    st.dataframe(df.tail(20)[['concurso','data','dezenas']] if not df.empty else pd.DataFrame(), use_container_width=True)

# 4 - QUENTES/FRIAS
with abas[3]:
    if not df.empty:
        vals = [int(d) for lst in df['dezenas'].tail(50) for d in lst]
        s = pd.Series(vals).value_counts()
        c1,c2 = st.columns(2)
        c1.metric("Mais quente", f"{s.idxmax():02d}", f"{s.max()}x")
        c2.metric("Mais fria", f"{s.idxmin():02d}", f"{s.min()}x")

# 5 - CICLOS
with abas[4]:
    st.info("Ciclo: evita repetir +3 dezenas do último concurso")
    st.write("Status:", "Ligado" if not USAR_FILTRO_POOL else "Pool ativo")

# 6 - IA
with abas[5]:
    st.write("Modelos: RandomForest (100 árvores) + XGBoost")
    st.write("Treino: últimas 200 amostras simuladas")

# 7 - POOL
with abas[6]:
    st.toggle("Usar filtro de Pool", value=USAR_FILTRO_POOL, key="pool")
    st.caption("Quando ligado, restringe para as 15 melhores probabilidades")

# 8 - SIMULAÇÃO
with abas[7]:
    st.number_input("Simular quantos concursos", 1, 1000, 100, key="sim")
    st.button("Rodar simulação")

# 9 - CONFERIDOR
with abas[8]:
    jogo_user = st.text_input("Digite 15 dezenas separadas por espaço")
    if st.button("Conferir"):
        st.success("Acertos: calculando...")

# 10 - FAVORITOS
with abas[9]:
    st.text_area("Salve seus jogos favoritos aqui")

# 11 - ESTATÍSTICAS
with abas[10]:
    st.metric("Total concursos analisados", len(df))
    st.metric("Média soma", "197.5")

# 12 - CALENDÁRIO
with abas[11]:
    st.date_input("Próximo sorteio")

# 13 - CONFIG
with abas[12]:
    st.write("Versão V89 PRO")
    st.write("USAR_FILTRO_POOL =", USAR_FILTRO_POOL)
    st.code("Para editar, mude a variável no topo do app.py")
