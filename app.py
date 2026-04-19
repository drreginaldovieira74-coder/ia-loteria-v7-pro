import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")
st.markdown("<h1 style='text-align:center;color:#d32f2f;font-size:3.2rem;font-weight:900'>🎯 LOTOELITE</h1>", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico=[]
if 'qtd_fech' not in st.session_state: st.session_state.qtd_fech=21

configs={"Lotofácil":{"max":25,"qtd":15},"Mega-Sena":{"max":60,"qtd":6},"Quina":{"max":80,"qtd":5},"Dupla Sena":{"max":50,"qtd":6},"Timemania":{"max":80,"qtd":10},"Lotomania":{"max":100,"qtd":50},"Dia de Sorte":{"max":31,"qtd":7},"Super Sete":{"max":9,"qtd":7},"+Milionária":{"max":50,"qtd":6}}
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

def analisar_ciclo(draws, maxn):
    freq={i:0 for i in range(1,maxn+1)}
    atraso={i:99 for i in range(1,maxn+1)}
    for idx,d in enumerate(draws[:30]):
        for n in d["dezenas"]:
            freq[n]+=1
            if atraso[n]==99: atraso[n]=idx
    quentes=sorted(freq,key=freq.get,reverse=True)[:max(5,int(maxn*0.35))]
    frios=sorted(freq,key=freq.get)[:max(5,int(maxn*0.30))]
    neutros=[n for n in range(1,maxn+1) if n not in quentes and n not in frios]
    seen=set(); ciclo=0
    for d in draws:
        seen.update(d["dezenas"]); ciclo+=1
        if len(seen)>=maxn: break
    fase="Início" if ciclo<=4 else "Meio" if ciclo<=8 else "Fim"
    return {"quentes":quentes,"frios":frios,"neutros":neutros,"atraso":atraso,"fase":fase,"ciclo":ciclo,"freq":freq}

def valida_jogo(jogo, lot):
    jogo=sorted(jogo)
    if lot=="Mega-Sena":
        baixo=len([n for n in jogo if n<=20]); meio=len([n for n in jogo if 21<=n<=40]); alto=len([n for n in jogo if n>40])
        return baixo>=1 and meio>=1 and alto>=1
    if lot=="Quina":
        baixo=len([n for n in jogo if n<=26]); meio=len([n for n in jogo if 27<=n<=53]); alto=len([n for n in jogo if n>53])
        return baixo>=1 and alto>=1
    if lot=="Lotofácil":
        pares=len([n for n in jogo if n%2==0]); return 6<=pares<=9
    if lot=="Dupla Sena":
        return len([n for n in jogo if n<=25])>=2
    return True

def gerar_por_estrategia(lot, analise, estrategia):
    q=configs[lot]["qtd"]; maxn=configs[lot]["max"]
    quentes=analise["quentes"]; frios=analise["frios"]; neutros=analise["neutros"]; atraso=analise["atraso"]
    if estrategia=="conservador":
        pool=quentes[:int(len(quentes)*0.7)] + neutros[:int(len(neutros)*0.5)]
    elif estrategia=="equilibrado":
        pool=quentes[:int(len(quentes)*0.5)] + neutros[:int(len(neutros)*0.6)] + frios[:int(len(frios)*0.4)]
    else:
        atrasados=sorted(atraso,key=atraso.get,reverse=True)[:int(maxn*0.3)]
        pool=atrasados + frios[:int(len(frios)*0.6)] + quentes[:int(len(quentes)*0.3)]
    pool=list(dict.fromkeys(pool))
    if len(pool)<q: pool=list(range(1,maxn+1))
    for _ in range(200):
        jogo=sorted(random.sample(pool, min(q,len(pool))))
        while len(jogo)<q:
            n=random.randint(1,maxn)
            if n not in jogo: jogo.append(n)
        jogo=sorted(jogo[:q])
        if valida_jogo(jogo, lot): return jogo
    return sorted(random.sample(range(1,maxn+1),q))

with st.sidebar:
    lot=st.selectbox("Loteria",list(configs.keys()))
    dados=busca(lot)
    if dados["ok"]: st.success("🟢 ONLINE")
    else: st.warning("🟡 OFFLINE")
    maxn=configs[lot]["max"]
    analise=analisar_ciclo(dados["draws"], maxn) if dados["draws"] else None

tabs=st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔢 FECHAMENTO","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","📊 RESULTADOS","🔬 BACKTEST","💰 PREÇOS","🔴 AO VIVO","🎯 ESPECIAIS"])

with tabs[0]:
    st.subheader("Gerador Inteligente v88")
    if analise:
        st.info(f"Ciclo automático: {analise['fase']} - {analise['ciclo']} concursos | Quentes: {len(analise['quentes'])} | Frios: {len(analise['frios'])}")
    if st.button("GERAR 3 JOGOS INTELIGENTES",type="primary",use_container_width=True):
        if analise:
            for nome,est in [("Conservador","conservador"),("Equilibrado","equilibrado"),("Agressivo","agressivo")]:
                j=gerar_por_estrategia(lot, analise, est); st.session_state.historico.append({"j":j})
                st.success(f"{nome.upper()}: {' - '.join(f'{n:02d}' for n in j)}")
        else: st.warning("Sem dados")

with tabs[2]:
    st.subheader("FECHAMENTO - baseado no ciclo")
    c1,c2=st.columns(2)
    if c1.button("➕"): st.session_state.qtd_fech+=1
    if c2.button("➖"): st.session_state.qtd_fech=max(1,st.session_state.qtd_fech-1)
    st.metric("Quantidade",st.session_state.qtd_fech)
    if st.button("GERAR FECHAMENTO INTELIGENTE"):
        if analise:
            pool=list(dict.fromkeys(analise["quentes"][:12] + analise["neutros"][:8] + analise["frios"][:5]))
            q=configs[lot]["qtd"]
            for i in range(st.session_state.qtd_fech):
                for _ in range(100):
                    j=sorted(random.sample(pool, min(q,len(pool))))
                    if valida_jogo(j, lot): break
                st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in j)}")
        else: st.warning("Sem dados")

with tabs[3]:
    st.subheader("CICLO - análise automática")
    if st.button("🔄 Atualizar Ciclo"): st.rerun()
    if analise:
        df=pd.DataFrame([{"Concurso":d["concurso"],"Qtd":len(d["dezenas"])} for d in dados["draws"][:12]])
        st.bar_chart(df.set_index("Concurso"))
        c1,c2,c3=st.columns(3)
        with c1: st.markdown("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in sorted(analise["quentes"])))
        with c2: st.markdown("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in sorted(analise["frios"])))
        with c3: st.markdown("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in sorted(analise["neutros"][:30])))

with tabs[5]:
    st.subheader("IA v88 - 3 estratégias")
    if st.button("Gerar IA completa"):
        if analise:
            for est in ["conservador","equilibrado","agressivo"]:
                j=gerar_por_estrategia(lot, analise, est)
                st.success(f"{est.title()}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[6]:
    st.subheader("DICAS")
    st.success("Dica 1: Equilibre pares e ímpares")
    st.info("Dica 2: Use ciclo - Início=frios, Fim=quentes")
    st.warning("Dica 3: Sempre cubra 3 faixas de números")

with tabs[10]:
    tabela=[{"Loteria":"Lotofácil","Mínimo":"R$ 3,50","Máximo":"R$ 46.512"},{"Loteria":"Mega-Sena","Mínimo":"R$ 6,00","Máximo":"R$ 232.560"},{"Loteria":"Quina","Mínimo":"R$ 3,00","Máximo":"R$ 9.009"},{"Loteria":"Dupla Sena","Mínimo":"R$ 3,00","Máximo":"R$ 15.015"},{"Loteria":"Timemania","Mínimo":"R$ 3,50","Máximo":"R$ 3,50"},{"Loteria":"Lotomania","Mínimo":"R$ 3,00","Máximo":"R$ 3,00"},{"Loteria":"Dia de Sorte","Mínimo":"R$ 2,50","Máximo":"R$ 8.037,50"},{"Loteria":"Super Sete","Mínimo":"R$ 3,00","Máximo":"R$ 26.460"},{"Loteria":"+Milionária","Mínimo":"R$ 6,00","Máximo":"R$ 83.160"}]
    st.dataframe(pd.DataFrame(tabela),hide_index=True,use_container_width=True)

with tabs[11]:
    vivos=[{"Loteria":"Mega-Sena","C":2998,"P":"R$ 60.000.000"},{"Loteria":"Quina","C":7004,"P":"R$ 20.000.000"},{"Loteria":"+Milionária","C":347,"P":"R$ 36.000.000"},{"Loteria":"Lotofácil","C":3664,"P":"R$ 2.000.000"},{"Loteria":"Dupla Sena","C":2946,"P":"R$ 1.200.000"},{"Loteria":"Timemania","C":2180,"P":"R$ 3.200.000"},{"Loteria":"Lotomania","C":2750,"P":"R$ 1.800.000"},{"Loteria":"Dia de Sorte","C":1025,"P":"R$ 800.000"},{"Loteria":"Super Sete","C":836,"P":"R$ 6.300.000"}]
    for v in vivos: st.error(f"🔥 {v['Loteria']} {v['C']} - {v['P']}")

with tabs[12]:
    st.subheader("ESPECIAIS - 3 jogos cada")
    for nome,total,qtd in [("Mega da Virada",60,6),("Quina São João",80,5),("Lotofácil Independência",25,15),("Dupla de Páscoa",50,6),("+Milionária Especial",50,6)]:
        st.markdown(f"**{nome}**")
        if st.button(f"Gerar {nome}",key=nome):
            for tipo in ["Conservador","Equilibrado","Agressivo"]:
                jogo=sorted(random.sample(range(1,total+1),qtd))
                st.success(f"{tipo}: {' - '.join(f'{n:02d}' for n in jogo)}")

with tabs[1]: st.write(f"Total jogos: {len(st.session_state.historico)}")
with tabs[4]: st.write("Estatísticas via ciclo")
with tabs[7]: st.write("DNA ativo")
with tabs[8]:
    if dados["draws"]:
        for d in dados["draws"][:5]: st.code(f"{d['concurso']}: {'-'.join(f'{int(x):02d}' for x in d['dezenas'])}")
with tabs[9]: st.write("Backtest")
