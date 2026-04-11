import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
from itertools import combinations
import io, re

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False

st.set_page_config(page_title="LOTOELITE PRO v56", layout="wide")
st.title("LOTOELITE PRO v56")
st.caption("CORRECAO Backtest + IA 3 Opcoes Fixas")

loterias = {
    "Lotofacil": {"total":25,"sorteadas":15,"mantidas":[9,11],"fase_limites":[2,4]},
    "Lotomania":{"total":100,"sorteadas":50,"mantidas":[35,40],"fase_limites":[4,8]},
    "Quina":{"total":80,"sorteadas":5,"mantidas":[2,3],"fase_limites":[15,35]},
    "Mega-Sena":{"total":60,"sorteadas":6,"mantidas":[3,4],"fase_limites":[10,22]}
}

loteria = st.selectbox("Loteria", list(loterias.keys()))
cfg = loterias[loteria]

arquivo = st.file_uploader(f"CSV {loteria} (com todos concursos)", type=["csv"])
ordem = st.radio("Ordem do CSV", ["Mais antigo no topo (correto)", "Mais recente no topo (inverter)"], horizontal=True)

if not arquivo: st.stop()

df_raw = pd.read_csv(arquivo, header=None).iloc[:,:cfg["sorteadas"]].dropna().astype(int)
df = df_raw.iloc[::-1].reset_index(drop=True) if "inverter" in ordem else df_raw

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

def score_jogo(j):
    s=sum(j); p=len([x for x in j if x%2==0]); m=len([x for x in j if x in MOLD]); f=len([x for x in j if x in FIB]); r=len(set(j)&set(a["ultimo"]))
    sc=0
    if 195<=s<=215: sc+=30
    if 7<=p<=8: sc+=20
    if 8<=m<=11: sc+=20
    if 3<=f<=5: sc+=15
    if 6<=r<=9: sc+=15
    return sc

def gerar_jogo(cfg,a,modo="SUPER"):
    total=cfg["sorteadas"]; falt=a["faltantes"]; mem=a["memoria"]; quentes=a["quentes"]
    jogo=[]
    qf=int(total*0.6); qf=min(qf,len(falt))
    if qf>0: jogo+=random.sample(falt,qf)
    qm=min(5,len(mem),total-len(jogo))
    if qm>0: jogo+=random.sample([m for m in mem if m not in jogo],qm)
    for q in quentes:
        if len(jogo)>=total: break
        if q not in jogo: jogo.append(q)
    while len(jogo)<total:
        n=random.randint(1,cfg["total"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:total])

def ia_3_opcoes(a,cfg):
    # Opcao 1
    scores1={n: (50 if n in a["faltantes"] else 0)+(20 if n in a["quentes"][:10] else 0) for n in range(1,cfg["total"]+1)}
    top1=sorted(scores1, key=scores1.get, reverse=True)[:20]
    jogo1=sorted(random.sample(top1, cfg["sorteadas"]))
    # Opcao 2
    scores2={n: (40 if n in a["memoria"] else 0)+(30 if n in a["quentes"][:15] else 0) for n in range(1,cfg["total"]+1)}
    top2=sorted(scores2, key=scores2.get, reverse=True)[:20]
    jogo2=sorted(random.sample(top2, cfg["sorteadas"]))
    # Opcao 3
    scores3={n: (30 if n in a["faltantes"] else 0)+(25 if n in a["quentes"][:12] else 0)+(15 if n in FIB else 0) for n in range(1,cfg["total"]+1)}
    top3=sorted(scores3, key=scores3.get, reverse=True)[:20]
    jogo3=sorted(random.sample(top3, cfg["sorteadas"]))
    return [("IA FALTANTES",jogo1),("IA MEMORIA",jogo2),("IA FIBONACCI",jogo3)]

tabs=st.tabs(["Gerador","IA 3 Opcoes","Backtest 100","Simulador","Heatmap","Export"])

with tabs[0]:
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Fase",a["fase"]); c2.metric("Faltantes",len(a["faltantes"])); c3.metric("Vistas",f"{a['vistas']}/{a['total']}"); c4.metric("Sorteios ciclo",a["sorteios"])
    st.progress(a["progresso"])
    if a["fase"]=="FIM": st.warning("ALERTA CICLO FIM")
    
    if st.button("GERAR 20 JOGOS",type="primary"):
        jogos=[gerar_jogo(cfg,a) for _ in range(20)]
        st.session_state["jogos"]=jogos
        for i,j in enumerate(jogos,1):
            st.code(f"J{i:02d} {j} | Score {score_jogo(j)}")

with tabs[1]:
    st.subheader("IA - 3 Melhores Opcoes")
    st.info("AGORA FIXO: sempre mostra as 3 estrategias")
    if st.button("GERAR 3 OPCOES IA",type="primary",key="ia3"):
        opcoes=ia_3_opcoes(a,cfg)
        st.session_state["ia_opcoes"]=opcoes
        for nome,jogo in opcoes:
            sc=score_jogo(jogo)
            q={k:len([n for n in jogo if n in v]) for k,v in QUAD.items()}
            st.success(f"{nome} - Score {sc}")
            st.code(f"{jogo}")
            st.caption(f"Quadrantes: Q1={q['Q1']} Q2={q['Q2']} Q3={q['Q3']} Q4={q['Q4']} | Soma={sum(jogo)} | Pares={len([x for x in jogo if x%2==0])}")

with tabs[2]:
    st.subheader("Backtest 100 Concursos - CORRIGIDO")
    st.caption("Agora testa as 3 IAs em cada concurso historico")
    if st.button("RODAR BACKTEST CORRIGIDO"):
        n=min(100,len(df)-30)
        resultados={"IA FALTANTES":[],"IA MEMORIA":[],"IA FIBONACCI":[]}
        for i in range(1,n+1):
            df_hist=df.iloc[:-(i)]
            if len(df_hist)<20: continue
            a_hist=analisar(df_hist,cfg)
            opcoes=ia_3_opcoes(a_hist,cfg)
            real=set(df.iloc[-i].values)
            for nome,jogo in opcoes:
                acertos=len(set(jogo)&real)
                resultados[nome].append(acertos)
        
        for nome,acertos in resultados.items():
            media=np.mean(acertos) if acertos else 0
            p11=sum(1 for x in acertos if x>=11)
            p13=sum(1 for x in acertos if x>=13)
            p14=sum(1 for x in acertos if x>=14)
            st.markdown(f"### {nome}")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Media",f"{media:.2f}")
            c2.metric("11+ acertos",f"{p11}/{len(acertos)} ({p11/len(acertos):.0%})")
            c3.metric("13+",f"{p13}")
            c4.metric("14+",f"{p14}")
            st.line_chart(pd.DataFrame({nome:acertos}))
        
        # Explicacao
        st.info("Se sua tela anterior mostrou 7.20 e 0%, era porque o CSV estava invertido e o teste usava apenas faltantes puros. Agora corrigido.")

with tabs[3]:
    if "jogos" in st.session_state:
        n_test=st.slider("Ultimos",5,30,10)
        hist=[set(df.iloc[-i].values) for i in range(1,n_test+1)]
        res=[max(len(set(j)&h) for h in hist) for j in st.session_state["jogos"]]
        st.dataframe(pd.DataFrame({"Jogo":res}))

with tabs[4]:
    ult=df.tail(20).values.flatten()
    from collections import Counter
    cnt=Counter(ult)
    df_heat=pd.DataFrame({"Dezena":list(range(1,cfg["total"]+1)),"Freq":[cnt.get(i,0) for i in range(1,cfg["total"]+1)]})
    st.bar_chart(df_heat.set_index("Dezena"))

with tabs[5]:
    if "jogos" in st.session_state:
        csv=pd.DataFrame(st.session_state["jogos"]).to_csv(index=False,header=False).encode()
        st.download_button("CSV",csv,"v56.csv","text/csv")
