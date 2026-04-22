
import streamlit as st
import pandas as pd
import numpy as np
import random
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt

st.set_page_config(page_title="LOTOELITE V91 TURBO", layout="wide", page_icon="🚀")
st.markdown('<h1 style="text-align:center;color:#d32f2f">🚀 LOTOELITE V91 TURBO - ETAPA 1</h1>', unsafe_allow_html=True)

LOTERIAS = {
    "Lotofácil":{"max":25,"qtd":15,"preco":3.0,"api":"lotofacil"},
    "Mega-Sena":{"max":60,"qtd":6,"preco":5.0,"api":"megasena"},
    "Quina":{"max":80,"qtd":5,"preco":2.5,"api":"quina"},
    "Lotomania":{"max":100,"qtd":50,"preco":3.0,"api":"lotomania"},
    "Timemania":{"max":80,"qtd":10,"preco":3.5,"api":"timemania"},
}
lot = st.sidebar.selectbox("Loteria", list(LOTERIAS.keys()))
cfg = LOTERIAS[lot]
fase = ["INÍCIO","MEIO","FIM"][datetime.now().day % 3]

# CACHE 50 CONCURSOS
@st.cache_data(ttl=3600, show_spinner="Carregando 50 concursos em paralelo...")
def carrega_50(api):
    try:
        latest = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api}/latest", timeout=10).json()
        ultimo = int(latest.get("concurso", 2800))
        concursos = list(range(max(1, ultimo-49), ultimo+1))
        
        def fetch(c):
            try:
                r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api}/{c}", timeout=5).json()
                return {"concurso":c,"data":r.get("data"),"dezenas":[int(d) for d in r.get("dezenas",[])],}
            except: return None
        
        resultados=[]
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(fetch,c):c for c in concursos}
            for f in as_completed(futures):
                res = f.result()
                if res: resultados.append(res)
        return sorted(resultados, key=lambda x: x["concurso"], reverse=True)
    except Exception as e:
        st.error(f"Erro API: {e}")
        return []

dados = carrega_50(cfg["api"])
st.sidebar.success(f"✅ {len(dados)} concursos carregados em paralelo")

# CALCULA FREQUENCIAS
todos_nums = list(range(1, cfg["max"]+1))
freq = {n:0 for n in todos_nums}
ultima_aparicao = {n:999 for n in todos_nums}

for idx, conc in enumerate(dados):
    for n in conc["dezenas"]:
        freq[n]+=1
        if ultima_aparicao[n]==999: ultima_aparicao[n]=idx

# CLASSIFICA QUENTES/FRIOS
sorted_freq = sorted(freq.items(), key=lambda x:-x[1])
qtd_terco = max(1, len(todos_nums)//3)
quentes = [n for n,_ in sorted_freq[:qtd_terco]]
frios = [n for n,_ in sorted_freq[-qtd_terco:]]
neutros = [n for n in todos_nums if n not in quentes+frios]

def render_color(nums):
    html=""
    for n in sorted(nums):
        if n in quentes: cor="#4caf50"; emoji="🟢"
        elif n in frios: cor="#2196f3"; emoji="🔵"
        else: cor="#9e9e9e"; emoji="⚫"
        html+=f'<span style="background:{cor};color:white;padding:6px 10px;border-radius:50%;margin:2px;display:inline-block;min-width:36px;text-align:center;font-weight:bold" title="{emoji}">{n:02d}</span>'
    return html

tabs = st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔢 FECHAMENTO","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA AVANÇADA","💡 DICAS","🎯 DNA","📊 RESULTADOS","🔬 BACKTEST","💰 PREÇOS","🔴 AO VIVO","🎯 ESPECIAIS"])

# 1 GERADOR
with tabs[0]:
    st.subheader(f"Gerador - {lot} | Fase {fase}")
    def gerar(tipo):
        if tipo=="Conservador": base=quentes+neutros[:5]
        elif tipo=="Agressivo": base=frios+neutros[:5]
        else: base=quentes[:8]+frios[:8]+neutros
        return sorted(random.sample(list(set(base)), cfg["qtd"]))
    if st.button("Gerar 3 jogos"):
        for t in ["Conservador","Equilibrado","Agressivo"]:
            st.markdown(f"**{t}:** {render_color(gerar(t))}")

# 2 MEUS JOGOS
with tabs[1]:
    st.info("Histórico salvo na sessão")

# 3 FECHAMENTO
with tabs[2]:
    st.subheader("Fechamento inteligente")
    txt=st.text_input("Dezenas base", " ".join(str(x) for x in quentes[:18]))
    if st.button("Gerar"):
        base=[int(x) for x in txt.split() if x.isdigit()]
        for i in range(8): st.code(f"{i+1}: {' '.join(f'{x:02d}' for x in sorted(random.sample(base,cfg['qtd'])))}")

# 4 CICLO
with tabs[3]:
    st.metric("Fase atual", fase)
    st.write(f"Quentes ({len(quentes)}): {render_color(quentes[:10])}", unsafe_allow_html=True)
    st.write(f"Frios ({len(frios)}): {render_color(frios[:10])}", unsafe_allow_html=True)

# 5 ESTATÍSTICAS
with tabs[4]:
    st.subheader("Frequência acumulada - últimos 50")
    df_freq=pd.DataFrame([{"Dezena":n,"Freq":freq[n],"Atraso":ultima_aparicao[n]} for n in todos_nums]).sort_values("Freq",ascending=False)
    col1,col2=st.columns(2)
    with col1:
        st.write("**Top 10 mais frequentes**")
        st.dataframe(df_freq.head(10), hide_index=True)
    with col2:
        st.write("**Top 10 menos frequentes**")
        st.dataframe(df_freq.tail(10), hide_index=True)
    st.bar_chart(df_freq.set_index("Dezena")["Freq"])

# 6 IA AVANÇADA
with tabs[5]:
    st.warning("🧠 XGBoost + LSTM + Genético — em desenvolvimento na Etapa 2")
    st.json({"dados_carregados":len(dados),"quentes":len(quentes),"pronto_para_treino":True})

# 7 DICAS
with tabs[6]:
    st.subheader("Guia de Ciclos")
    dicas = {
        "Lotofácil":"Janela 4-6 concursos. INÍCIO: priorize quentes. FIM: priorize frios.",
        "Mega-Sena":"Janela 7-17. Use fechamentos.",
        "Quina":"Janela 15-30. Alta variância."
    }
    st.info(dicas.get(lot,"Siga a fase do ciclo"))

# 8 DNA
with tabs[7]:
    st.subheader("DNA das Dezenas")
    def is_primo(n): return n>1 and all(n%i for i in range(2,int(n**0.5)+1))
    dna=[]
    for n in todos_nums:
        dna.append({
            "Dezena":n,
            "Freq":freq[n],
            "Atraso":ultima_aparicao[n],
            "Paridade":"Par" if n%2==0 else "Ímpar",
            "Primo":"Sim" if is_primo(n) else "Não",
            "Categoria":"🟢 Quente" if n in quentes else "🔵 Frio" if n in frios else "⚫ Neutro"
        })
    st.dataframe(pd.DataFrame(dna), hide_index=True, height=400)

# 9 RESULTADOS
with tabs[8]:
    st.subheader(f"Últimos {min(20,len(dados))} concursos")
    for conc in dados[:20]:
        st.markdown(f"**{conc['concurso']} - {conc['data']}**: {render_color(conc['dezenas'])}", unsafe_allow_html=True)

# 10 BACKTEST
with tabs[9]:
    st.warning("Backtest XGBoost — disponível na Etapa 2")

# 11 PREÇOS
with tabs[10]:
    st.dataframe(pd.DataFrame([{"Loteria":k,"Preço":f"R$ {v['preco']:.2f}"} for k,v in LOTERIAS.items()]), hide_index=True)

# 12 AO VIVO
with tabs[11]:
    if dados:
        ult=dados[0]
        st.success(f"Concurso {ult['concurso']} - {ult['data']}")
        st.markdown(render_color(ult["dezenas"]), unsafe_allow_html=True)
        st.metric("Prêmio acumulado","Em breve")

# 13 ESPECIAIS
with tabs[12]:
    st.subheader("Loterias Especiais")
    for nome in ["Mega da Virada","Quina São João","Lotofácil Independência"]:
        st.write(f"**{nome}**")
