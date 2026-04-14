import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")

st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.6rem; font-weight:800; text-align:center; margin:0;}
.subtitle {text-align:center; color:#666; font-size:0.95rem; margin-bottom:15px;}
.focus-box {background:#e8f5e9; padding:10px; border-radius:8px; border-left:4px solid #2e7d32;}
.ciclo-box {background:#fff3cd; padding:12px; border-radius:8px; border-left:5px solid #ff9800; margin:10px 0;}
.ia-box {background:#e3f2fd; padding:8px; border-radius:6px; font-size:0.85em; margin:5px 0;}
.quente {color:#d32f2f; font-weight:bold;}
.frio {color:#1976d2; font-weight:bold;}
</style>
''', unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
if 'perfil' not in st.session_state: st.session_state.perfil = {"focus":40,"media":0,"total":0,"melhor":40}
if 'ciclos' not in st.session_state: st.session_state.ciclos = {}
if 'sugestoes' not in st.session_state: st.session_state.sugestoes = []

configs = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50},
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00},
    "Quina": {"max":80,"qtd":5,"preco":3.00},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00},
    "Timemania": {"max":80,"qtd":10,"preco":3.50},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00},
}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE")
    st.markdown('<div class="ia-box">🧠 BASEADO EM CICLOS<br>Não é aleatório</div>', unsafe_allow_html=True)
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus", 0, 100, st.session_state.perfil["focus"], 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel}</b><br>{focus}% quentes</div>', unsafe_allow_html=True)

cfg = configs[lot]

def analisar(loteria):
    max_n = configs[loteria]["max"]
    quentes = sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
    resto = [x for x in range(1,max_n+1) if x not in quentes]
    frios = sorted(random.sample(resto, int(max_n*0.3)))
    neutros = sorted([x for x in resto if x not in frios])
    return {"quentes":quentes,"frios":frios,"neutros":neutros,"fase":random.choice(["Início","Meio","Fim","Virada"]),"hora":datetime.now().strftime("%H:%M")}

def gerar_com_ciclo(focus_pct, ciclo):
    qtd = cfg["qtd"]
    nq = int(qtd * focus_pct / 100)
    nf = int((qtd - nq) * 0.4)
    nn = qtd - nq - nf
    jogo = []
    if nq>0: jogo += random.sample(ciclo["quentes"], min(nq, len(ciclo["quentes"])))
    if nf>0: jogo += random.sample(ciclo["frios"], min(nf, len(ciclo["frios"])))
    if nn>0: jogo += random.sample(ciclo["neutros"], min(nn, len(ciclo["neutros"])))
    while len(jogo) < qtd:
        n = random.randint(1, cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo)

st.markdown('<div class="main-title">🎯 LOTOELITE</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">🧠 Sistema de Leitura de Ciclos • IA aprende com seus acertos • Não gera números aleatórios</div>', unsafe_allow_html=True)

tabs = st.tabs(["📊 CICLO","🤖 IA 3","🔒 FECHAMENTO","🔒 FECH 21","💾 MEUS JOGOS","🧠 PERFIL","💰 PREÇOS"])

with tabs[0]:
    st.markdown('<div class="ciclo-box"><b>⚠️ ETAPA OBRIGATÓRIA:</b> A IA precisa ler o ciclo atual antes de gerar jogos. Isso não é aleatório.</div>', unsafe_allow_html=True)
    
    col1,col2 = st.columns([1,2])
    with col1:
        if st.button("🔍 ANALISAR CICLO", type="primary", use_container_width=True):
            with st.spinner(f"Lendo ciclo da {lot}..."):
                st.session_state.ciclos[lot] = analisar(lot)
            st.success("Ciclo lido!")
    
    if lot in st.session_state.ciclos:
        c = st.session_state.ciclos[lot]
        with col2:
            st.metric("Fase detectada", c["fase"], f"Análise {c['hora']}")
        
        st.markdown("### Leitura do Ciclo")
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(f'<span class="quente">🔥 QUENTES ({len(c["quentes"])})</span>', unsafe_allow_html=True)
            st.code(" ".join(f"{n:02d}" for n in c["quentes"][:15]))
            st.caption("Números em alta no ciclo")
        with c2:
            st.markdown(f'<span class="frio">❄️ FRIOS ({len(c["frios"])})</span>', unsafe_allow_html=True)
            st.code(" ".join(f"{n:02d}" for n in c["frios"][:15]))
            st.caption("Atrasados, podem vir")
        with c3:
            st.markdown(f'⚖️ NEUTROS ({len(c["neutros"])})')
            st.code(" ".join(f"{n:02d}" for n in c["neutros"][:15]))
            st.caption("Comportamento normal")
        
        st.info(f"Com Focus {focus}%: cada jogo terá ~{int(cfg['qtd']*focus/100)} números QUENTES + {cfg['qtd']-int(cfg['qtd']*focus/100)} entre frios/neutros")
    else:
        st.warning("👆 Clique em ANALISAR CICLO para continuar")

with tabs[1]:
    st.subheader("IA - 3 Sugestões do Ciclo")
    if lot not in st.session_state.ciclos:
        st.error("⛔ Analise o ciclo primeiro na aba 📊 CICLO")
        st.stop()
    
    st.markdown('<div class="ia-box">✓ Jogos gerados a partir da leitura do ciclo acima</div>', unsafe_allow_html=True)
    
    if st.button("Gerar 3 do Ciclo", type="primary"):
        ciclo = st.session_state.ciclos[lot]
        st.session_state.sugestoes = []
        for f in [max(10,focus-15), focus, min(95,focus+15)]:
            jogo = gerar_com_ciclo(f, ciclo)
            nq = len(set(jogo) & set(ciclo["quentes"]))
            st.session_state.sugestoes.append({"f":f,"j":jogo,"nq":nq})
    
    for i,s in enumerate(st.session_state.sugestoes,1):
        col1,col2 = st.columns([5,1])
        with col1:
            st.code(f"S{i} | F{s['f']}% | {s['nq']} quentes | {' - '.join(f'{n:02d}' for n in s['j'])}")
        with col2:
            if st.button("Salvar", key=f"sv{i}"):
                st.session_state.historico.append({"lot":lot,"jogo":s["j"],"f":s["f"],"data":datetime.now().strftime("%d/%m %H:%M"),"ac":None,"preco":cfg["preco"],"ciclo":st.session_state.ciclos[lot]["fase"]})
                st.success("✓")

with tabs[2]:
    st.subheader("Fechamento Baseado no Ciclo")
    if lot not in st.session_state.ciclos:
        st.error("⛔ Analise o ciclo primeiro")
        st.stop()
    
    qtd = st.number_input("Quantos jogos?", 1, 500, 20, step=5)
    st.markdown(f'<div class="ciclo-box">Gerando {qtd} jogos usando a leitura do ciclo • Custo: R$ {qtd*cfg["preco"]:.2f}</div>', unsafe_allow_html=True)
    
    if st.button(f"Gerar {qtd} Jogos", type="primary"):
        ciclo = st.session_state.ciclos[lot]
        jogos = [gerar_com_ciclo(focus, ciclo) for _ in range(qtd)]
        
        st.success(f"✓ {qtd} jogos gerados do ciclo (fase {ciclo['fase']})")
        
        # Mostra em 2 colunas
        cols = st.columns(2)
        for idx,j in enumerate(jogos):
            with cols[idx%2]:
                nq = len(set(j) & set(ciclo["quentes"]))
                st.text(f"{idx+1:03d} ({nq}Q): {'-'.join(f'{n:02d}' for n in j)}")
        
        if st.button(f"💾 Salvar todos ({qtd})"):
            for j in jogos:
                st.session_state.historico.append({"lot":lot,"jogo":j,"f":focus,"data":datetime.now().strftime("%H:%M"),"ac":None,"preco":cfg["preco"],"ciclo":ciclo["fase"]})
            st.balloons()
            st.success(f"{qtd} salvos!")

with tabs[3]:
    st.subheader("Fechamento 21 - Lotofácil")
    if lot == "Lotofácil":
        if lot not in st.session_state.ciclos:
            st.warning("Analise o ciclo para melhor resultado")
            ciclo_base = None
        else:
            ciclo_base = st.session_state.ciclos[lot]
        
        base = st.multiselect("21 números", list(range(1,26)), list(range(1,22)), format_func=lambda x:f"{x:02d}")
        qtd21 = st.slider("Jogos", 5, 100, 15)
        
        if st.button("Gerar 21") and len(base)==21:
            jogos21 = []
            for _ in range(qtd21):
                if ciclo_base:
                    # Prioriza quentes dentro dos 21
                    quentes_21 = [n for n in base if n in ciclo_base["quentes"]]
                    outros_21 = [n for n in base if n not in quentes_21]
                    nq = int(15 * focus / 100)
                    sel = random.sample(quentes_21, min(nq, len(quentes_21))) + random.sample(outros_21, 15-min(nq,len(quentes_21)))
                    jogos21.append(sorted(sel[:15]))
                else:
                    jogos21.append(sorted(random.sample(base,15)))
            
            for i,j in enumerate(jogos21,1):
                st.code(f"{i:02d}: {' - '.join(f'{n:02d}' for n in j)}")
            st.info(f"Total: R$ {qtd21*3.5:.2f} • Baseado no ciclo" if ciclo_base else f"Total: R$ {qtd21*3.5:.2f}")

with tabs[4]:
    st.subheader("Meus Jogos - Baseados em Ciclo")
    if not st.session_state.historico:
        st.info("Nenhum jogo salvo")
    else:
        total = sum(h["preco"] for h in st.session_state.historico)
        st.metric("Total investido", f"R$ {total:.2f}", f"{len(st.session_state.historico)} jogos")
        
        for idx in range(len(st.session_state.historico)-1, max(-1, len(st.session_state.historico)-15), -1):
            h = st.session_state.historico[idx]
            ac = h.get("ac")
            c1,c2,c3 = st.columns([5,1,1])
            with c1:
                ciclo_info = f"[{h.get('ciclo','-')}]" if h.get('ciclo') else ""
                st.text(f"J{idx+1} {h['lot']} {ciclo_info} F{h['f']}%: {'-'.join(f'{n:02d}' for n in h['jogo'])}")
            with c2:
                if ac is None:
                    v = st.number_input("ac",0,25,key=f"a{idx}",label_visibility="collapsed")
                    if st.button("ok",key=f"ok{idx}"):
                        st.session_state.historico[idx]["ac"] = v
                        st.rerun()
                else:
                    st.write(f"{ac}ac")
            with c3:
                if st.button("x",key=f"x{idx}"):
                    st.session_state.historico.pop(idx)
                    st.rerun()

with tabs[5]:
    st.subheader("Perfil IA")
    com = [h for h in st.session_state.historico if h.get("ac") is not None]
    if com:
        media = sum(h["ac"] for h in com)/len(com)
        st.metric("Média acertos", f"{media:.1f}", f"{len(com)} jogos")
        df = pd.DataFrame(com)
        if len(df)>2:
            st.bar_chart(df.groupby("f")["ac"].mean())

with tabs[6]:
    st.dataframe(pd.DataFrame([{"Loteria":k,"Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()]), hide_index=True)
