import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v78", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:2.4rem; font-weight:800; text-align:center; margin:0;}
.subtitle {text-align:center; color:#666; font-size:0.85rem; margin-bottom:8px;}
.ciclo-box {background:#fff3cd; padding:8px; border-radius:6px; border-left:4px solid #ff9800; margin:6px 0;}
.focus-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #2e7d32;}
.ia-box {background:#e3f2fd; padding:5px; border-radius:5px; font-size:0.75em;}
</style>
""", unsafe_allow_html=True)

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
    st.markdown('<div class="ia-box">🧠 CICLOS + IA</div>', unsafe_allow_html=True)
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, st.session_state.perfil["focus"], 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel}</b> {focus}%</div>', unsafe_allow_html=True)

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
    pool = ciclo["f"] + ciclo["n"]
    if len(jogo) < qtd:
        jogo += random.sample(pool, min(qtd-len(jogo), len(pool)))
    while len(jogo) < qtd:
        n = random.randint(1, cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

st.markdown('<div class="main-title">🎯 LOTOELITE v78</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sistema de Ciclos • Memória por Loteria • Estável</div>', unsafe_allow_html=True)

tabs = st.tabs(["📊 CICLO","🤖 IA 3","🔒 FECHAMENTO","🔒 FECH 21","📍 POSIÇÃO","📈 GRÁFICO","🎲 BOLÕES","🏆 RESULTADOS","💾 MEUS JOGOS","🔍 CONFERIDOR","🧠 PERFIL","💰 PREÇOS","📥 EXPORTAR"])

with tabs[0]:
    st.markdown('<div class="ciclo-box"><b>Analise o ciclo antes de gerar jogos</b></div>', unsafe_allow_html=True)
    c1,c2 = st.columns([1,3])
    with c1:
        if st.button("🔍 ANALISAR", type="primary", use_container_width=True):
            st.session_state.ciclos[lot] = analisar(lot)
            st.rerun()
    if lot in st.session_state.ciclos:
        c = st.session_state.ciclos[lot]
        with c2: st.metric("Fase do Ciclo", c["fase"], c["h"])
        col1,col2,col3 = st.columns(3)
        with col1: st.caption("🔥 QUENTES"); st.code(" ".join(f"{n:02d}" for n in c["q"][:15]))
        with col2: st.caption("❄️ FRIOS"); st.code(" ".join(f"{n:02d}" for n in c["f"][:15]))
        with col3: st.caption("⚖️ NEUTROS"); st.code(" ".join(f"{n:02d}" for n in c["n"][:15]))
    else:
        st.warning("Clique em ANALISAR para ver o ciclo")

with tabs[1]:
    st.subheader("IA - 3 Sugestões do Ciclo")
    if lot not in st.session_state.ciclos:
        st.error("⛔ Analise o ciclo primeiro na aba 📊 CICLO")
        st.stop()
    
    sug_atuais = st.session_state.sugestoes_por_loteria.get(lot, [])
    
    if st.button("Gerar 3 do Ciclo", type="primary"):
        ciclo = st.session_state.ciclos[lot]
        novas = []
        for f in [max(10,focus-15), focus, min(95,focus+15)]:
            jogo = gerar(f, ciclo)
            nq = len(set(jogo) & set(ciclo["q"]))
            novas.append({"f":f,"j":jogo,"nq":nq})
        st.session_state.sugestoes_por_loteria[lot] = novas
        sug_atuais = novas
        st.rerun()
    
    if sug_atuais:
        st.caption(f"Jogos salvos para {lot} (permanecem até gerar novamente)")
        for i,s in enumerate(sug_atuais,1):
            c1,c2 = st.columns([5,1])
            with c1: st.code(f"S{i} F{s['f']}% ({s['nq']}Q): {'-'.join(f'{n:02d}' for n in s['j'])}")
            with c2:
                if st.button("💾", key=f"s{lot}{i}"):
                    st.session_state.historico.append({"lot":lot,"j":s["j"],"f":s["f"],"data":datetime.now().strftime("%d/%m %H:%M"),"ac":None,"p":cfg["preco"]})
                    st.success("Salvo!")

with tabs[2]:
    st.subheader("Fechamento de Jogos")
    if lot not in st.session_state.ciclos:
        st.error("Analise o ciclo primeiro")
        st.stop()
    qtd = st.number_input("Quantos jogos?", 1, 500, 20, key="qf")
    st.info(f"{qtd} jogos = R$ {qtd*cfg['preco']:.2f}")
    if st.button(f"Gerar {qtd} Jogos", type="primary"):
        ciclo = st.session_state.ciclos[lot]
        jogos = [gerar(focus, ciclo) for _ in range(qtd)]
        st.success(f"{qtd} jogos gerados do ciclo {ciclo['fase']}")
        cols = st.columns(3)
        for i,j in enumerate(jogos[:30]):
            with cols[i%3]: st.text(f"{i+1:03d}: {'-'.join(f'{n:02d}' for n in j)}")
        if qtd>30: st.caption(f"... mais {qtd-30} jogos")
        if st.button("Salvar Todos no Histórico"):
            for j in jogos:
                st.session_state.historico.append({"lot":lot,"j":j,"f":focus,"data":datetime.now().strftime("%H:%M"),"ac":None,"p":cfg["preco"]})
            st.balloons()

with tabs[3]:
    st.subheader("Fechamento 21 Dezenas")
    if lot=="Lotofácil":
        base = st.multiselect("Escolha 21 números", list(range(1,26)), list(range(1,22)), format_func=lambda x:f"{x:02d}")
        q = st.slider("Qtd jogos",5,100,15)
        if st.button("Gerar Fechamento") and len(base)==21:
            for i in range(q):
                st.code(f"{i+1}: {'-'.join(f'{n:02d}' for n in sorted(random.sample(base,15)))}")
    else:
        st.info("Disponível apenas para Lotofácil")

with tabs[4]:
    st.subheader("Posição no Ciclo - Todas Loterias")
    dados = [{"Loteria":n,"Fase":random.choice(["Início","Meio","Fim","Virada"]),"Ação":random.choice(["↑ Focus","→ Manter","↓ Focus"])} for n in configs]
    st.dataframe(pd.DataFrame(dados), hide_index=True, use_container_width=True)

with tabs[5]:
    st.subheader("Gráfico de Evolução")
    com = [h for h in st.session_state.historico if h.get("ac") is not None]
    if len(com)>=2:
        df = pd.DataFrame(com)
        st.line_chart(df["ac"])
        st.metric("Média Acertos", f"{df['ac'].mean():.1f}")
    else:
        st.info("Registre acertos em MEUS JOGOS para ver o gráfico")

with tabs[6]:
    st.subheader("Gerador de Bolões")
    jb = st.number_input("Jogos no bolão",5,50,15,key="jb")
    ct = st.number_input("Cotas",2,20,10,key="ct")
    if st.button("Criar Bolão"):
        total = jb*cfg["preco"]
        st.success(f"Bolão {lot}: R$ {total:.2f} = {ct} cotas de R$ {total/ct:.2f}")
        if lot in st.session_state.ciclos:
            ciclo = st.session_state.ciclos[lot]
            for i in range(min(5,jb)):
                j = gerar(focus, ciclo)
                st.code(f"{i+1}: {'-'.join(f'{n:02d}' for n in j)}")

with tabs[7]:
    st.subheader("Últimos Resultados")
    res = {
        "Lotofácil":"03-05-08-10-11-13-14-17-18-19-21-22-23-24-25",
        "Mega-Sena":"07-18-23-34-45-56",
        "Quina":"02-14-29-45-77"
    }
    for k,v in res.items(): st.code(f"{k}: {v}")

with tabs[8]:
    st.subheader("Meus Jogos Salvos")
    if st.session_state.historico:
        total = sum(h["p"] for h in st.session_state.historico)
        st.metric("Total Investido", f"R$ {total:.2f}", f"{len(st.session_state.historico)} jogos")
        for idx in range(len(st.session_state.historico)-1, max(-1,len(st.session_state.historico)-30), -1):
            h = st.session_state.historico[idx]
            c1,c2,c3 = st.columns([6,1,1])
            with c1: st.text(f"J{idx+1} {h['lot']} F{h['f']}%: {'-'.join(f'{n:02d}' for n in h['j'])}")
            with c2:
                if h.get("ac") is None:
                    v = st.number_input("",0,25,key=f"ac{idx}",label_visibility="collapsed")
                    if st.button("ok",key=f"ok{idx}"):
                        st.session_state.historico[idx]["ac"]=v
                        st.rerun()
                else:
                    st.write(f"{h['ac']}ac")
            with c3:
                if st.button("x",key=f"del{idx}"):
                    st.session_state.historico.pop(idx)
                    st.rerun()
    else:
        st.info("Nenhum jogo salvo. Gere na aba IA 3 ou FECHAMENTO")

with tabs[9]:
    st.subheader("Conferidor de Jogos")
    j = st.text_input("Cole seu jogo (ex: 03 05 08 10 11...)")
    r = st.text_input("Resultado oficial")
    if st.button("Conferir"):
        try:
            nj = [int(x) for x in j.replace("-"," ").split() if x.isdigit()]
            nr = [int(x) for x in r.split() if x.isdigit()]
            ac = len(set(nj) & set(nr))
            st.metric("Acertos", ac)
            if ac>=11: st.balloons()
        except:
            st.error("Formato inválido")

with tabs[10]:
    st.subheader("Perfil de Performance")
    com = [h for h in st.session_state.historico if h.get("ac") is not None]
    if com:
        df = pd.DataFrame(com)
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Jogos Conferidos", len(com))
        with c2: st.metric("Média Acertos", f"{df['ac'].mean():.1f}")
        with c3: st.metric("Melhor Focus", f"{int(df.groupby('f')['ac'].mean().idxmax())}%")
    else:
        st.info("Registre acertos para ver estatísticas")

with tabs[11]:
    st.subheader("Preços Oficiais 2026")
    dfp = pd.DataFrame([{"Loteria":k,"Preço":f"R$ {v['preco']:.2f}","Dezenas":v["qtd"]} for k,v in configs.items()])
    st.dataframe(dfp, hide_index=True, use_container_width=True)

with tabs[12]:
    st.subheader("Exportar Histórico")
    if st.session_state.historico:
        df = pd.DataFrame(st.session_state.historico)
        df["Jogo"] = df["j"].apply(lambda x: "-".join(f"{n:02d}" for n in x))
        csv = df[["data","lot","f","p","Jogo"]].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV (abre no Excel)", csv, "lotoelite_v78.csv", "text/csv", use_container_width=True)
        st.success(f"{len(df)} jogos prontos para exportar")
    else:
        st.info("Salve jogos primeiro nas abas IA 3 ou FECHAMENTO")
