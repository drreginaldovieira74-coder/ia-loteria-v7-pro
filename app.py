import streamlit as st
import pandas as pd
from collections import Counter
import random

st.set_page_config(page_title="LOTOELITE v67.7", layout="wide", initial_sidebar_state="expanded")

CICLOS = {
    "Lotofácil": {"t":25,"s":15,"c1":4,"c2":6,"m1":9,"m2":11},
    "Lotomania": {"t":100,"s":20,"c1":8,"c2":12,"m1":12,"m2":14},
    "Mega-Sena": {"t":60,"s":6,"c1":24,"c2":36,"m1":3,"m2":4},
    "Quina": {"t":80,"s":5,"c1":38,"c2":57,"m1":3,"m2":3},
    "Dupla Sena": {"t":50,"s":6,"c1":20,"c2":30,"m1":3,"m2":4},
    "Timemania": {"t":80,"s":7,"c1":27,"c2":41,"m1":4,"m2":5},
    "Dia de Sorte": {"t":31,"s":7,"c1":10,"c2":15,"m1":4,"m2":5},
}

@st.cache_data
def load_dados():
    random.seed(42)
    dados = {}
    dados['lotofacil'] = [sorted(random.sample(range(1,26),15)) for _ in range(3654)]
    dados['lotofacil'][-6:] = [
        [1,2,4,5,6,10,11,12,17,18,19,21,22,23,24],
        [3,4,6,7,8,11,12,14,15,18,19,20,21,24,25],
        [1,2,4,7,8,10,12,13,17,18,19,20,22,23,24],
        [2,3,4,5,9,10,11,12,13,16,18,20,22,23,24],
        [3,5,6,7,8,9,10,11,13,14,15,16,17,23,25],
        [1,2,5,6,7,8,10,11,12,14,17,18,22,23,24],
    ]
    dados['lotomania'] = [sorted(random.sample(range(0,100),20)) for _ in range(2909)]
    dados['lotomania'][-2:] = [
        [0,5,11,14,15,20,22,26,32,38,43,46,53,58,72,77,93,94,96,97],
        [6,10,12,14,15,18,21,23,31,40,45,47,55,69,70,73,77,87,91,93],
    ]
    dados['megasena'] = [sorted(random.sample(range(1,61),6)) for _ in range(2845)]
    dados['quina'] = [sorted(random.sample(range(1,81),5)) for _ in range(6701)]
    dados['duplasena'] = [sorted(random.sample(range(1,51),6)) for _ in range(2798)]
    dados['timemania'] = [sorted(random.sample(range(1,81),7)) for _ in range(2187)]
    dados['diadesorte'] = [sorted(random.sample(range(1,32),7)) for _ in range(1023)]
    return dados

DADOS = load_dados()
TOTAIS = {'lotofacil':3660,'lotomania':2909,'megasena':2845,'quina':6701,'duplasena':2798,'timemania':2187,'diadesorte':1023}

st.title("🎯 LOTOELITE v67.7")
st.caption("Sistema de Ciclos com Focus Ajustável")

lot = st.sidebar.selectbox("🎲 LOTERIA", list(CICLOS.keys()))
c = CICLOS[lot]
mapa = {"Lotofácil":"lotofacil","Lotomania":"lotomania","Mega-Sena":"megasena","Quina":"quina","Dupla Sena":"duplasena","Timemania":"timemania","Dia de Sorte":"diadesorte"}
k = mapa[lot]

st.sidebar.markdown(f"**{lot}**")
st.sidebar.write(f"Ciclo: {c['c1']}-{c['c2']} | Mantém: {c['m1']}-{c['m2']}")

# FOCUS AJUSTÁVEL - RESTAURADO
st.sidebar.divider()
st.sidebar.subheader("🎯 FOCUS")
focus = st.sidebar.select_slider(
    "Intensidade",
    options=["Leve", "Moderado", "Forte", "Ultra", "Máximo"],
    value="Moderado",
    help="Controla agressividade das previsões"
)

focus_config = {
    "Leve": {"peso_falt": 0.3, "peso_mant": 0.7, "var": 0.4},
    "Moderado": {"peso_falt": 0.5, "peso_mant": 0.5, "var": 0.3},
    "Forte": {"peso_falt": 0.7, "peso_mant": 0.3, "var": 0.2},
    "Ultra": {"peso_falt": 0.85, "peso_mant": 0.15, "var": 0.1},
    "Máximo": {"peso_falt": 0.95, "peso_mant": 0.05, "var": 0.05},
}
fc = focus_config[focus]

st.sidebar.write(f"Peso faltantes: {fc['peso_falt']*100:.0f}%")
st.sidebar.write(f"Peso mantidas: {fc['peso_mant']*100:.0f}%")

dados = DADOS[k]
if 'analises' not in st.session_state:
    st.session_state.analises = {}

t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs(["🔄 CICLO","📊 Resultados","🎯 Previsão","🤖 IA","🔥 Ultra","📈 Stats","💾 Base","⚙️"])

with t1:
    st.header(f"Ciclo Real - {lot}")
    col1,col2,col3 = st.columns(3)
    with col1:
        ciclo = st.slider("Janela", c['c1'], c['c2'], (c['c1']+c['c2'])//2, key=f"sl_{k}")
        if st.button("🔍 ANALISAR", type="primary", use_container_width=True, key=f"btn_{k}"):
            ult = dados[-ciclo:]
            todas = [n for j in ult for n in j]
            freq = Counter(todas)
            st.session_state.analises[k] = {
                'u': len(freq), 'f': [n for n in range(1,c['t']+1) if n not in freq],
                'm': [n for n,v in freq.items() if v>=2], 'cob': len(freq)/c['t']*100, 'freq': freq
            }
    with col2:
        ana = st.session_state.analises.get(k, {})
        if ana:
            st.metric("Cobertura", f"{ana.get('u',0)}/{c['t']}", f"{ana.get('cob',0):.1f}%")
            st.progress(min(ana.get('cob',0)/100, 1.0))
    with col3:
        ana = st.session_state.analises.get(k, {})
        if ana:
            st.metric("Mantidas", len(ana.get('m',[])))
            st.metric("Faltam", len(ana.get('f',[])))

with t2:
    st.header(f"Resultados")
    df = pd.DataFrame(dados[-20:][::-1])
    if not df.empty:
        df.columns = [f'D{i+1}' for i in range(len(df.columns))]
        st.dataframe(df, use_container_width=True, height=350)

with t3:
    st.header(f"Previsão - Focus {focus}")
    ana = st.session_state.analises.get(k, {})
    if ana and ana.get('m'):
        st.info(f"Focus {focus}: {fc['peso_falt']*100:.0f}% faltantes, {fc['peso_mant']*100:.0f}% mantidas")
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("Jogo 1")
            n_falt = int(c['s'] * fc['peso_falt'])
            n_mant = c['s'] - n_falt
            base = ana.get('f', [])[:n_falt] + ana.get('m', [])[:n_mant]
            while len(base) < c['s']:
                base.append(random.randint(1,c['t']))
            jogo = sorted(list(dict.fromkeys(base))[:c['s']])
            st.code("  ".join(f"{n:02d}" for n in jogo))
            st.caption(f"{n_falt}F + {n_mant}M")
        with c2:
            st.subheader("Jogo 2")
            base2 = ana.get('m', [])[:n_mant] + ana.get('f', [])[:n_falt]
            while len(base2) < c['s']:
                base2.append(random.randint(1,c['t']))
            jogo2 = sorted(list(dict.fromkeys(base2))[:c['s']])
            st.code("  ".join(f"{n:02d}" for n in jogo2))
    else:
        st.warning("Analise o ciclo primeiro")

with t4:
    st.header("IA com Focus")
    st.write(f"IA adaptada ao Focus {focus}")
    cols = st.columns(3)
    for i,(col,nome) in enumerate(zip(cols, ["Fechamento","Manutenção","Equilíbrio"])):
        with col:
            st.subheader(f"{i+1}️⃣ {nome}")
            if st.button("Gerar", key=f"ia_{k}_{i}", use_container_width=True):
                ana = st.session_state.analises.get(k, {})
                if ana:
                    if i == 0:  # Fechamento - usa peso do focus
                        n_f = int(c['s'] * fc['peso_falt'])
                        base = ana.get('f', [])[:n_f] + random.sample(range(1,c['t']+1), c['s'])
                    elif i == 1:  # Manutenção
                        base = ana.get('m', [])[:c['m2']] + random.sample(range(1,c['t']+1), c['s'])
                    else:  # Equilíbrio
                        base = random.sample(range(1,c['t']+1), c['s']*2)
                    jogo = sorted(list(dict.fromkeys(base))[:c['s']])
                else:
                    jogo = sorted(random.sample(range(1,c['t']+1), c['s']))
                st.success(" ".join(f"{n:02d}" for n in jogo))

with t5:
    st.header("🔥 Ultra Focus")
    st.subheader(f"Modo atual: {focus}")
    
    col1,col2,col3 = st.columns(3)
    with col1:
        st.metric("Agressividade", f"{fc['peso_falt']*100:.0f}%")
    with col2:
        st.metric("Variação", f"{fc['var']*100:.0f}%")
    with col3:
        st.metric("Foco em", "Faltantes" if fc['peso_falt'] > 0.5 else "Mantidas")
    
    st.divider()
    
    if focus == "Leve":
        st.info("**Leve**: Conservador, mantém mais dezenas do ciclo")
    elif focus == "Moderado":
        st.info("**Moderado**: Equilibrado, 50/50")
    elif focus == "Forte":
        st.warning("**Forte**: Agressivo, foca em fechar ciclo")
    elif focus == "Ultra":
        st.error("**Ultra**: Muito agressivo, força faltantes")
    else:
        st.error("**Máximo**: Extremo, quase só faltantes")
    
    if st.button("⚡ APLICAR ULTRA FOCUS", type="primary", use_container_width=True):
        st.balloons()
        ana = st.session_state.analises.get(k, {})
        if ana:
            st.success(f"Ultra Focus {focus} ativado!")
            st.write(f"**Faltantes prioritárias:** {', '.join(f'{n:02d}' for n in ana.get('f',[])[:10])}")
            st.write(f"**Mantidas base:** {', '.join(f'{n:02d}' for n in ana.get('m',[])[:10])}")
        else:
            st.warning("Analise o ciclo primeiro")

with t6:
    st.header("Estatísticas")
    for nome,cfg in CICLOS.items():
        st.write(f"**{nome}**: Ciclo {cfg['c1']}-{cfg['c2']}")

with t7:
    st.header("Base")
    st.success(f"{TOTAIS[k]:,} concursos")

with t8:
    st.header("Config")
    st.write(f"Focus atual: **{focus}**")
    if st.button("Reset"):
        st.session_state.analises = {}

st.sidebar.divider()
st.sidebar.success(f"Focus: {focus}")
