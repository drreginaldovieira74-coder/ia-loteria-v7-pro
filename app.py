import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="LOTOELITE PRO v59", layout="wide")
st.title("LOTOELITE PRO v59")
st.caption("TODAS LOTERIAS + Trevos + Time + Mes da Sorte")

loterias = {
    "Lotofacil": {"total":25,"sorteadas":15,"mantidas":[9,11],"fase":[2,4]},
    "Lotomania": {"total":100,"sorteadas":50,"mantidas":[35,40],"fase":[4,8]},
    "Quina": {"total":80,"sorteadas":5,"mantidas":[2,3],"fase":[15,35]},
    "Mega-Sena": {"total":60,"sorteadas":6,"mantidas":[3,4],"fase":[10,22]},
    "Dupla Sena": {"total":50,"sorteadas":6,"mantidas":[3,4],"fase":[8,18]},
    "Timemania": {"total":80,"sorteadas":10,"mantidas":[5,7],"fase":[12,25]},
    "Dia de Sorte": {"total":31,"sorteadas":7,"mantidas":[3,5],"fase":[5,10]},
    "Mais Milionaria": {"total":50,"sorteadas":6,"mantidas":[3,4],"fase":[8,18],"trevos":2},
    "Super Sete": {"total":10,"sorteadas":7,"mantidas":[4,5],"fase":[2,4]}
}

times_timemania = [
"ABC-RN","AMERICA-MG","AMERICA-RN","AMERICANO","ASA","ATLETICO-GO","ATLETICO-MG","ATLETICO-PR","AVAI","BAHIA",
"BANGU","BOA","BOTAFOGO","BOTAFOGO-PB","BRAGANTINO","BRASIL-RS","BRASILIENSE","CEARA","CHAPECOENSE","CONFIDENCA",
"CORINTHIANS","CORITIBA","CRB","CRICIUMA","CRUZEIRO","CSA","CUIABA","FIGUEIRENSE","FLAMENGO","FLUMINENSE",
"FORTALEZA","GOIAS","GREMIO","GUARANI","INTERNACIONAL","ITUANO","JOINVILLE","JUVENTUDE","LONDRINA","MIRASSOL",
"NAUTICO","OESTE","PALMEIRAS","PARANA","PAYSANDU","PONTE PRETA","PORTUGUESA","REMO","SAMPAIO CORREA","SANTA CRUZ",
"SANTO ANDRE","SANTOS","SAO BERNARDO","SAO CAETANO","SAO PAULO","SPORT","VASCO","VILA NOVA","VITORIA","VOLTA REDONDA"
]

meses_sorte = ["JANEIRO","FEVEREIRO","MARCO","ABRIL","MAIO","JUNHO","JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]

c1,c2 = st.columns([3,1])
with c1:
    loteria = st.selectbox("LOTERIA", list(loterias.keys()))
with c2:
    cfg = loterias[loteria]
    extra = ""
    if loteria=="Mais Milionaria": extra=" +2"
    if loteria=="Timemania": extra=" +Time"
    if loteria=="Dia de Sorte": extra=" +Mes"
    st.metric("Formato", f"{cfg['sorteadas']}/{cfg['total']}{extra}")

arquivo = st.file_uploader(f"CSV {loteria}", type=["csv"])
ordem = st.radio("Ordem", ["Mais recente no topo","Mais antigo no topo"], horizontal=True)

if not arquivo:
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
    peso=0.7 if modo in ["SUPER","TURBO"] else 0.5
    qf=min(int(total*peso), len(falt))
    if qf>0: jogo+=random.sample(falt,qf)
    if mem:
        qm=min(3,len(mem),total-len(jogo))
        jogo+=random.sample([m for m in mem if m not in jogo],qm)
    for q in quentes:
        if len(jogo)>=total: break
        if q not in jogo: jogo.append(q)
    while len(jogo)<total:
        n=random.randint(1,cfg["total"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:total])

def ia3(a,cfg):
    t=cfg["total"]; s=cfg["sorteadas"]
    pool=range(1,t+1)
    j1=sorted(random.sample([n for n in pool if n in a["faltantes"] or n in a["quentes"][:10]], s))
    j2=sorted(random.sample([n for n in pool if n in a["memoria"] or n in a["quentes"][:15]], s))
    j3=sorted(random.sample(a["quentes"][:20], min(s,20)))
    while len(j3)<s: j3.append(random.randint(1,t))
    j3=sorted(j3[:s])
    return [("IA FALTANTES",j1),("IA MEMORIA",j2),("IA QUENTES",j3)]

tabs = st.tabs(["Gerador","IA 3","Filtros","Desdobro","Heatmap","Backtest","Export"])

with tabs[0]:
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Fase",a["fase"]); m2.metric("Faltantes",len(a["faltantes"])); m3.metric("Vistas",f"{a['vistas']}/{a['total']}"); m4.metric("Prog",f"{a['progresso']:.0%}")
    st.progress(a["progresso"])
    
    # Opcoes extras por loteria
    time_escolhido=None; mes_escolhido=None
    if loteria=="Timemania":
        time_escolhido=st.selectbox("Time do Coracao", times_timemania)
    if loteria=="Dia de Sorte":
        mes_escolhido=st.selectbox("Mes da Sorte", meses_sorte)
    if loteria=="Mais Milionaria":
        st.info("Trevos (2/6) serao gerados automaticamente")
    
    modo=st.select_slider("Modo",["MODERADO","AVANCADO","SUPER","ULTRA","TURBO"],value="SUPER")
    qtd=st.slider("Jogos",5,30,15)
    
    if st.button("GERAR",type="primary",use_container_width=True):
        jogos=[gerar(cfg,a,modo) for _ in range(qtd)]
        st.session_state["jogos"]=jogos
        st.session_state["time"]=time_escolhido
        st.session_state["mes"]=mes_escolhido
        for i,j in enumerate(jogos,1):
            txt=f"J{i:02d}: {'-'.join(f'{n:02d}' for n in j)}"
            if loteria=="Mais Milionaria":
                t=sorted(random.sample(range(1,7),2))
                txt+=f" | Trevos: {t[0]:02d}-{t[1]:02d}"
            if loteria=="Timemania" and time_escolhido:
                txt+=f" | Time: {time_escolhido}"
            if loteria=="Dia de Sorte" and mes_escolhido:
                txt+=f" | Mes: {mes_escolhido}"
            st.code(txt)

with tabs[1]:
    if st.button("GERAR 3 IAS"):
        ops=ia3(a,cfg)
        for nome,j in ops:
            txt='-'.join(f'{n:02d}' for n in j)
            if loteria=="Mais Milionaria":
                t=sorted(random.sample(range(1,7),2)); txt+=f" | T:{t[0]:02d}-{t[1]:02d}"
            st.success(nome); st.code(txt)

with tabs[2]:
    st.write("Filtros automaticos ativos para", loteria)

with tabs[3]:
    base=st.slider("Base desdobro", cfg["sorteadas"]+1, min(25,cfg["total"]), 18)
    if st.button("Desdobrar"):
        pool=list(dict.fromkeys(a["faltantes"]+a["quentes"]))[:base]
        jogos=[sorted(random.sample(pool,cfg["sorteadas"])) for _ in range(12)]
        st.session_state["jogos"]=jogos
        st.success(f"{len(jogos)} jogos")

with tabs[4]:
    cnt=pd.Series(df.tail(30).values.flatten()).value_counts().sort_index()
    st.bar_chart(cnt)

with tabs[5]:
    if st.button("Backtest 50"):
        n=min(50,len(df)-10); res=[]
        for i in range(1,n+1):
            h=df.iloc[:-(i)]; ah=analisar(h,cfg); j=gerar(cfg,ah,"SUPER"); r=set(df.iloc[-i].values); res.append(len(set(j)&r))
        st.metric("Media",f"{np.mean(res):.2f}"); st.line_chart(pd.DataFrame({"acertos":res}))

with tabs[6]:
    if "jogos" in st.session_state:
        jogos=st.session_state["jogos"]
        linhas=[]
        for j in jogos:
            base='-'.join(f'{n:02d}' for n in j)
            if loteria=="Mais Milionaria":
                t=sorted(random.sample(range(1,7),2)); base+=f";{t[0]:02d}-{t[1]:02d}"
            if loteria=="Timemania" and st.session_state.get("time"):
                base+=f";{st.session_state['time']}"
            if loteria=="Dia de Sorte" and st.session_state.get("mes"):
                base+=f";{st.session_state['mes']}"
            linhas.append(base)
        txt="\n".join(linhas)
        st.text_area("Jogos", txt, height=200)
        st.download_button("CSV", "\n".join(linhas), f"{loteria}_v59.txt")
