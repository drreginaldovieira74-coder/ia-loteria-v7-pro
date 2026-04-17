import streamlit as st
import pandas as pd
import random, requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v86.4", layout="wide", page_icon="🎯")
st.markdown("<h1 style='text-align:center;color:#d32f2f;font-size:3rem;font-weight:900'>🎯 LOTOELITE v86.4</h1>", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico=[]
if 'qtd_fech' not in st.session_state: st.session_state.qtd_fech=21

configs={"Lotofácil":{"max":25,"qtd":15},"Mega-Sena":{"max":60,"qtd":6},"Quina":{"max":80,"qtd":5},"Dupla Sena":{"max":50,"qtd":6},"Timemania":{"max":80,"qtd":10},"Lotomania":{"max":100,"qtd":50},"Dia de Sorte":{"max":31,"qtd":7},"Super Sete":{"max":9,"qtd":7},"+Milionária":{"max":50,"qtd":6}}
DNAS={"Lotofácil":[4,6,10,14,17,19,20,24,25],"Mega-Sena":[14,32,37,39,42,43],"Quina":[4,10,14,19,20,25,32,37],"Dupla Sena":[14,19,25,32,37,42]}
API={"Lotofácil":"lotofacil","Mega-Sena":"megasena","Quina":"quina","Dupla Sena":"duplasena","Timemania":"timemania","Lotomania":"lotomania","Dia de Sorte":"diadesorte","Super Sete":"supersete","+Milionária":"maismilionaria"}

def busca(lot):
    try:
        base=f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{API[lot]}"
        r=requests.get(base,timeout=7).json()
        draws=[]
        for i in range(r.get("numero",0), max(r.get("numero",0)-30,0), -1):
            try:
                d=requests.get(f"{base}/{i}",timeout=4).json()
                draws.append({"concurso":i,"dezenas":[int(x) for x in d.get("listaDezenas",[])], "data":d.get("dataApuracao"),"acum":d.get("acumulado",True)})
            except: pass
        return {"ok":True,"latest":r,"draws":draws}
    except:
        return {"ok":False,"draws":[]}

with st.sidebar:
    st.markdown("### v86.4 COMPLETO")
    lot=st.selectbox("Loteria",list(configs.keys()))
    focus=st.slider("Focus %",0,100,40,5)
    dados=busca(lot)
    st.success("🟢 ONLINE") if dados["ok"] else st.warning("🟡 OFFLINE - backup")

def gerar(f=focus):
    q=configs[lot]["qtd"]; maxn=configs[lot]["max"]; jogo=[]; dna=DNAS.get(lot,[])
    nq=int(q*f/100)
    for n in dna[:nq]:
        if n<=maxn and n not in jogo: jogo.append(n)
    pool=list(range(1,maxn+1)); random.shuffle(pool)
    for n in pool:
        if len(jogo)>=q: break
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:q])

tabs=st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","📊 RESULTADOS","📚 HISTÓRICO","🔬 BACKTEST","💰 PREÇOS","📤 EXPORTAR","🔴 AO VIVO","🎯 ESPECIAIS","🔢 FECHAMENTO"])

with tabs[0]:
    c1,c2=st.columns([3,1])
    with c1:
        if st.button("🎲 GERAR 3 JOGOS",type="primary",use_container_width=True):
            for i in range(3):
                j=gerar(); st.session_state.historico.append({"data":datetime.now().strftime("%d/%m %H:%M"),"lot":lot,"j":j})
                st.success(f"**JOGO {i+1}:** {' - '.join(f'{n:02d}' for n in j)}")
    with c2:
        if dados["ok"]: st.metric("Último",dados["latest"].get("numero"))

with tabs[1]:
    st.subheader("Meus Jogos"); 
    for h in reversed(st.session_state.historico[-15:]):
        st.code(f"{h['data']} - {h['lot']}: {'-'.join(f'{n:02d}' for n in h['j'])}")

with tabs[2]:
    st.subheader("CICLO - Restaurado")
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
        st.info(f"**Fase: {fase}** - {ciclo} concursos")
        df=pd.DataFrame([{"Concurso":d["concurso"],"Dezenas":len(d["dezenas"])} for d in dados["draws"][:12]])
        st.bar_chart(df.set_index("Concurso"))
        c1,c2,c3=st.columns(3)
        with c1: st.write("🔥 QUENTES"); st.write(", ".join(f"{n:02d}" for n in sorted(quentes)[:12]))
        with c2: st.write("❄️ FRIOS"); st.write(", ".join(f"{n:02d}" for n in sorted(frios)[:12]))
        with c3: st.write("➖ NEUTROS"); neutros=[n for n in range(1,maxn+1) if n not in quentes and n not in frios]; st.write(", ".join(f"{n:02d}" for n in sorted(neutros)[:12]))

with tabs[3]:
    st.subheader("ESTATÍSTICAS")
    if dados["draws"]:
        maxn=configs[lot]["max"]; freq={i:0 for i in range(1,maxn+1)}; atraso={i:0 for i in range(1,maxn+1)}
        for d in dados["draws"]: 
            for n in d["dezenas"]: freq[n]+=1
        for n in range(1,maxn+1):
            a=0
            for d in dados["draws"]:
                if n in d["dezenas"]: break
                a+=1
            atraso[n]=a
        df=pd.DataFrame([{"Dezena":n,"Freq":freq[n],"Atraso":atraso[n]} for n in range(1,maxn+1)]).sort_values("Freq",ascending=False)
        st.dataframe(df.head(20),hide_index=True,use_container_width=True)

with tabs[4]:
    st.subheader("IA - 3 jogos prontos pelo ciclo")
    if st.button("Gerar 3 estratégias IA"):
        for nome,pct in [("Conservador (30%)",30),("Equilibrado (50%)",50),("Agressivo (75%)",75)]:
            j=gerar(pct); st.success(f"**{nome}:** {' - '.join(f'{n:02d}' for n in j)}")

with tabs[5]:
    st.subheader("DICAS")
    ciclo=5
    if dados["draws"]:
        maxn=configs[lot]["max"]; seen=set(); ciclo=0
        for d in dados["draws"]:
            seen.update(d["dezenas"]); ciclo+=1
            if len(seen)>=maxn: break
    if ciclo<=4: st.success("INÍCIO DE CICLO: Use Focus 25-35%, priorize números frios, jogue 2-3 cartões")
    elif ciclo<=8: st.info("MEIO DE CICLO: Use Focus 45-55%, misture quentes e frios")
    else: st.warning("FIM DE CICLO: Use Focus 70-80%, priorize quentes, aumente para 5 jogos")

with tabs[6]:
    st.subheader("DNA")
    dna=DNAS.get(lot,[]); st.write("Dezenas DNA:", ", ".join(f"{n:02d}" for n in dna))
    st.caption("Baseado nos padrões históricos da loteria")

with tabs[7]:
    st.subheader("RESULTADOS")
    if dados["draws"]:
        for d in dados["draws"][:5]:
            dezenas=" - ".join(f"{int(x):02d}" for x in d["dezenas"])
            st.code(f"Concurso {d['concurso']} ({d['data']}): {dezenas}")
    else:
        # backup com valores do usuário
        backup={"Mega-Sena":{"n":2998,"d":"17/04/2026","dez":[14,32,37,39,42,43]},"Quina":{"n":7004,"d":"17/04/2026","dez":[4,10,14,19,25]}," +Milionária":{"n":347,"d":"17/04/2026","dez":[12,24,33,36,41,48]}}
        if lot in backup:
            b=backup[lot]; st.code(f"Concurso {b['n']} ({b['d']}): {' - '.join(f'{x:02d}' for x in b['dez'])}")

with tabs[8]:
    st.subheader("HISTÓRICO"); st.write(f"{len(st.session_state.historico)} jogos gerados")

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
        {"Loteria":"Lotofácil","Mín":"15 nº - R$ 3,50","Máx":"20 nº - R$ 46.512,00"},
        {"Loteria":"Mega-Sena","Mín":"6 nº - R$ 6,00","Máx":"20 nº - R$ 232.560,00"},
        {"Loteria":"Quina","Mín":"5 nº - R$ 3,00","Máx":"15 nº - R$ 9.009,00"},
        {"Loteria":"Dupla Sena","Mín":"6 nº - R$ 3,00","Máx":"15 nº - R$ 15.015,00"},
        {"Loteria":"Timemania","Mín":"10 nº - R$ 3,50","Máx":"10 nº - R$ 3,50"},
        {"Loteria":"Lotomania","Mín":"50 nº - R$ 3,00","Máx":"50 nº - R$ 3,00"},
        {"Loteria":"Dia de Sorte","Mín":"7 nº - R$ 2,50","Máx":"15 nº - R$ 8.037,50"},
        {"Loteria":"Super Sete","Mín":"R$ 3,00","Máx":"R$ 26.460,00"},
        {"Loteria":"+Milionária","Mín":"6+2 - R$ 6,00","Máx":"12+6 - R$ 83.160,00"},
    ]
    st.dataframe(pd.DataFrame(tabela),hide_index=True,use_container_width=True)

with tabs[11]:
    st.subheader("EXPORTAR"); 
    if st.session_state.historico:
        df=pd.DataFrame(st.session_state.historico); st.download_button("Baixar CSV",df.to_csv(index=False).encode(),"jogos.csv")

with tabs[12]:
    st.subheader("AO VIVO")
    # valores confirmados pelo usuário
    vivos=[
        {"Loteria":"Mega-Sena","Concurso":2998,"Prêmio":"R$ 60.000.000,00","Acum":"SIM"},
        {"Loteria":"Quina","Concurso":7004,"Prêmio":"R$ 20.000.000,00","Acum":"SIM"},
        {"Loteria":"+Milionária","Concurso":347,"Prêmio":"R$ 36.000.000,00","Acum":"SIM"},
        {"Loteria":"Lotofácil","Concurso":3369,"Prêmio":"R$ 1.700.000,00","Acum":"NÃO"},
    ]
    for v in vivos:
        if v["Acum"]=="SIM": st.error(f"🔥 {v['Loteria']} {v['Concurso']} - {v['Prêmio']} - ACUMULOU")
        else: st.info(f"{v['Loteria']} {v['Concurso']} - {v['Prêmio']}")
    st.dataframe(pd.DataFrame(vivos),hide_index=True)

with tabs[13]:
    st.subheader("ESPECIAIS")
    c1,c2=st.columns(2)
    with c1:
        if st.button("Mega da Virada"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,61),6))))
        if st.button("Quina São João"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,81),5))))
        if st.button("Lotofácil Independência"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,26),15))))
    with c2:
        if st.button("Dupla de Páscoa"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,51),6))))
        if st.button("+Milionária Especial"): st.success(" - ".join(f"{n:02d}" for n in sorted(random.sample(range(1,51),6))))

with tabs[14]:
    st.subheader("FECHAMENTO")
    c1,c2=st.columns(2)
    if c1.button("➕"): st.session_state.qtd_fech+=1
    if c2.button("➖"): st.session_state.qtd_fech=max(1,st.session_state.qtd_fech-1)
    st.write(f"**{st.session_state.qtd_fech} jogos**")
    if st.button("GERAR FECHAMENTO"):
        for i in range(st.session_state.qtd_fech):
            st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in gerar())}")
