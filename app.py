import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v86.5", layout="wide", page_icon="🎯")
st.markdown("<h1 style='text-align:center;color:#d32f2f;font-size:3rem;font-weight:900'>🎯 LOTOELITE v86.5</h1>", unsafe_allow_html=True)

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
        for i in range(r.get("numero",0), max(r.get("numero",0)-25,0), -1):
            try:
                d=requests.get(f"{base}/{i}",timeout=3).json()
                draws.append({"concurso":i,"dezenas":[int(x) for x in d.get("listaDezenas",[])], "data":d.get("dataApuracao")})
            except: pass
        return {"ok":True,"latest":r,"draws":draws}
    except: return {"ok":False,"draws":[]}

with st.sidebar:
    st.markdown("### v86.5 COMPLETO")
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

# 12 abas - FECHAMENTO na posição 3
tabs=st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔢 FECHAMENTO","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","📊 RESULTADOS","🔬 BACKTEST","💰 PREÇOS","🔴 AO VIVO"])

with tabs[0]:
    if st.button("🎲 GERAR 3 JOGOS",type="primary",use_container_width=True):
        for i in range(3):
            j=gerar(); st.session_state.historico.append({"data":datetime.now().strftime("%d/%m %H:%M"),"lot":lot,"j":j})
            st.success(f"JOGO {i+1}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[1]:
    st.subheader("Meus Jogos")
    for h in reversed(st.session_state.historico[-20:]):
        st.code(f"{h['data']} - {h['lot']}: {'-'.join(f'{n:02d}' for n in h['j'])}")

with tabs[2]:
    st.subheader("FECHAMENTO - 21 jogos (padrão)")
    c1,c2,c3=st.columns([1,1,3])
    with c1:
        if st.button("➕",use_container_width=True): st.session_state.qtd_fech+=1
    with c2:
        if st.button("➖",use_container_width=True): st.session_state.qtd_fech=max(1,st.session_state.qtd_fech-1)
    with c3:
        st.metric("Quantidade",st.session_state.qtd_fech)
    if st.button("GERAR FECHAMENTO",type="primary",use_container_width=True):
        for i in range(st.session_state.qtd_fech):
            st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in gerar())}")

with tabs[3]:
    st.subheader("CICLO")
    if dados["draws"]:
        maxn=configs[lot]["max"]; freq={i:0 for i in range(1,maxn+1)}
        for d in dados["draws"][:20]:
            for n in d["dezenas"]: freq[n]+=1
        quentes=sorted(freq,key=freq.get,reverse=True)[:int(maxn*0.3)]
        frios=sorted(freq,key=freq.get)[:int(maxn*0.3)]
        ciclo=0; seen=set()
        for d in dados["draws"]:
            seen.update(d["dezenas"]); ciclo+=1
            if len(seen)>=maxn: break
        fase="Início" if ciclo<=4 else "Meio" if ciclo<=8 else "Fim"
        st.info(f"Fase: {fase} - {ciclo} concursos")
        df=pd.DataFrame([{"Concurso":d["concurso"],"Qtd":len(d["dezenas"])} for d in dados["draws"][:12]])
        st.bar_chart(df.set_index("Concurso"))
        st.write("🔥 QUENTES:", ", ".join(f"{n:02d}" for n in sorted(quentes)[:15]))
        st.write("❄️ FRIOS:", ", ".join(f"{n:02d}" for n in sorted(frios)[:15]))

with tabs[4]:
    st.subheader("ESTATÍSTICAS")
    if dados["draws"]:
        maxn=configs[lot]["max"]; freq={i:0 for i in range(1,maxn+1)}
        for d in dados["draws"]: 
            for n in d["dezenas"]: freq[n]+=1
        df=pd.DataFrame([{"Dezena":n,"Freq":freq[n]} for n in range(1,maxn+1)]).sort_values("Freq",ascending=False)
        st.dataframe(df.head(25),hide_index=True,use_container_width=True)

with tabs[5]:
    st.subheader("IA - 3 jogos prontos pelo ciclo")
    if st.button("Gerar 3 estratégias"):
        for nome,pct in [("Conservador (30%)",30),("Equilibrado (50%)",50),("Agressivo (75%)",75)]:
            j=gerar(pct); st.success(f"{nome}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[6]:
    st.subheader("DICAS")
    ciclo=5
    if dados["draws"]:
        maxn=configs[lot]["max"]; seen=set(); ciclo=0
        for d in dados["draws"]:
            seen.update(d["dezenas"]); ciclo+=1
            if len(seen)>=maxn: break
    if ciclo<=4: st.success("INÍCIO: Focus 25-35%, priorize frios")
    elif ciclo<=8: st.info("MEIO: Focus 45-55%, equilibrado")
    else: st.warning("FIM: Focus 70-80%, priorize quentes")

with tabs[7]:
    st.subheader("DNA")
    dna=DNAS.get(lot,[]); st.write(", ".join(f"{n:02d}" for n in dna))

with tabs[8]:
    st.subheader("RESULTADOS")
    if dados["draws"]:
        for d in dados["draws"][:5]:
            dezenas=" - ".join(f"{int(x):02d}" for x in d["dezenas"])
            st.code(f"Concurso {d['concurso']}: {dezenas}")

with tabs[9]:
    st.subheader("BACKTEST")
    if dados["draws"] and st.session_state.historico:
        ultimo=st.session_state.historico[-1]["j"]
        res=[]
        for d in dados["draws"][:10]:
            ac=len(set(ultimo)&set(d["dezenas"])); res.append({"Concurso":d["concurso"],"Acertos":ac})
        st.dataframe(pd.DataFrame(res),hide_index=True)
    else: st.info("Gere um jogo primeiro")

with tabs[10]:
    st.subheader("PREÇOS - Mínimo e Máximo")
    tabela=[
        {"Loteria":"Lotofácil","Mínimo":"15 nº - R$ 3,50","Máximo":"20 nº - R$ 46.512,00"},
        {"Loteria":"Mega-Sena","Mínimo":"6 nº - R$ 6,00","Máximo":"20 nº - R$ 232.560,00"},
        {"Loteria":"Quina","Mínimo":"5 nº - R$ 3,00","Máximo":"15 nº - R$ 9.009,00"},
        {"Loteria":"Dupla Sena","Mínimo":"6 nº - R$ 3,00","Máximo":"15 nº - R$ 15.015,00"},
        {"Loteria":"Timemania","Mínimo":"R$ 3,50","Máximo":"R$ 3,50"},
        {"Loteria":"Lotomania","Mínimo":"R$ 3,00","Máximo":"R$ 3,00"},
        {"Loteria":"Dia de Sorte","Mínimo":"7 nº - R$ 2,50","Máximo":"15 nº - R$ 8.037,50"},
        {"Loteria":"Super Sete","Mínimo":"R$ 3,00","Máximo":"R$ 26.460,00"},
        {"Loteria":"+Milionária","Mínimo":"R$ 6,00","Máximo":"R$ 83.160,00"},
    ]
    st.dataframe(pd.DataFrame(tabela),hide_index=True,use_container_width=True)

with tabs[11]:
    st.subheader("AO VIVO")
    vivos=[
        {"Loteria":"Mega-Sena","Concurso":2998,"Prêmio":"R$ 60.000.000,00"},
        {"Loteria":"Quina","Concurso":7004,"Prêmio":"R$ 20.000.000,00"},
        {"Loteria":"+Milionária","Concurso":347,"Prêmio":"R$ 36.000.000,00"},
        {"Loteria":"Lotofácil","Concurso":3369,"Prêmio":"R$ 1.700.000,00"},
    ]
    for v in vivos:
        st.error(f"🔥 {v['Loteria']} {v['Concurso']} - {v['Prêmio']} - ACUMULOU")
    st.dataframe(pd.DataFrame(vivos),hide_index=True)

# Menu Mais na sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("🎯 Especiais"):
        st.session_state.show_esp=True
    if st.button("📤 Exportar CSV"):
        if st.session_state.historico:
            df=pd.DataFrame(st.session_state.historico); st.download_button("Baixar",df.to_csv(index=False).encode(),"jogos.csv")

if st.session_state.get("show_esp"):
    st.sidebar.success("Mega: "+"-".join(f"{n:02d}" for n in sorted(random.sample(range(1,61),6))))
