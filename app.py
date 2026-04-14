import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v78", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:2.4rem; font-weight:800; text-align:center;}
.ciclo-box {background:#fff3cd; padding:8px; border-radius:6px; border-left:4px solid #ff9800;}
</style>
""", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
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
    st.markdown("### 🎯 LOTOELITE")
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, 40, 5)

cfg = configs[lot]

def analisar(loteria):
    max_n = configs[loteria]["max"]
    quentes = sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
    resto = [x for x in range(1,max_n+1) if x not in quentes]
    frios = sorted(random.sample(resto, int(max_n*0.3)))
    neutros = sorted([x for x in resto if x not in frios])
    return {"q":quentes,"f":frios,"n":neutros,"fase":random.choice(["Início","Meio","Fim","Virada"])}

def gerar(focus_pct, ciclo):
    qtd = cfg["qtd"]
    nq = int(qtd * focus_pct / 100)
    jogo = []
    if nq>0: jogo += random.sample(ciclo["q"], min(nq, len(ciclo["q"])))
    pool = ciclo["f"] + ciclo["n"]
    if len(jogo) < qtd:
        jogo += random.sample(pool, min(qtd-len(jogo), len(pool)))
    while len(jogo) < qtd:
        n = random.randint(1, cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

st.markdown('<div class="main-title">🎯 LOTOELITE v78</div>', unsafe_allow_html=True)

tabs = st.tabs(["📊 CICLO","🤖 IA 3","🔒 FECHAMENTO","🔒 FECH 21","📍 POSIÇÃO","📈 GRÁFICO","🎲 BOLÕES","🏆 RESULTADOS","💾 MEUS JOGOS","🔍 CONFERIDOR","🧠 PERFIL","💰 PREÇOS","📥 EXPORTAR"])

with tabs[0]:
    st.markdown('<div class="ciclo-box">Analise o ciclo antes de gerar</div>', unsafe_allow_html=True)
    if st.button("🔍 ANALISAR CICLO", type="primary"):
        st.session_state.ciclos[lot] = analisar(lot)
        st.success("Ciclo analisado!")
    if lot in st.session_state.ciclos:
        c = st.session_state.ciclos[lot]
        st.metric("Fase", c["fase"])
        col1,col2,col3 = st.columns(3)
        with col1: st.caption("🔥 QUENTES"); st.code(" ".join(f"{n:02d}" for n in c["q"][:15]))
        with col2: st.caption("❄️ FRIOS"); st.code(" ".join(f"{n:02d}" for n in c["f"][:15]))
        with col3: st.caption("⚖️ NEUTROS"); st.code(" ".join(f"{n:02d}" for n in c["n"][:15]))

with tabs[1]:
    if lot not in st.session_state.ciclos:
        st.error("⛔ Analise o ciclo primeiro")
        st.stop()
    if st.button("Gerar 3 Jogos", type="primary"):
        ciclo = st.session_state.ciclos[lot]
        novas = []
        for f in [max(10,focus-15), focus, min(95,focus+15)]:
            jogo = gerar(f, ciclo)
            nq = len(set(jogo) & set(ciclo["q"]))
            novas.append({"f":f,"j":jogo,"nq":nq})
        st.session_state.sugestoes_por_loteria[lot] = novas
    
    for i,s in enumerate(st.session_state.sugestoes_por_loteria.get(lot, []), 1):
        c1,c2 = st.columns([5,1])
        with c1: st.code(f"S{i} F{s['f']}% ({s['nq']}Q): {'-'.join(f'{n:02d}' for n in s['j'])}")
        with c2:
            if st.button("💾", key=f"sv{lot}{i}"):
                st.session_state.historico.append({"lot":lot,"j":s["j"],"f":s["f"],"data":datetime.now().strftime("%H:%M"),"ac":None,"p":cfg["preco"]})
                st.success("✓")

with tabs[2]:
    if lot not in st.session_state.ciclos:
        st.error("Analise o ciclo")
        st.stop()
    qtd = st.number_input("Quantos jogos?", 1, 500, 20)
    st.info(f"R$ {qtd*cfg['preco']:.2f}")
    if st.button(f"Gerar {qtd}"):
        ciclo = st.session_state.ciclos[lot]
        jogos = [gerar(focus, ciclo) for _ in range(qtd)]
        cols = st.columns(2)
        for i,j in enumerate(jogos[:40]):
            with cols[i%2]: st.text(f"{i+1:03d}: {'-'.join(f'{n:02d}' for n in j)}")
        if st.button("Salvar Todos"):
            for j in jogos:
                st.session_state.historico.append({"lot":lot,"j":j,"f":focus,"data":datetime.now().strftime("%H:%M"),"ac":None,"p":cfg["preco"]})
            st.balloons()

with tabs[3]:
    if lot == "Lotofácil":
        base = st.multiselect("21 números", list(range(1,26)), list(range(1,22)), format_func=lambda x:f"{x:02d}")
        q = st.slider("Jogos",5,50,15)
        if st.button("Gerar Fechamento") and len(base)==21:
            for i in range(q):
                st.code(f"{i+1}: {'-'.join(f'{n:02d}' for n in sorted(random.sample(base,15)))}")

with tabs[4]:
    st.dataframe(pd.DataFrame([{"Loteria":k,"Fase":random.choice(["Início","Meio","Fim"])} for k in configs]), hide_index=True)

with tabs[5]:
    com = [h for h in st.session_state.historico if h.get("ac") is not None]
    if com: st.line_chart(pd.DataFrame(com)["ac"])
    else: st.info("Registre acertos")

with tabs[6]:
    jb = st.number_input("Jogos",5,30,10)
    if st.button("Criar Bolão"):
        st.success(f"R$ {jb*cfg['preco']:.2f} total")

with tabs[7]:
    st.code("Lotofácil: 03-05-08-10-11-13-14-17-18-19-21-22-23-24-25")

with tabs[8]:
    if st.session_state.historico:
        for idx in range(len(st.session_state.historico)-1, max(-1,len(st.session_state.historico)-20), -1):
            h = st.session_state.historico[idx]
            c1,c2,c3 = st.columns([6,1,1])
            c1.text(f"{h['lot']} F{h['f']}%: {'-'.join(f'{n:02d}' for n in h['j'])}")
            if c3.button("x", key=f"d{idx}"):
                st.session_state.historico.pop(idx); st.rerun()
    else:
        st.info("Nenhum jogo")

with tabs[9]:
    j = st.text_input("Seu jogo")
    r = st.text_input("Resultado")
    if st.button("Conferir") and j and r:
        ac = len(set(map(int, j.split())) & set(map(int, r.split())))
        st.metric("Acertos", ac)

with tabs[10]:
    com = [h for h in st.session_state.historico if h.get("ac") is not None]
    if com: st.metric("Média", f"{sum(h['ac'] for h in com)/len(com):.1f}")
    else: st.info("Sem dados")

with tabs[11]:
    st.dataframe(pd.DataFrame([{"Loteria":k,"Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()]), hide_index=True)

with tabs[12]:
    if st.session_state.historico:
        df = pd.DataFrame(st.session_state.historico)
        df["Jogo"] = df["j"].apply(lambda x: "-".join(f"{n:02d}" for n in x))
        csv = df[["data","lot","f","p","Jogo"]].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV", csv, "lotoelite.csv", "text/csv")
    else:
        st.info("Salve jogos primeiro")
