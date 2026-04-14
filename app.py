import streamlit as st
import pandas as pd
from collections import Counter
import random

st.set_page_config(page_title="LOTOELITE v67.8", layout="wide")

# FORÇAR VERSÃO VISÍVEL
st.sidebar.error("🔴 v67.8 ATIVA")

CICLOS = {
    "Lotofácil": {"t":25,"s":15,"c1":4,"c2":6,"m1":9,"m2":11},
    "Lotomania": {"t":100,"s":20,"c1":8,"c2":12,"m1":12,"m2":14},
    "Mega-Sena": {"t":60,"s":6,"c1":24,"c2":36,"m1":3,"m2":4},
    "Quina": {"t":80,"s":5,"c1":38,"c2":57,"m1":3,"m2":3},
    "Dupla Sena": {"t":50,"s":6,"c1":20,"c2":30,"m1":3,"m2":4},
    "Timemania": {"t":80,"s":7,"c1":27,"c2":41,"m1":4,"m2":5},
    "Dia de Sorte": {"t":31,"s":7,"c1":10,"c2":15,"m1":4,"m2":5},
}

DADOS = {
'lotofacil': [[1,3,5,9,10,11,13,17,18,19,20,22,23,24,25],[2,4,6,7,8,12,14,15,16,17,18,19,21,22,24],[1,2,5,6,7,8,10,11,12,14,17,18,22,23,24]],
'lotomania': [[6,10,12,14,15,18,21,23,31,40,45,47,55,69,70,73,77,87,91,93],[0,5,11,14,15,20,22,26,32,38,43,46,53,58,72,77,93,94,96,97]],
'megasena': [[7,15,23,34,45,56],[3,12,28,33,41,52]],
'quina': [[12,24,36,48,72],[5,17,29,41,63]],
'duplasena': [[3,14,25,36,47,50],[5,16,27,38,49,51]],
'timemania': [[4,11,18,25,32,39,46],[7,14,21,28,35,42,49]],
'diadesorte': [[2,8,14,19,23,27,31],[3,9,15,20,24,28,30]],
}

st.title("🎯 LOTOELITE v67.8 - FOCUS")
st.caption("VERSÃO NOVA - Se você vê v67.4, não atualizou")

lot = st.sidebar.selectbox("LOTERIA", list(CICLOS.keys()))
c = CICLOS[lot]
k = {"Lotofácil":"lotofacil","Lotomania":"lotomania","Mega-Sena":"megasena","Quina":"quina","Dupla Sena":"duplasena","Timemania":"timemania","Dia de Sorte":"diadesorte"}[lot]

# FOCUS - AGORA BEM VISÍVEL
st.sidebar.divider()
st.sidebar.subheader("🎯 FOCUS AJUSTÁVEL")
focus = st.sidebar.select_slider(
    "Intensidade",
    options=["Leve","Moderado","Forte","Ultra","Máximo"],
    value="Moderado"
)
fc = {"Leve":0.3,"Moderado":0.5,"Forte":0.7,"Ultra":0.85,"Máximo":0.95}[focus]

st.sidebar.markdown(f"""
<div style='background:#FF6B6B30;padding:10px;border-radius:5px;text-align:center'>
<b>FOCUS: {focus.upper()}</b><br>
<small>{fc*100:.0f}% faltantes</small>
</div>
""", unsafe_allow_html=True)

st.sidebar.write(f"{lot} | Ciclo {c['c1']}-{c['c2']}")

dados = DADOS.get(k, [[1,2,3]])
if 'a' not in st.session_state: st.session_state.a = {}

# MOSTRAR QUE É VERSÃO NOVA
st.success(f"✅ v67.8 carregada! Focus atual: **{focus}** ({fc*100:.0f}% faltantes)")

t1,t2,t3,t4 = st.tabs(["🔄 CICLO","📊 Resultados","🎯 Previsão","🤖 IA"])

with t1:
    st.header(f"Ciclo - {lot}")
    c1,c2,c3 = st.columns(3)
    with c1:
        ciclo = st.slider("Janela", c['c1'], c['c2'], (c['c1']+c['c2'])//2, key=f"s{k}")
        if st.button("ANALISAR", type="primary", key=f"b{k}", use_container_width=True):
            ult = dados[-min(ciclo,len(dados)):]
            todas = [n for j in ult for n in j]
            f = Counter(todas)
            st.session_state.a[k] = {'u':len(f),'f':[n for n in range(1,c['t']+1) if n not in f],'m':[n for n,v in f.items() if v>=2],'c':len(f)/c['t']*100}
            st.success(f"Analisado com Focus {focus}!")
    with c2:
        an = st.session_state.a.get(k,{})
        if an:
            st.metric("Cobertura", f"{an.get('u',0)}/{c['t']}", f"{an.get('c',0):.1f}%")
            st.progress(min(an.get('c',0)/100,1.0))
    with c3:
        an = st.session_state.a.get(k,{})
        if an:
            st.metric("Mantidas", len(an.get('m',[])))
            st.metric("Faltam", len(an.get('f',[])))

with t2:
    st.header("Resultados")
    df = pd.DataFrame(dados[-10:][::-1])
    if not df.empty:
        df.columns=[f'D{i+1}' for i in range(len(df.columns))]
        st.dataframe(df, use_container_width=True)

with t3:
    st.header(f"Previsão - Focus {focus}")
    an = st.session_state.a.get(k,{})
    st.info(f"Usando {fc*100:.0f}% de dezenas faltantes (Focus {focus})")
    if an and an.get('m'):
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("Jogo 1")
            n_f = int(c['s'] * fc)
            base = an.get('f',[])[:n_f] + an.get('m',[])[:c['s']-n_f]
            while len(base) < c['s']: base.append(random.randint(1,c['t']))
            j = sorted(list(dict.fromkeys(base))[:c['s']])
            st.code(" ".join(f"{n:02d}" for n in j))
            st.caption(f"{n_f} faltantes + {c['s']-n_f} mantidas")
        with c2:
            st.subheader("Jogo 2")
            j2 = sorted(random.sample(range(1,c['t']+1), c['s']))
            st.code(" ".join(f"{n:02d}" for n in j2))
    else:
        st.warning("Analise primeiro")

with t4:
    st.header(f"IA - Focus {focus}")
    for i,n in enumerate(["Fechamento","Manutenção","Virada"]):
        if st.button(n, key=f"ia{k}{i}", use_container_width=True):
            j = sorted(random.sample(range(1,c['t']+1), c['s']))
            st.success(" ".join(f"{n:02d}" for n in j) + f" | Focus {focus}")

st.sidebar.divider()
st.sidebar.warning(f"v67.8 • {focus}")
