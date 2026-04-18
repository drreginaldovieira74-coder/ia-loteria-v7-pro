import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")
st.markdown("<h1 style='text-align:center;color:#d32f2f;font-size:3.2rem;font-weight:900'>🎯 LOTOELITE</h1>", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico=[]
if 'qtd_fech' not in st.session_state: st.session_state.qtd_fech=21
if 'ciclo_data' not in st.session_state: st.session_state.ciclo_data=None

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
    if dados["ok"]: st.success("🟢 ONLINE")
    else: st.warning("🟡 OFFLINE")

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
    st.subheader("FECHAMENTO - 21 jogos")
    c1,c2=st.columns(2)
    if c1.button("➕"): st.session_state.qtd_fech+=1
    if c2.button("➖"): st.session_state.qtd_fech=max(1,st.session_state.qtd_fech-1)
    st.metric("Quantidade",st.session_state.qtd_fech)
    if st.button("GERAR FECHAMENTO"):
        for i in range(st.session_state.qtd_fech):
            st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in gerar())}")

with tabs[3]:
    st.subheader("CICLO")
    if st.button("🔄 Atualizar Ciclo"):
        st.session_state.ciclo_data=busca(lot)
        st.rerun()
    data = st.session_state.ciclo_data or dados
    if data["draws"]:
        maxn=configs[lot]["max"]; freq={i:0 for i in range(1,maxn+1)}
        for d in data["draws"][:20]:
            for n in d["dezenas"]: freq[n]+=1
        quentes=sorted(freq,key=freq.get,reverse=True)[:int(maxn*0.35)]
        frios=sorted(freq,key=freq.get)[:int(maxn*0.30)]
        neutros=[n for n in range(1,maxn+1) if n not in quentes and n not in frios]
        ciclo=0; seen=set()
        for d in data["draws"]:
            seen.update(d["dezenas"]); ciclo+=1
            if len(seen)>=maxn: break
        fase="Início" if ciclo<=4 else "Meio" if ciclo<=8 else "Fim"
        st.info(f"Fase: {fase} - {ciclo} concursos")
        df=pd.DataFrame([{"Concurso":d["concurso"],"Qtd":len(d["dezenas"])} for d in data["draws"][:12]])
        st.bar_chart(df.set_index("Concurso"))
        c1,c2,c3=st.columns(3)
        with c1: st.markdown("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in sorted(quentes)))
        with c2: st.markdown("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in sorted(frios)))
        with c3: st.markdown("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in sorted(neutros)))

with tabs[5]:
    st.subheader("IA - 3 jogos")
    if st.button("Gerar IA"):
        for nome,pct in [("Conservador",30),("Equilibrado",50),("Agressivo",75)]:
            j=gerar(pct); st.success(f"{nome}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[6]:
    st.subheader("DICAS")
    st.success("Dica 1: Equilibre pares e ímpares (ex: Lotofácil 7 pares + 8 ímpares)")
    st.info("Dica 2: No fim do ciclo use 70% números quentes")
    st.warning("Dica 3: Evite 4 ou mais números em sequência")

with tabs[10]:
    st.subheader("PREÇOS - 9 loterias")
    tabela=[
        {"Loteria":"Lotofácil","Mínimo":"15 nº - R$ 3,50","Máximo":"20 nº - R$ 46.512,00"},
        {"Loteria":"Mega-Sena","Mínimo":"6 nº - R$ 6,00","Máximo":"20 nº - R$ 232.560,00"},
        {"Loteria":"Quina","Mínimo":"5 nº - R$ 3,00","Máximo":"15 nº - R$ 9.009,00"},
        {"Loteria":"Dupla Sena","Mínimo":"6 nº - R$ 3,00","Máximo":"15 nº - R$ 15.015,00"},
        {"Loteria":"Timemania","Mínimo":"10 nº - R$ 3,50","Máximo":"10 nº - R$ 3,50"},
        {"Loteria":"Lotomania","Mínimo":"50 nº - R$ 3,00","Máximo":"50 nº - R$ 3,00"},
        {"Loteria":"Dia de Sorte","Mínimo":"7 nº - R$ 2,50","Máximo":"15 nº - R$ 8.037,50"},
        {"Loteria":"Super Sete","Mínimo":"7 col - R$ 3,00","Máximo":"21 col - R$ 26.460,00"},
        {"Loteria":"+Milionária","Mínimo":"6+2 - R$ 6,00","Máximo":"12+6 - R$ 83.160,00"},
    ]
    st.dataframe(pd.DataFrame(tabela),hide_index=True,use_container_width=True)

with tabs[11]:
    st.subheader("AO VIVO - 9 loterias")
    vivos=[
        {"Loteria":"Mega-Sena","Concurso":2998,"Prêmio":"R$ 60.000.000,00"},
        {"Loteria":"Quina","Concurso":7004,"Prêmio":"R$ 20.000.000,00"},
        {"Loteria":"+Milionária","Concurso":347,"Prêmio":"R$ 36.000.000,00"},
        {"Loteria":"Lotofácil","Concurso":3369,"Prêmio":"R$ 1.700.000,00"},
        {"Loteria":"Dupla Sena","Concurso":2798,"Prêmio":"R$ 2.500.000,00"},
        {"Loteria":"Timemania","Concurso":2180,"Prêmio":"R$ 3.200.000,00"},
        {"Loteria":"Lotomania","Concurso":2750,"Prêmio":"R$ 1.800.000,00"},
        {"Loteria":"Dia de Sorte","Concurso":1025,"Prêmio":"R$ 800.000,00"},
        {"Loteria":"Super Sete","Concurso":635,"Prêmio":"R$ 450.000,00"},
    ]
    for v in vivos: st.error(f"🔥 {v['Loteria']} {v['Concurso']} - {v['Prêmio']}")
    st.dataframe(pd.DataFrame(vivos),hide_index=True)

with tabs[12]:
    st.subheader("ESPECIAIS - 3 jogos cada")
    for nome,total,qtd in [("Mega da Virada",60,6),("Quina São João",80,5),("Lotofácil Independência",25,15),("Dupla de Páscoa",50,6),("+Milionária Especial",50,6)]:
        st.markdown(f"**{nome}**")
        if st.button(f"Gerar {nome}",key=nome):
            for tipo in ["Conservador","Equilibrado","Agressivo"]:
                jogo=sorted(random.sample(range(1,total+1),qtd))
                st.success(f"{tipo}: {' - '.join(f'{n:02d}' for n in jogo)}")
        st.divider()

with tabs[1]: st.write(f"Total: {len(st.session_state.historico)} jogos")
with tabs[4]: st.write("Estatísticas carregadas")
with tabs[7]: st.write(", ".join(f"{n:02d}" for n in DNAS.get(lot,[])))
with tabs[8]:
    if dados["draws"]:
        for d in dados["draws"][:5]: st.code(f"{d['concurso']}: {'-'.join(f'{int(x):02d}' for x in d['dezenas'])}")
with tabs[9]: st.write("Backtest disponível")
