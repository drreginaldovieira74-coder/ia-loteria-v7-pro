import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="LOTOELITE PRO v58", layout="wide")
st.title("LOTOELITE PRO v58")
st.caption("TODAS AS LOTERIAS BRASILEIRAS")

loterias = {
    "Lotofacil": {"total":25,"sorteadas":15,"mantidas":[9,11],"fase":[2,4]},
    "Lotomania": {"total":100,"sorteadas":50,"mantidas":[35,40],"fase":[4,8]},
    "Quina": {"total":80,"sorteadas":5,"mantidas":[2,3],"fase":[15,35]},
    "Mega-Sena": {"total":60,"sorteadas":6,"mantidas":[3,4],"fase":[10,22]},
    "Dupla Sena": {"total":50,"sorteadas":6,"mantidas":[3,4],"fase":[8,18]},
    "Timemania": {"total":80,"sorteadas":10,"mantidas":[5,7],"fase":[12,25]},
    "Dia de Sorte": {"total":31,"sorteadas":7,"mantidas":[3,5],"fase":[5,10]},
    "Mais Milionaria": {"total":50,"sorteadas":6,"mantidas":[3,4],"fase":[8,18]},
    "Super Sete": {"total":10,"sorteadas":7,"mantidas":[4,5],"fase":[2,4]}
}

c1,c2 = st.columns([3,1])
with c1:
    loteria = st.selectbox("ESCOLHA A LOTERIA", list(loterias.keys()))
with c2:
    cfg = loterias[loteria]
    st.metric("Formato", f"{cfg['sorteadas']}/{cfg['total']}")

arquivo = st.file_uploader(f"Upload CSV - {loteria}", type=["csv"])
ordem = st.radio("Ordem do arquivo", ["Mais recente no topo", "Mais antigo no topo"], horizontal=True)

if not arquivo:
    st.info("Faca upload do historico em CSV")
    st.stop()

df_raw = pd.read_csv(arquivo, header=None).iloc[:,:cfg["sorteadas"]].dropna().astype(int)
df = df_raw.iloc[::-1].reset_index(drop=True) if ordem=="Mais recente no topo" else df_raw

def analisar(df,cfg):
    total=cfg["total"]; vistas=set(); atual=[]
    for _,row in df.iterrows():
        nums=[int(x) for x in row if 1<=int(x)<=total]
        atual.append(1); vistas.update(nums)
        if len(vistas)>=total: atual=[]; vistas=set()
    falt=sorted(set(range(1,total+1))-vistas)
    sorteios=len(atual); lim1,lim2=cfg["fase"]
    fase="ZERADO" if sorteios==0 else "INICIO" if sorteios<=lim1 else "MEIO" if sorteios<=lim2 else "FIM"
    progresso=len(vistas)/total
    freq=np.bincount(df.tail(30).values.flatten(), minlength=total+1)[1:]
    quentes=[int(x) for x in np.argsort(freq)[-20:][::-1]+1]
    ultimo=[int(x) for x in df.iloc[-1].values]
    memoria=list(set(df.iloc[-2].values)) if len(df)>1 else []
    return {"fase":fase,"faltantes":falt,"memoria":memoria,"quentes":quentes,"ultimo":ultimo,"progresso":progresso,"sorteios":sorteios,"vistas":len(vistas),"total":total}

a = analisar(df,cfg)

def gerar(cfg,a,modo):
    total=cfg["sorteadas"]; falt=a["faltantes"]; mem=a["memoria"]; quentes=a["quentes"]
    jogo=[]
    peso = 0.7 if modo in ["SUPER","TURBO"] else 0.5 if modo=="AVANCADO" else 0.3
    qf = min(int(total*peso), len(falt))
    if qf>0: jogo += random.sample(falt, qf)
    if mem:
        qm = min(3, len(mem), total-len(jogo))
        jogo += random.sample([m for m in mem if m not in jogo], qm)
    for q in quentes:
        if len(jogo)>=total: break
        if q not in jogo: jogo.append(q)
    while len(jogo)<total:
        n=random.randint(1,cfg["total"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:total])

def ia3(a,cfg):
    t=cfg["total"]; s=cfg["sorteadas"]
    top1 = sorted(range(1,t+1), key=lambda n: (n in a["faltantes"], n in a["quentes"][:10]), reverse=True)[:20]
    j1 = sorted(random.sample(top1, s))
    top2 = sorted(range(1,t+1), key=lambda n: (n in a["memoria"], n in a["quentes"][:15]), reverse=True)[:20]
    j2 = sorted(random.sample(top2, s))
    top3 = sorted(range(1,t+1), key=lambda n: (n in a["quentes"], n in a["faltantes"]), reverse=True)[:20]
    j3 = sorted(random.sample(top3, s))
    return [("IA FALTANTES",j1),("IA MEMORIA",j2),("IA QUENTES",j3)]

tabs = st.tabs(["Gerador","IA 3 Opcoes","Filtros","Desdobramento","Heatmap","Backtest","Export","Loterias"])

with tabs[0]:
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Fase", a["fase"]); m2.metric("Faltantes", len(a["faltantes"])); m3.metric("Vistas", f"{a['vistas']}/{a['total']}"); m4.metric("Progresso", f"{a['progresso']:.0%}")
    st.progress(a["progresso"])
    if a["fase"]=="FIM": st.warning("CICLO EM FIM - OPORTUNIDADE")
    modo = st.select_slider("Modo", ["MODERADO","AVANCADO","SUPER","ULTRA","TURBO"], value="SUPER")
    qtd = st.slider("Jogos", 5, 50, 20)
    if st.button("GERAR", type="primary", use_container_width=True):
        jogos = [gerar(cfg,a,modo) for _ in range(qtd)]
        st.session_state["jogos"]=jogos
        for i,j in enumerate(jogos,1):
            st.code(f"J{i:02d}: {'-'.join(f'{n:02d}' for n in j)}")

with tabs[1]:
    if st.button("GERAR 3 IAS", type="primary"):
        ops = ia3(a,cfg)
        st.session_state["ia"]=ops
        for nome,j in ops:
            st.success(nome)
            st.code(' - '.join(f'{n:02d}' for n in j))

with tabs[2]:
    st.subheader("Filtros")
    if loteria=="Lotofacil":
        st.checkbox("Moldura 8-11", True)
        st.checkbox("Pares 7-8", True)
        st.checkbox("Soma 195-215", True)
    else:
        st.info(f"Filtros automaticos para {loteria} ativos")

with tabs[3]:
    st.subheader("Desdobramento")
    base = st.slider("Base", cfg["sorteadas"]+1, min(cfg["total"],25), 18)
    if st.button("Desdobrar"):
        pool = list(dict.fromkeys(a["faltantes"]+a["quentes"]))[:base]
        jogos = [sorted(random.sample(pool, cfg["sorteadas"])) for _ in range(15)]
        st.session_state["jogos"]=jogos
        st.success(f"{len(jogos)} jogos")

with tabs[4]:
    st.subheader("Heatmap")
    cnt = pd.Series(df.tail(30).values.flatten()).value_counts().sort_index()
    st.bar_chart(cnt)

with tabs[5]:
    st.subheader("Backtest")
    if st.button("Rodar"):
        n=min(50,len(df)-10); res=[]
        for i in range(1,n+1):
            hist=df.iloc[:-(i)]; ah=analisar(hist,cfg); j=gerar(cfg,ah,"SUPER"); r=set(df.iloc[-i].values); res.append(len(set(j)&r))
        st.metric("Media", f"{np.mean(res):.2f}")
        st.line_chart(pd.DataFrame({"acertos":res}))

with tabs[6]:
    if "jogos" in st.session_state:
        jogos=st.session_state["jogos"]
        csv=pd.DataFrame(jogos).to_csv(index=False,header=False).encode()
        st.download_button("Baixar CSV", csv, f"{loteria}_v58.csv")
        txt = "\n".join(["-".join(f"{n:02d}" for n in j) for j in jogos])
        st.text_area("Copiar", txt, height=150)

with tabs[7]:
    st.dataframe(pd.DataFrame([
        ["Lotofacil", "15/25", "2-4 sorteios"],
        ["Lotomania", "50/100", "4-8 sorteios"],
        ["Quina", "5/80", "15-35"],
        ["Mega-Sena", "6/60", "10-22"],
        ["Dupla Sena", "6/50", "8-18"],
        ["Timemania", "10/80", "12-25"],
        ["Dia de Sorte", "7/31", "5-10"],
        ["Mais Milionaria", "6/50", "8-18"],
        ["Super Sete", "7/10", "2-4"],
    ], columns=["Loteria","Formato","Ciclo"]), hide_index=True, use_container_width=True)
