# -*- coding: utf-8 -*-
import streamlit as st, requests, random, json
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="LOTOELITE v85.1", layout="wide")

# CSS
st.markdown('''<style>
.main-title{text-align:center;font-size:2.8em;font-weight:900;background:linear-gradient(90deg,#FFD700,#FF8C00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
.ia-box{position:fixed;top:12px;left:12px;background:#111;color:#0f0;padding:6px 12px;border-radius:8px;font-family:monospace;font-size:0.85em;z-index:999}
</style><div class="ia-box">🧠 v85.1 IA CICLO+</div>''', unsafe_allow_html=True)
st.markdown('<div class="main-title">LOTOELITE v85.1</div>', unsafe_allow_html=True)

# DNA
DNA = {
 "lotofacil":[4,6,10,14,17,19,20,24,25],
 "megasena":[5,12,23,34,41,56],
 "quina":[7,17,23,34,58],
 "lotomania":[3,8,15,22,29,36,44,51,63,71,78,85,92,97],
 "duplasena":[8,14,19,27,35,42],
 "supersete":[2,4,6,8,1,3,5],
 "timemania":[5,12,23,34,45,56,67],
 "diadesorte":[4,8,12,16,20,24,28],
 "+milionaria":[7,14,21,28,35,42]
}

loterias = {
 "lotofacil":{"n":15,"max":25,"api":"lotofacil"},
 "megasena":{"n":6,"max":60,"api":"mega-sena"},
 "quina":{"n":5,"max":80,"api":"quina"},
 "lotomania":{"n":20,"max":100,"api":"lotomania"},
 "duplasena":{"n":6,"max":50,"api":"dupla-sena"},
 "supersete":{"n":7,"max":9,"api":"super-sete"},
 "timemania":{"n":7,"max":80,"api":"timemania"},
 "diadesorte":{"n":7,"max":31,"api":"dia-de-sorte"},
 "+milionaria":{"n":6,"max":50,"api":"+milionaria"}
}

ciclos_ideais = {
 "lotofacil":(4,6),"megasena":(9,11),"quina":(14,16),"lotomania":(4,5),
 "duplasena":(7,9),"supersete":(8,10),"timemania":(10,12),"diadesorte":(4,5),"+milionaria":(8,10)
}

if "ciclos" not in st.session_state: st.session_state.ciclos={}
if "historico_ciclos" not in st.session_state: st.session_state.historico_ciclos={}
if "jogos_salvos" not in st.session_state: st.session_state.jogos_salvos=[]

def fetch_draws(api,n=80):
    try:
        url=f"https://loteriascaixa-api.herokuapp.com/api/{api}/latest"
        r=requests.get(url,timeout=5).json()
        ultimo=r.get("concurso",1000)
        draws=[]
        for i in range(n):
            try:
                rr=requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api}/{ultimo-i}",timeout=4).json()
                nums=[int(x) for x in rr.get("dezenas",[])]
                draws.append({"concurso":ultimo-i,"nums":nums})
            except: pass
        return draws
    except: return []

def buscar_ciclo_real(lot):
    cfg=loterias[lot]; draws=fetch_draws(cfg["api"],80)
    if not draws: return {"q":[],"f":[],"n":list(range(1,cfg["max"]+1)),"ciclo_atual":0,"freq":{}}
    pool=cfg["max"]; freq={i:0 for i in range(1,pool+1)}
    for d in draws:
        for n in d["nums"]: freq[n]+=1
    # ciclo atual = quantos concursos até cobrir pool
    vistos=set(); ciclo=0
    for d in draws:
        vistos.update(d["nums"]); ciclo+=1
        if len(vistos)>=pool: break
    orden=sorted(freq.items(),key=lambda x:x[1],reverse=True)
    q=[x[0] for x in orden[:int(pool*0.3)]]
    f=[x[0] for x in orden[-int(pool*0.3):]]
    n=[x for x in range(1,pool+1) if x not in q and x not in f]
    return {"q":q,"f":f,"n":n,"ciclo_atual":ciclo,"freq":freq,"draws":draws}

def gerar(lot,focus,ciclo):
    cfg=loterias[lot]; n=cfg["n"]; pool=cfg["max"]
    q,f,nn=ciclo["q"],ciclo["f"],ciclo["n"]
    dna=DNA.get(lot,[])
    # v85.1 brecha DNA
    dna_q=[d for d in dna if d in q]
    dna_f=[d for d in dna if d in f]
    ca=ciclo.get("ciclo_atual",0); ideal=ciclos_ideais.get(lot,(0,0))
    prioriza_frios = ca < ideal[0]*0.8 if ideal[0] else False
    dna_prio = dna_f + dna_q if prioriza_frios else dna_q + dna_f
    
    base=int(n*(focus/100)); base=max(2,min(n-2,base))
    jogo=[]
    # 1) DNA priorizado
    for d in dna_prio:
        if len(jogo)<base and d<=pool and d not in jogo: jogo.append(d)
    # 2) completa quentes
    for x in q:
        if len(jogo)<base and x not in jogo: jogo.append(x)
    # 3) neutros
    random.shuffle(nn)
    for x in nn:
        if len(jogo)<n-2 and x not in jogo: jogo.append(x)
    # 4) frios para fechar
    for x in f:
        if len(jogo)<n and x not in jogo: jogo.append(x)
    while len(jogo)<n:
        r=random.randint(1,pool)
        if r not in jogo: jogo.append(r)
    return sorted(jogo[:n])

# SIDEBAR
with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v85.1")
    lot=st.selectbox("Loteria",list(loterias.keys()),index=0)
    focus=st.slider("Foco Quentes %",10,95,60)

tabs=st.tabs(["CICLO","IA · 3 Sugestões","HUB","SALVOS"])

with tabs[0]:
    st.subheader(f"CICLO REAL - {lot.upper()}")
    if st.button("🔄 ATUALIZAR"):
        c=buscar_ciclo_real(lot)
        st.session_state.ciclos[lot]=c
        hist=st.session_state.historico_ciclos.get(lot,[])
        hist.append({"data":datetime.now().strftime("%d/%m %H:%M"),"ciclo_atual":c["ciclo_atual"],"concurso":c["draws"][0]["concurso"] if c["draws"] else 0})
        st.session_state.historico_ciclos[lot]=hist[-10:]
        st.success("Ciclo atualizado")
    if lot in st.session_state.ciclos:
        c=st.session_state.ciclos[lot]; ideal=ciclos_ideais[lot]; ca=c["ciclo_atual"]
        st.metric("Ciclo atual",f"{ca} concursos",f"Ideal {ideal[0]}-{ideal[1]}")
        # v85.1 anti-ciclo
        freq=c["freq"]; media=sum(freq.values())/len(freq) if freq else 0
        atrasados=[n for n,v in freq.items() if v < media*0.7]
        atrasados=sorted(atrasados,key=lambda x:freq[x])[:8]
        if atrasados:
            st.warning(f"⚠️ ATRASADOS (1.5x): {' '.join(f'{x:02d}' for x in atrasados)}")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown("**🔥 QUENTES**"); st.code(" ".join(f"{n:02d}" for n in c["q"]))
        with c2: st.markdown("**❄️ FRIOS**"); st.code(" ".join(f"{n:02d}" for n in c["f"]))
        with c3: st.markdown("**⚖️ NEUTROS**"); st.code(" ".join(f"{n:02d}" for n in c["n"][:14]))

with tabs[1]:
    st.subheader("IA - 3 Sugestões v85.1")
    if lot not in st.session_state.ciclos: st.error("Atualize ciclo"); st.stop()
    ciclo=st.session_state.ciclos[lot]
    if st.button("🎯 Gerar 3 Jogos REAIS",type="primary"):
        ca=ciclo.get("ciclo_atual",0); ideal=ciclos_ideais.get(lot,(0,0))
        hist=st.session_state.historico_ciclos.get(lot,[])
        vel_media=(ideal[0]+ideal[1])/2
        if len(hist)>=3: vel_media=sum(h["ciclo_atual"] for h in hist[-3:])/3
        velocidade=ca/vel_media if vel_media else 1
        if ca < ideal[0]*0.8:
            base=max(10,focus-25); focos=[base,base+10,base+20]; modo=f"Início ({ca}) → frios+DNA brecha"
        elif ca > ideal[1]*1.1:
            base=min(90,focus+15); focos=[base-10,base,min(95,base+10)]; modo=f"Fim atrasado ({ca}>{ideal[1]}) → quentes"
        else:
            if velocidade<0.85: focos=[max(15,focus-10),focus,min(85,focus+5)]; modo=f"Ciclo rápido {velocidade:.1f}x"
            elif velocidade>1.15: focos=[max(20,focus-5),min(90,focus+10),min(95,focus+20)]; modo=f"Ciclo lento {velocidade:.1f}x"
            else: focos=[max(10,focus-15),focus,min(95,focus+15)]; modo="Meio equilibrado"
        st.caption(f"IA ajustada: {modo}")
        for i,f in enumerate(focos,1):
            jogo=gerar(lot,f,ciclo)
            cols=st.columns([4,1])
            with cols[0]: st.code(" ".join(f"{n:02d}" for n in jogo),language="text")
            with cols[1]:
                if st.button("💾",key=f"sv{i}"): st.session_state.jogos_salvos.append({"lot":lot,"jogo":jogo,"data":datetime.now().strftime("%d/%m")}); st.toast("Salvo!")

with tabs[2]:
    st.subheader("HUB ESPECIAL")
    st.info("DNA ativo em todas as loterias. v85.1 com brecha e anti-ciclo.")

with tabs[3]:
    st.subheader("JOGOS SALVOS")
    for j in st.session_state.jogos_salvos: st.code(f"{j['lot'].upper()} {j['data']}: "+" ".join(f"{n:02d}" for n in j["jogo"]))
