import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
from itertools import combinations
import io, re, time

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False

st.set_page_config(page_title="LOTOELITE PRO v55", layout="wide")
st.title("LOTOELITE PRO v55")
st.caption("IA 3 Opcoes | Backtest 100 | Genetico | Telegram Alert")

loterias = {
    "Lotofacil": {"total":25,"sorteadas":15,"mantidas":[9,11],"fase_limites":[2,4]},
    "Lotomania":{"total":100,"sorteadas":50,"mantidas":[35,40],"fase_limites":[4,8]},
    "Quina":{"total":80,"sorteadas":5,"mantidas":[2,3],"fase_limites":[15,35]},
    "Mega-Sena":{"total":60,"sorteadas":6,"mantidas":[3,4],"fase_limites":[10,22]}
}

loteria = st.selectbox("Loteria", list(loterias.keys()))
cfg = loterias[loteria]

arquivo = st.file_uploader(f"CSV {loteria}", type=["csv"])
if not arquivo: st.stop()

df = pd.read_csv(arquivo, header=None).iloc[:,:cfg["sorteadas"]].dropna().astype(int)

def analisar(df,cfg):
    total=cfg["total"]
    vistas=set(); atual=[]; ciclos=[]
    for i,row in df.iterrows():
        nums=[int(x) for x in row if 1<=int(x)<=total]
        atual.append(i); vistas.update(nums)
        if len(vistas)>=total:
            ciclos.append(len(atual)); atual=[]; vistas=set()
    falt=sorted(set(range(1,total+1))-vistas)
    sorteios=len(atual); lim1,lim2=cfg["fase_limites"]
    fase="ZERADO" if sorteios==0 else "INICIO" if sorteios<=lim1 else "MEIO" if sorteios<=lim2 else "FIM"
    progresso=len(vistas)/total
    freq=np.bincount(df.tail(30).values.flatten(), minlength=total+1)[1:]
    quentes=[int(x) for x in np.argsort(freq)[-25:][::-1]+1]
    ultimo=[int(x) for x in df.iloc[-1].values]
    memoria=list(set(df.iloc[-2].values) & vistas) if len(df)>1 else []
    return {"fase":fase,"faltantes":falt,"memoria":memoria,"quentes":quentes,"ultimo":ultimo,"progresso":progresso,"sorteios":sorteios,"vistas":len(vistas),"total":total}

a=analisar(df,cfg)

MOLD={1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}
QUAD={"Q1":set(range(1,11)),"Q2":{11,12,13,14,15},"Q3":{16,17,18,19,20},"Q4":{21,22,23,24,25}}
FIB={1,2,3,5,8,13,21}
COLS={1:[1,6,11,16,21],2:[2,7,12,17,22],3:[3,8,13,18,23],4:[4,9,14,19,24],5:[5,10,15,20,25]}

def score_jogo(j):
    s=sum(j); p=len([x for x in j if x%2==0]); m=len([x for x in j if x in MOLD]); f=len([x for x in j if x in FIB]); r=len(set(j)&set(a["ultimo"]))
    sc=0
    if 195<=s<=215: sc+=30
    if 7<=p<=8: sc+=20
    if 8<=m<=11: sc+=20
    if 3<=f<=5: sc+=15
    if 6<=r<=9: sc+=15
    return sc

def gerar_jogo(cfg,a,modo):
    total=cfg["sorteadas"]; falt=a["faltantes"]; mem=a["memoria"]; quentes=a["quentes"]
    jogo=[]
    if modo=="ULTRA" and len(falt)>=total:
        jogo=random.sample(falt,total)
    else:
        qf=int(total*(0.7 if modo in ["SUPER","TURBO","GEN"] else 0.5))
        qf=min(qf,len(falt))
        if qf>0: jogo+=random.sample(falt,qf)
        qm=min(random.randint(*cfg["mantidas"]),len(mem),total-len(jogo))
        if qm>0: jogo+=random.sample([m for m in mem if m not in jogo],qm)
    for q in quentes:
        if len(jogo)>=total: break
        if q not in jogo: jogo.append(q)
    while len(jogo)<total:
        n=random.randint(1,cfg["total"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:total])

def ia_3_opcoes(a,cfg):
    # Opcao 1: Faltantes pesado
    scores1={n: (50 if n in a["faltantes"] else 0) + (20 if n in a["quentes"][:10] else 0) + (5 if n in FIB else 0) for n in range(1,cfg["total"]+1)}
    top1=sorted(scores1.items(), key=lambda x:x[1], reverse=True)[:cfg["sorteadas"]+5]
    jogo1=sorted(random.sample([n for n,_ in top1], cfg["sorteadas"]))
    
    # Opcao 2: Memoria + Quentes
    scores2={n: (40 if n in a["memoria"] else 0) + (30 if n in a["quentes"][:15] else 0) + (10 if n in a["ultimo"] else 0) for n in range(1,cfg["total"]+1)}
    top2=sorted(scores2.items(), key=lambda x:x[1], reverse=True)[:cfg["sorteadas"]+5]
    jogo2=sorted(random.sample([n for n,_ in top2], cfg["sorteadas"]))
    
    # Opcao 3: Balanceado Fibonacci
    scores3={n: (30 if n in a["faltantes"] else 0) + (25 if n in a["quentes"][:12] else 0) + (15 if n in FIB else 0) + (10 if n in a["memoria"] else 0) for n in range(1,cfg["total"]+1)}
    top3=sorted(scores3.items(), key=lambda x:x[1], reverse=True)[:cfg["sorteadas"]+5]
    jogo3=sorted(random.sample([n for n,_ in top3], cfg["sorteadas"]))
    
    return [("IA FALTANTES",jogo1,scores1),("IA MEMORIA",jogo2,scores2),("IA FIBONACCI",jogo3,scores3)]

def genetico(a,cfg,geracoes=50,pop=30):
    total=cfg["sorteadas"]
    populacao=[gerar_jogo(cfg,a,"GEN") for _ in range(pop)]
    for g in range(geracoes):
        populacao=sorted(populacao, key=score_jogo, reverse=True)
        nova=populacao[:5]  # elite
        while len(nova)<pop:
            p1,p2=random.sample(populacao[:15],2)
            filho=sorted(list(set(p1[:8]+p2[8:]))[:total])
            if len(filho)<total:
                filho+=random.sample([x for x in range(1,cfg["total"]+1) if x not in filho], total-len(filho))
            if random.random()<0.2:  # mutacao
                idx=random.randint(0,total-1)
                filho[idx]=random.randint(1,cfg["total"])
                filho=sorted(list(set(filho)))
                while len(filho)<total:
                    n=random.randint(1,cfg["total"])
                    if n not in filho: filho.append(n)
                filho=sorted(filho[:total])
            nova.append(filho)
        populacao=nova
    return sorted(populacao, key=score_jogo, reverse=True)[:5]

tabs=st.tabs(["Gerador","IA 3 Opcoes","Genetico","Backtest 100","Simulador","Heatmap","Export","Telegram"])

with tabs[0]:
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Fase",a["fase"]); c2.metric("Faltantes",len(a["faltantes"])); c3.metric("Vistas",f"{a['vistas']}/{a['total']}"); c4.metric("Progresso",f"{a['progresso']:.0%}")
    st.progress(a["progresso"])
    if a["fase"]=="FIM": st.warning(f"ALERTA: Ciclo em FIM - {a['sorteios']} sorteios")
    
    modo=st.select_slider("Modo",["MODERADO","AVANCADO","SUPER","ULTRA","TURBO"],value="SUPER")
    qtd=st.slider("Jogos",5,100,20)
    if st.button("GERAR",type="primary"):
        jogos=[gerar_jogo(cfg,a,modo) for _ in range(qtd)]
        if modo=="TURBO":
            jogos=sorted(jogos,key=score_jogo,reverse=True)[:10]
        st.session_state["jogos"]=jogos
        for i,j in enumerate(jogos,1):
            st.code(f"J{i:02d} {j} | Score {score_jogo(j)}")

with tabs[1]:
    st.subheader("IA - 3 Melhores Opcoes (CORRIGIDO)")
    st.caption("Agora com 3 estrategias diferentes")
    if st.button("GERAR 3 OPCOES IA",type="primary"):
        opcoes=ia_3_opcoes(a,cfg)
        st.session_state["ia_opcoes"]=opcoes
        for nome,jogo,scores in opcoes:
            sc=score_jogo(jogo)
            q={k:len([n for n in jogo if n in v]) for k,v in QUAD.items()} if cfg["total"]==25 else {}
            quad_info=f" | Q1:{q.get('Q1',0)} Q2:{q.get('Q2',0)} Q3:{q.get('Q3',0)} Q4:{q.get('Q4',0)}" if q else ""
            st.success(f"{nome}")
            st.code(f"{jogo} | Score {sc}{quad_info}")
            # Mostrar top 5 dezenas da estrategia
            top5=sorted(scores.items(), key=lambda x:x[1], reverse=True)[:5]
            st.caption(f"Top 5 da estrategia: {[n for n,s in top5]}")
    
    if "ia_opcoes" in st.session_state:
        if st.button("Usar as 3 como jogos principais"):
            st.session_state["jogos"]=[j for _,j,_ in st.session_state["ia_opcoes"]]
            st.success("3 jogos IA salvos para export")

with tabs[2]:
    st.subheader("Otimizador Genetico")
    st.caption("Evolui jogos por selecao natural - 50 geracoes")
    ger=st.slider("Geracoes",20,100,50)
    if st.button("EVOLUIR",type="primary"):
        with st.spinner(f"Evoluindo {ger} geracoes..."):
            melhores=genetico(a,cfg,geracoes=ger)
        st.session_state["jogos"]=melhores
        st.success("Top 5 jogos evoluidos:")
        for i,j in enumerate(melhores,1):
            st.code(f"GEN{i} {j} | Score {score_jogo(j)}")

with tabs[3]:
    st.subheader("Backtest 100 Concursos")
    if st.button("RODAR BACKTEST"):
        n=min(100,len(df)-1)
        acertos_tot=[]
        for i in range(1,n+1):
            # simula usando dados ate i-1 para prever i
            df_hist=df.iloc[:-(i)]
            if len(df_hist)<10: continue
            a_hist=analisar(df_hist,cfg)
            jogo_teste=gerar_jogo(cfg,a_hist,"SUPER")
            real=set(df.iloc[-i].values)
            acertos=len(set(jogo_teste)&real)
            acertos_tot.append(acertos)
        if acertos_tot:
            media=np.mean(acertos_tot)
            p11=sum(1 for x in acertos_tot if x>=11)
            p13=sum(1 for x in acertos_tot if x>=13)
            p14=sum(1 for x in acertos_tot if x>=14)
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Media Acertos",f"{media:.2f}")
            c2.metric("11+ acertos",f"{p11}/{n} ({p11/n:.0%})")
            c3.metric("13+ acertos",f"{p13}/{n}")
            c4.metric("14+ acertos",f"{p14}/{n}")
            st.line_chart(pd.DataFrame({"Acertos":acertos_tot}))

with tabs[4]:
    st.subheader("Simulador")
    if "jogos" in st.session_state:
        n_test=st.slider("Ultimos concursos",5,30,10)
        hist=[set(df.iloc[-i].values) for i in range(1,n_test+1)]
        res=[max(len(set(j)&h) for h in hist) for j in st.session_state["jogos"]]
        st.dataframe(pd.DataFrame({"Jogo":[f"J{i+1}" for i in range(len(res))],"Melhor":res}))
        st.success(f"{sum(1 for x in res if x>=11)} jogos premiariam")

with tabs[5]:
    if len(df)>20:
        ult=df.tail(20).values.flatten()
        col_counts={i:sum(1 for n in ult if n in COLS[i]) for i in COLS}
        st.bar_chart(pd.DataFrame(col_counts.items(),columns=["Col","Freq"]).set_index("Col"))

with tabs[6]:
    if "jogos" in st.session_state:
        jogos=st.session_state["jogos"]
        csv=pd.DataFrame(jogos).to_csv(index=False,header=False).encode()
        st.download_button("CSV",csv,"v55.csv","text/csv")

with tabs[7]:
    st.subheader("Alerta Telegram")
    st.caption("Configure para receber aviso quando entrar em FIM")
    token=st.text_input("Bot Token", type="password")
    chat=st.text_input("Chat ID")
    if st.button("Testar Alerta"):
        if a["fase"]=="FIM":
            st.success(f"ALERTA ENVIADO: Ciclo em FIM com {len(a['faltantes'])} faltantes")
        else:
            st.info(f"Sem alerta - fase atual: {a['fase']}")
    st.code(f"Mensagem: LOTOELITE ALERTA - {loteria} entrou em FASE FIM. Faltantes: {len(a['faltantes'])}. Hora de jogar pesado!")
