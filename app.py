import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v86.6", layout="wide", page_icon="🎯")
st.markdown("<h1 style='text-align:center;color:#d32f2f;font-size:3rem;font-weight:900'>🎯 LOTOELITE v86.6</h1>", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico=[]
if 'qtd_fech' not in st.session_state: st.session_state.qtd_fech=21

configs={"Lotofácil":{"max":25,"qtd":15},"Mega-Sena":{"max":60,"qtd":6},"Quina":{"max":80,"qtd":5},"Dupla Sena":{"max":50,"qtd":6},"Timemania":{"max":80,"qtd":10},"Lotomania":{"max":100,"qtd":50},"Dia de Sorte":{"max":31,"qtd":7},"Super Sete":{"max":9,"qtd":7},"+Milionária":{"max":50,"qtd":6}}
DNAS={"Lotofácil":[4,6,10,14,17,19,20,24,25],"Mega-Sena":[14,32,37,39,42,43],"Quina":[4,10,14,19,20,25,32,37]}
API={"Lotofácil":"lotofacil","Mega-Sena":"megasena","Quina":"quina","Dupla Sena":"duplasena","Timemania":"timemania","Lotomania":"lotomania","Dia de Sorte":"diadesorte","Super Sete":"supersete","+Milionária":"maismilionaria"}

def busca(lot):
    try:
        base=f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{API[lot]}"
        r=requests.get(base,timeout=6).json()
        draws=[]
        for i in range(r.get("numero",0), max(r.get("numero",0)-30,0), -1):
            try:
                d=requests.get(f"{base}/{i}",timeout=3).json()
                draws.append({"concurso":i,"dezenas":[int(x) for x in d.get("listaDezenas",[])], "data":d.get("dataApuracao")})
            except: pass
        return {"ok":True,"latest":r,"draws":draws}
    except: return {"ok":False,"draws":[]}

with st.sidebar:
    lot=st.selectbox("Loteria",list(configs.keys()))
    focus=st.slider("Focus %",0,100,40,5)
    dados=busca(lot)
    st.success("🟢 ONLINE") if dados["ok"] else st.warning("🟡 OFFLINE")

def gerar(f=focus):
    q=configs[lot]["qtd"]; maxn=configs[lot]["max"]; jogo=[]; dna=DNAS.get(lot,[])
    for n in dna[:int(q*f/100)]:
        if n<=maxn and n not in jogo: jogo.append(n)
    while len(jogo)<q:
        n=random.randint(1,maxn)
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:q])

tabs=st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔢 FECHAMENTO","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","📊 RESULTADOS","🔬 BACKTEST","💰 PREÇOS","🔴 AO VIVO","🎯 ESPECIAIS"])

with tabs[0]:
    if st.button("GERAR 3 JOGOS",type="primary",use_container_width=True):
        for i in range(3):
            j=gerar(); st.session_state.historico.append({"j":j})
            st.success(f"JOGO {i+1}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[2]:
    st.subheader("FECHAMENTO")
    c1,c2=st.columns(2)
    if c1.button("➕"): st.session_state.qtd_fech+=1
    if c2.button("➖"): st.session_state.qtd_fech=max(1,st.session_state.qtd_fech-1)
    st.metric("Jogos",st.session_state.qtd_fech)
    if st.button("GERAR"):
        for i in range(st.session_state.qtd_fech):
            st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in gerar())}")

with tabs[3]:
    st.subheader("CICLO - Quentes, Frios e Neutros")
    if dados["draws"]:
        maxn=configs[lot]["max"]; freq={i:0 for i in range(1,maxn+1)}
        for d in dados["draws"][:20]:
            for n in d["dezenas"]: freq[n]+=1
        quentes=sorted(freq,key=freq.get,reverse=True)[:int(maxn*0.35)]
        frios=sorted(freq,key=freq.get)[:int(maxn*0.30)]
        neutros=[n for n in range(1,maxn+1) if n not in quentes and n not in frios]
        ciclo=0; seen=set()
        for d in dados["draws"]:
            seen.update(d["dezenas"]); ciclo+=1
            if len(seen)>=maxn: break
        fase="Início" if ciclo<=4 else "Meio" if ciclo<=8 else "Fim"
        st.info(f"Fase: {fase} - {ciclo} concursos")
        df=pd.DataFrame([{"Concurso":d["concurso"],"Qtd":len(d["dezenas"])} for d in dados["draws"][:12]])
        st.bar_chart(df.set_index("Concurso"))
        c1,c2,c3=st.columns(3)
        with c1: st.markdown("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in sorted(quentes)))
        with c2: st.markdown("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in sorted(frios)))
        with c3: st.markdown("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in sorted(neutros)))

with tabs[5]:
    st.subheader("IA - 3 jogos")
    if st.button("Gerar"):
        for nome,pct in [("Conservador",30),("Equilibrado",50),("Agressivo",75)]:
            j=gerar(pct); st.success(f"{nome}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[11]:
    st.subheader("AO VIVO")
    vivos=[{"Loteria":"Mega-Sena","C":2998,"P":"R$ 60.000.000,00"},{"Loteria":"Quina","C":7004,"P":"R$ 20.000.000,00"},{"Loteria":"+Milionária","C":347,"P":"R$ 36.000.000,00"},{"Loteria":"Lotofácil","C":3369,"P":"R$ 1.700.000,00"}]
    for v in vivos: st.error(f"🔥 {v['Loteria']} {v['C']} - {v['P']}")

with tabs[12]:
    st.subheader("ESPECIAIS - 5 loterias")
    c1,c2=st.columns(2)
    with c1:
        if st.button("Mega da Virada"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,61),6))))
        if st.button("Quina São João"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,81),5))))
        if st.button("Lotofácil Independência"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,26),15))))
    with c2:
        if st.button("Dupla de Páscoa"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,51),6))))
        if st.button("+Milionária Especial"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,51),6))))

# outras abas simplificadas
with tabs[1]: st.write(f"{len(st.session_state.historico)} jogos")
with tabs[4]: st.write("Estatísticas carregadas")
with tabs[6]: st.write("Dicas por fase")
with tabs[7]: st.write(", ".join(f"{n:02d}" for n in DNAS.get(lot,[])))
with tabs[8]: 
    if dados["draws"]:
        for d in dados["draws"][:5]: st.code(f"{d['concurso']}: {'-'.join(f'{int(x):02d}' for x in d['dezenas'])}")
with tabs[9]: st.write("Backtest disponível")
with tabs[10]:
    st.dataframe(pd.DataFrame([
        {"Loteria":"Lotofácil","Min":"R$ 3,50","Max":"R$ 46.512"},
        {"Loteria":"Mega-Sena","Min":"R$ 6,00","Max":"R$ 232.560"},
        {"Loteria":"Quina","Min":"R$ 3,00","Max":"R$ 9.009"},
    ]),hide_index=True)
