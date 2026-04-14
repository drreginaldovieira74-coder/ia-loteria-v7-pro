import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'perfil' not in st.session_state: st.session_state.perfil = {"focus":40}
if 'ciclos' not in st.session_state: st.session_state.ciclos = {}
if 'sugestoes_por_loteria' not in st.session_state: st.session_state.sugestoes_por_loteria = {}

configs = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50},
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00},
    "Quina": {"max":80,"qtd":5,"preco":3.00},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00},
    "Timemania": {"max":80,"qtd":10,"preco":3.50},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50},
    "Super Sete": {"max":9,"qtd":7,"preco":3.00},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00},
}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v78")
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus", 0, 100, st.session_state.perfil["focus"], 5)

cfg = configs[lot]

def analisar(loteria):
    max_n = configs[loteria]["max"]
    quentes = sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
    resto = [x for x in range(1,max_n+1) if x not in quentes]
    frios = sorted(random.sample(resto, int(max_n*0.3)))
    neutros = sorted([x for x in resto if x not in frios])
    return {"q":quentes,"f":frios,"n":neutros,"fase":random.choice(["Início","Meio","Fim","Virada"]),"h":datetime.now().strftime("%H:%M")}

def gerar(focus_pct, ciclo):
    qtd = cfg["qtd"]
    nq = int(qtd * focus_pct / 100)
    jogo = []
    if nq>0: jogo += random.sample(ciclo["q"], min(nq, len(ciclo["q"])))
    resto = qtd - len(jogo)
    pool = ciclo["f"] + ciclo["n"]
    if resto>0: jogo += random.sample(pool, min(resto, len(pool)))
    while len(jogo) < qtd:
        n = random.randint(1, cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

st.title("🎯 LOTOELITE v78")
st.caption("Sistema de Ciclos • Estável")

tabs = st.tabs(["📊 CICLO","🤖 IA 3","🔒 FECHAMENTO","💾 MEUS JOGOS","📥 EXPORTAR"])

with tabs[0]:
    if st.button("🔍 ANALISAR CICLO", type="primary"):
        st.session_state.ciclos[lot] = analisar(lot)
    if lot in st.session_state.ciclos:
        c = st.session_state.ciclos[lot]
        st.success(f"Fase: {c['fase']} - {c['h']}")
        col1,col2,col3 = st.columns(3)
        with col1: st.write("🔥 QUENTES"); st.code(" ".join(f"{n:02d}" for n in c["q"][:12]))
        with col2: st.write("❄️ FRIOS"); st.code(" ".join(f"{n:02d}" for n in c["f"][:12]))
        with col3: st.write("⚖️ NEUTROS"); st.code(" ".join(f"{n:02d}" for n in c["n"][:12]))

with tabs[1]:
    if lot not in st.session_state.ciclos:
        st.error("Analise o ciclo primeiro")
        st.stop()
    
    sug = st.session_state.sugestoes_por_loteria.get(lot, [])
    
    if st.button("Gerar 3 Jogos"):
        ciclo = st.session_state.ciclos[lot]
        novas = []
        for f in [max(10,focus-15), focus, min(95,focus+15)]:
            jogo = gerar(f, ciclo)
            novas.append({"f":f,"j":jogo})
        st.session_state.sugestoes_por_loteria[lot] = novas
        sug = novas
    
    for i,s in enumerate(sug,1):
        c1,c2 = st.columns([4,1])
        with c1: st.code(f"S{i} F{s['f']}%: {'-'.join(f'{n:02d}' for n in s['j'])}")
        with c2:
            if st.button("💾", key=f"sv{lot}{i}"):
                st.session_state.historico.append({"lot":lot,"j":s["j"],"f":s["f"],"data":datetime.now().strftime("%d/%m %H:%M"),"ac":None,"p":cfg["preco"]})
                st.success("Salvo!")

with tabs[2]:
    if lot not in st.session_state.ciclos:
        st.error("Analise o ciclo")
        st.stop()
    qtd = st.number_input("Quantos jogos?", 1, 500, 20)
    st.info(f"Total: R$ {qtd*cfg['preco']:.2f}")
    if st.button(f"Gerar {qtd}"):
        ciclo = st.session_state.ciclos[lot]
        jogos = [gerar(focus, ciclo) for _ in range(qtd)]
        for i,j in enumerate(jogos[:20],1):
            st.text(f"{i:03d}: {'-'.join(f'{n:02d}' for n in j)}")
        if st.button("Salvar Todos"):
            for j in jogos:
                st.session_state.historico.append({"lot":lot,"j":j,"f":focus,"data":datetime.now().strftime("%H:%M"),"ac":None,"p":cfg["preco"]})
            st.balloons()

with tabs[3]:
    st.subheader("Meus Jogos")
    if st.session_state.historico:
        for idx,h in enumerate(reversed(st.session_state.historico[-20:])):
            real_idx = len(st.session_state.historico)-1-idx
            c1,c2 = st.columns([5,1])
            with c1:
                st.text(f"{h['lot']} F{h['f']}%: {'-'.join(f'{n:02d}' for n in h['j'])}")
            with c2:
                if st.button("X", key=f"del{real_idx}"):
                    st.session_state.historico.pop(real_idx)
                    st.rerun()
    else:
        st.info("Nenhum jogo salvo")

with tabs[4]:
    st.subheader("Exportar")
    if st.session_state.historico:
        # CSV em vez de Excel - não precisa openpyxl
        df = pd.DataFrame(st.session_state.historico)
        df["Jogo"] = df["j"].apply(lambda x: "-".join(f"{n:02d}" for n in x))
        csv = df[["data","lot","f","p","Jogo"]].to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📥 Baixar CSV (abre no Excel)",
            csv,
            "lotoelite_v78.csv",
            "text/csv",
            use_container_width=True
        )
        st.success(f"{len(df)} jogos prontos para exportar")
    else:
        st.info("Salve jogos primeiro")
