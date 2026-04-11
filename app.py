import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
from itertools import combinations
import io, re

st.set_page_config(page_title="LOTOELITE PRO v57", layout="wide")
st.title("LOTOELITE PRO v57")
st.caption("TODAS ABAS + MODO SUPER RESTAURADO")

loterias = {
    "Lotofacil": {"total":25,"sorteadas":15,"mantidas":[9,11],"fase_limites":[2,4]},
    "Lotomania":{"total":100,"sorteadas":50,"mantidas":[35,40],"fase_limites":[4,8]},
    "Quina":{"total":80,"sorteadas":5,"mantidas":[2,3],"fase_limites":[15,35]},
    "Mega-Sena":{"total":60,"sorteadas":6,"mantidas":[3,4],"fase_limites":[10,22]}
}

loteria = st.selectbox("Loteria", list(loterias.keys()))
cfg = loterias[loteria]

arquivo = st.file_uploader(f"CSV {loteria}", type=["csv"])
ordem = st.radio("Ordem CSV", ["Mais antigo no topo", "Mais recente no topo"], horizontal=True, index=1)

if not arquivo: st.stop()

df_raw = pd.read_csv(arquivo, header=None).iloc[:,:cfg["sorteadas"]].dropna().astype(int)
df = df_raw.iloc[::-1].reset_index(drop=True) if "recente" in ordem else df_raw

def analisar(df,cfg):
    total=cfg["total"]; vistas=set(); atual=[]
    for i,row in df.iterrows():
        nums=[int(x) for x in row if 1<=int(x)<=total]
        atual.append(i); vistas.update(nums)
        if len(vistas)>=total: atual=[]; vistas=set()
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
        peso=0.7 if modo in ["SUPER","TURBO"] else 0.5
        qf=int(total*peso); qf=min(qf,len(falt))
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
    scores1={n: (50 if n in a["faltantes"] else 0)+(20 if n in a["quentes"][:10] else 0) for n in range(1,cfg["total"]+1)}
    top1=sorted(scores1, key=scores1.get, reverse=True)[:20]
    jogo1=sorted(random.sample(top1, cfg["sorteadas"]))
    scores2={n: (40 if n in a["memoria"] else 0)+(30 if n in a["quentes"][:15] else 0) for n in range(1,cfg["total"]+1)}
    top2=sorted(scores2, key=scores2.get, reverse=True)[:20]
    jogo2=sorted(random.sample(top2, cfg["sorteadas"]))
    scores3={n: (30 if n in a["faltantes"] else 0)+(25 if n in a["quentes"][:12] else 0)+(15 if n in FIB else 0) for n in range(1,cfg["total"]+1)}
    top3=sorted(scores3, key=scores3.get, reverse=True)[:20]
    jogo3=sorted(random.sample(top3, cfg["sorteadas"]))
    return [("IA FALTANTES",jogo1),("IA MEMORIA",jogo2),("IA FIBONACCI",jogo3)]

tabs=st.tabs(["Gerador","IA 3 Opcoes","Filtros","Quadrantes","Desdobramento","Heatmap","Backtest 100","Export"])

with tabs[0]:
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Fase",a["fase"]); c2.metric("Faltantes",len(a["faltantes"])); c3.metric("Vistas",f"{a['vistas']}/{a['total']}"); c4.metric("Progresso",f"{a['progresso']:.0%}")
    st.progress(a["progresso"])
    if a["fase"]=="FIM": st.warning(f"ALERTA CICLO FIM")
    
    modo=st.select_slider("Modo", ["MODERADO","AVANCADO","SUPER","ULTRA","TURBO"], value="SUPER")
    qtd=st.slider("Qtd jogos",5,100,20)
    
    if st.button("GERAR",type="primary"):
        jogos=[gerar_jogo(cfg,a,modo) for _ in range(qtd)]
        if modo=="TURBO":
            jogos=sorted(jogos,key=score_jogo,reverse=True)[:10]
            st.success("TURBO ativo")
        st.session_state["jogos"]=jogos
        for i,j in enumerate(jogos,1):
            st.code(f"J{i:02d} {j} | Score {score_jogo(j)}")

with tabs[1]:
    st.subheader("IA 3 Opcoes")
    if st.button("GERAR 3 OPCOES IA",type="primary"):
        opcoes=ia_3_opcoes(a,cfg)
        st.session_state["ia_opcoes"]=opcoes
        for nome,jogo in opcoes:
            sc=score_jogo(jogo)
            st.success(f"{nome}")
            st.code(f"{jogo} | Score {sc}")

with tabs[2]:
    st.subheader("Filtros")
    st.checkbox("Moldura 8-11",True, key="f1")
    st.checkbox("Pares 7-8",True, key="f2")
    st.checkbox("Fibonacci 3-5",True, key="f3")
    st.checkbox("Soma 195-215",True, key="f4")

with tabs[3]:
    st.subheader("Quadrantes")
    st.write("Q1:1-10 | Q2:11-15 | Q3:16-20 | Q4:21-25")
    if "jogos" in st.session_state:
        for j in st.session_state["jogos"][:5]:
            q={k:len([n for n in j if n in v]) for k,v in QUAD.items()}
            st.write(f"{j} -> Q1:{q['Q1']} Q2:{q['Q2']} Q3:{q['Q3']} Q4:{q['Q4']}")

with tabs[4]:
    st.subheader("Desdobramento")
    base=st.slider("Base",16,20,18)
    if st.button("Desdobrar"):
        pool=list(dict.fromkeys(a["faltantes"]+a["memoria"]+a["quentes"]))[:base]
        jogos=[sorted(random.sample(pool,cfg["sorteadas"])) for _ in range(20)]
        st.session_state["jogos"]=jogos
        st.success(f"{len(jogos)} jogos")

with tabs[5]:
    st.subheader("Heatmap")
    if len(df)>20:
        ult=df.tail(20).values.flatten()
        col_counts={i:sum(1 for n in ult if n in COLS[i]) for i in COLS}
        st.bar_chart(pd.DataFrame(col_counts.items(),columns=["Col","Freq"]).set_index("Col"))

with tabs[6]:
    st.subheader("Backtest 100")
    if st.button("RODAR BACKTEST"):
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
            media=np.mean(acertos)
            p11=sum(1 for x in acertos if x>=11)
            st.markdown(f"### {nome}")
            c1,c2=st.columns(2)
            c1.metric("Media",f"{media:.2f}")
            c2.metric("11+",f"{p11}/{len(acertos)}")
            st.line_chart(pd.DataFrame({nome:acertos}))

with tabs[7]:
    st.subheader("Export")
    if "jogos" in st.session_state:
        jogos=st.session_state["jogos"]
        csv=pd.DataFrame(jogos).to_csv(index=False,header=False).encode()
        st.download_button("CSV",csv,"v57.csv","text/csv")
