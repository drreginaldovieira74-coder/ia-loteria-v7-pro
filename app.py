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

st.set_page_config(page_title="LOTOELITE PRO v54", layout="wide")
st.title("LOTOELITE PRO v54")
st.caption("Simulador | Alerta Ciclo | Comparador Mr.Loto | Turbo 100")

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

# Constantes Lotofacil
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

def gerar(cfg,a,modo,filtros):
    total=cfg["sorteadas"]; falt=a["faltantes"]; mem=a["memoria"]; quentes=a["quentes"]
    for _ in range(400):
        jogo=[]
        if modo=="ULTRA_FOCUS" and len(falt)>=total:
            jogo=random.sample(falt,total)
        else:
            qf=int(total*(0.7 if modo in ["SUPER_FOCUS","TURBO"] else 0.5))
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
        jogo=sorted(jogo[:total])
        if not filtros.get("ativo"): return jogo
        # filtro rapido
        if filtros.get("moldura") and not (8<=len([x for x in jogo if x in MOLD])<=11): continue
        if filtros.get("pares") and not (7<=len([x for x in jogo if x%2==0])<=8): continue
        return jogo
    return sorted(random.sample(range(1,cfg["total"]+1),total))

tabs=st.tabs(["Gerador v54","Filtros","Quadrantes","Desdobramento","Heatmap","IA","Simulador","Comparador","Export"])

with tabs[0]:
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Fase",a["fase"]); c2.metric("Faltantes",len(a["faltantes"])); c3.metric("Vistas",f"{a['vistas']}/{a['total']}"); c4.metric("Progresso",f"{a['progresso']:.0%}")
    st.progress(a["progresso"])
    # Alerta ciclo
    if a["fase"]=="FIM" and a["sorteios"]>=cfg["fase_limites"][1]-1:
        st.warning(f"ALERTA CICLO: faltam ~{cfg['fase_limites'][1]+2 - a['sorteios']} sorteios para fechar. Fase FIM = maior probabilidade.")
    elif a["fase"]=="MEIO":
        st.info("Ciclo em MEIO - comece a aumentar apostas.")
    
    modo=st.select_slider("Modo",["MODERADO","AVANCADO","SUPER_FOCUS","ULTRA_FOCUS","TURBO"],value="SUPER_FOCUS")
    qtd=st.slider("Qtd jogos",5,100,20) if modo!="TURBO" else 100
    
    if st.button("GERAR",type="primary"):
        filtros=st.session_state.get("f", {"ativo":True,"moldura":True,"pares":True})
        jogos=[gerar(cfg,a,modo,filtros) for _ in range(qtd)]
        if modo=="TURBO":
            jogos=sorted(jogos, key=score_jogo, reverse=True)[:10]
            st.success("TURBO: 100 gerados, top 10 selecionados por score")
        st.session_state["jogos"]=jogos
        for i,j in enumerate(jogos,1):
            st.code(f"J{i:02d} {j} | Score:{score_jogo(j)}")

with tabs[1]:
    st.subheader("Filtros v54")
    f={"ativo":st.checkbox("Ativar filtros",True)}
    f["moldura"]=st.checkbox("Moldura 8-11",True)
    f["pares"]=st.checkbox("Pares 7-8",True)
    f["fib"]=st.checkbox("Fibonacci 3-5",True)
    st.session_state["f"]=f

with tabs[2]:
    st.write("Q1 1-10 | Q2 11-15 | Q3 16-20 | Q4 21-25")
    if "jogos" in st.session_state:
        for j in st.session_state["jogos"][:3]:
            q={k:len([n for n in j if n in v]) for k,v in QUAD.items()}
            st.write(f"{j} -> {q}")

with tabs[3]:
    base=st.slider("Base desdobramento",16,20,20)
    if st.button("Desdobrar"):
        pool=list(dict.fromkeys(a["faltantes"]+a["memoria"]+a["quentes"]))[:base]
        jogos=[]
        if base==20:
            fix=pool[:11]
            for c in combinations(pool[11:],4): jogos.append(sorted(fix+list(c)))
        else:
            for _ in range(25): jogos.append(sorted(random.sample(pool,cfg["sorteadas"])))
        st.session_state["jogos"]=jogos[:25]
        st.success(f"{len(jogos[:25])} jogos gerados")

with tabs[4]:
    if len(df)>20:
        ult=df.tail(20).values.flatten()
        col_counts={i:sum(1 for n in ult if n in COLS[i]) for i in COLS}
        st.bar_chart(pd.DataFrame(col_counts.items(),columns=["Col","Freq"]).set_index("Col"))

with tabs[5]:
    top=[n for n in range(1,cfg["total"]+1)]
    top.sort(key=lambda x:(x in a["faltantes"], x in a["quentes"][:10]), reverse=True)
    st.write("Top IA:", top[:20])

with tabs[6]:
    st.subheader("Simulador de Premiacao")
    st.caption("Testa seus jogos contra os ultimos concursos")
    if "jogos" not in st.session_state:
        st.info("Gere jogos primeiro")
    else:
        n_test=st.slider("Ultimos concursos para testar",5,30,10)
        historico=[set(df.iloc[-i].values) for i in range(1,n_test+1)]
        resultados=[]
        for jogo in st.session_state["jogos"]:
            acertos=[len(set(jogo)&h) for h in historico]
            resultados.append(max(acertos))
        df_res=pd.DataFrame({"Jogo":[f"J{i+1}" for i in range(len(resultados))],"Melhor Acerto":resultados})
        st.dataframe(df_res)
        premiados=sum(1 for x in resultados if x>=11)
        st.success(f"Se tivesse jogado: {premiados} jogos premiariam (11+ acertos) nos ultimos {n_test} concursos")

with tabs[7]:
    st.subheader("Comparador vs Mr.Loto")
    txt=st.text_area("Cole jogos do Mr.Loto (um por linha, ex: 01-02-03...)")
    if st.button("Comparar") and txt:
        jogos_ml=[]
        for linha in txt.splitlines():
            nums=[int(x) for x in re.findall(r'\d+',linha)][:cfg["sorteadas"]]
            if len(nums)==cfg["sorteadas"]: jogos_ml.append(sorted(nums))
        if "jogos" in st.session_state:
            nossos=st.session_state["jogos"]
            score_nosso=np.mean([score_jogo(j) for j in nossos])
            score_ml=np.mean([score_jogo(j) for j in jogos_ml]) if jogos_ml else 0
            c1,c2=st.columns(2)
            c1.metric("Score Medio LotoElite",f"{score_nosso:.1f}")
            c2.metric("Score Medio Mr.Loto",f"{score_ml:.1f}")
            if score_nosso>score_ml:
                st.success("LotoElite vence por filtragem superior")
            else:
                st.warning("Ajuste filtros")

with tabs[8]:
    if "jogos" in st.session_state:
        jogos=st.session_state["jogos"]
        csv=pd.DataFrame(jogos).to_csv(index=False,header=False).encode()
        st.download_button("Baixar CSV",csv,"lotoelite_v54.csv","text/csv")
        if PDF_AVAILABLE:
            buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=A4); c.setFont("Helvetica-Bold",12)
            c.drawString(20*mm,280*mm,f"LOTOELITE v54 - {loteria}")
            y=260
            for i,j in enumerate(jogos,1):
                c.drawString(20*mm,y*mm,f"J{i:02d}: {'-'.join(f'{n:02d}' for n in j)}")
                y-=7
                if y<20: c.showPage(); y=280
            c.save(); buf.seek(0)
            st.download_button("PDF",buf,"v54.pdf","application/pdf")
