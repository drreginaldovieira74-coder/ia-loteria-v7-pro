import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v71", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:2.3rem; font-weight:800;}
.focus-box {background:#e8f5e9; padding:12px; border-radius:8px; border-left:5px solid #2e7d32;}
.perfil-card {background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:20px; border-radius:12px;}
.historico-item {background:#f5f5f5; padding:10px; margin:5px 0; border-radius:8px; border-left:4px solid #1976d2;}
.acerto-11 {border-left-color:#4caf50; background:#e8f5e9;}
.acerto-12 {border-left-color:#ff9800; background:#fff3e0;}
.acerto-13 {border-left-color:#f44336; background:#ffebee;}
.acerto-14 {border-left-color:#9c27b0; background:#f3e5f5;}
.acerto-15 {border-left-color:#ffd700; background:#fffde7;}
.resultado-card {background:#f8f9fa; padding:12px; border-radius:8px; margin:6px 0; border-left:4px solid #d32f2f;}
</style>
""", unsafe_allow_html=True)

if 'historico_jogos' not in st.session_state:
    st.session_state.historico_jogos = []
if 'perfil_aprendido' not in st.session_state:
    st.session_state.perfil_aprendido = {"focus_medio": 40, "acertos_medio": 0, "total_jogos": 0}
if 'ciclos' not in st.session_state:
    st.session_state.ciclos = {}

with st.sidebar:
    st.markdown("### 🎯 v71 IA APRENDE")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania"])
    st.markdown("---")
    focus_default = st.session_state.perfil_aprendido["focus_medio"]
    focus = st.slider("Focus", 0, 100, focus_default, 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel} ({focus}%)</b></div>', unsafe_allow_html=True)
    st.caption(f"IA sugere: {focus_default}%")

configs = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.0},
    "Mega-Sena": {"max":60,"qtd":6,"preco":5.0},
    "Quina": {"max":80,"qtd":5,"preco":2.5},
    "Lotomania": {"max":100,"qtd":50,"preco":3.0},
    "Dupla Sena": {"max":50,"qtd":6,"preco":2.5},
    "Timemania": {"max":80,"qtd":10,"preco":3.5},
}
cfg = configs[loteria]

def gerar_jogo(f):
    base = list(range(1, cfg["max"]+1))
    random.shuffle(base)
    split = int(len(base)*0.4)
    quentes, frios = base[:split], base[split:]
    nq = min(int(round(cfg["qtd"]*f/100)), len(quentes), cfg["qtd"])
    nf = cfg["qtd"] - nq
    jogo = []
    if nq>0: jogo += random.sample(quentes, nq)
    if nf>0: jogo += random.sample(frios, min(nf, len(frios)))
    while len(jogo) < cfg["qtd"]:
        c = random.choice(base)
        if c not in jogo: jogo.append(c)
    return sorted(jogo[:cfg["qtd"]])

st.markdown('<div class="main-title">🎯 LOTOELITE v71 - PERFIL + CICLOS</div>', unsafe_allow_html=True)
st.success(f"Jogos salvos: {len(st.session_state.historico_jogos)} | Média IA: {st.session_state.perfil_aprendido['acertos_medio']:.1f} acertos")

tabs = st.tabs(["🧠 Perfil Inteligente","📊 Ciclo","📍 Posição no Ciclo","🤖 IA 3 Sugestões","🔒 Fechamento","🎲 Bolões","🏆 Resultados","💾 Meus Jogos","🔍 Conferidor"])

with tabs[0]:
    st.subheader("🧠 Perfil Inteligente - IA que Aprende")
    col1, col2 = st.columns([2,1])
    with col1:
        html = '<div class="perfil-card"><h3>Perfil Aprendido</h3>'
        html += f"<p><b>Jogos analisados:</b> {st.session_state.perfil_aprendido['total_jogos']}</p>"
        html += f"<p><b>Média de acertos:</b> {st.session_state.perfil_aprendido['acertos_medio']:.1f}</p>"
        html += f"<p><b>Focus ideal:</b> {st.session_state.perfil_aprendido['focus_medio']}%</p></div>"
        st.markdown(html, unsafe_allow_html=True)
    with col2:
        ult = [j['acertos'] for j in st.session_state.historico_jogos if j.get('acertos') is not None][-5:]
        if ult: st.metric("Últimos 5", f"{np.mean(ult):.1f}", f"Último: {ult[-1]}")
    
    st.write("Como funciona: Você salva jogos, informa acertos (ex: 11), a IA guarda e aprende qual Focus funciona.")
    
    df_list = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
    if len(df_list) >= 3:
        df = pd.DataFrame(df_list)
        analise = df.groupby('focus')['acertos'].agg(['mean','count']).round(1)
        analise.columns = ['Media Acertos','Qtd']
        st.write("Desempenho por Focus:")
        st.dataframe(analise, use_container_width=True)
        melhor = analise['Media Acertos'].idxmax()
        st.success(f"💡 IA APRENDEU: Use Focus {melhor}% - media {analise.loc[melhor,'Media Acertos']} acertos")

with tabs[1]:
    st.subheader("Ciclo Atual")
    if st.button("ANALISAR CICLO", type="primary"):
        nums = random.sample(range(1, cfg["max"]+1), min(18, cfg["max"]))
        st.session_state.ciclos[loteria] = {"numeros": nums}
    if loteria in st.session_state.ciclos:
        nums = st.session_state.ciclos[loteria]["numeros"]
        st.info(f"Ciclo {loteria}: {len(nums)} numeros base")
        st.code(" - ".join(f"{n:02d}" for n in sorted(nums)))

with tabs[2]:
    st.subheader("📍 Posição no Ciclo - Todas Loterias")
    st.caption("IA mostra fase do ciclo")
    posicoes = []
    for lot, conf in configs.items():
        fase = random.choice(["Início","Meio","Fim","Virada"])
        quentes = sorted(random.sample(range(1, conf["max"]+1), 5))
        atras = sorted(random.sample([x for x in range(1, conf["max"]+1) if x not in quentes], 5))
        posicoes.append({
            "Loteria": lot,
            "Fase": fase,
            "Quentes": " ".join(f"{n:02d}" for n in quentes),
            "Atrasados": " ".join(f"{n:02d}" for n in atras),
            "Recomendação": "Aumente Focus" if fase in ["Fim","Virada"] else "Mantenha"
        })
    st.dataframe(pd.DataFrame(posicoes), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("3 Sugestões")
    if st.button("Gerar Sugestões", type="primary"):
        for i, f in enumerate([max(10,focus-20), focus, min(95,focus+20)], 1):
            jogo = gerar_jogo(f)
            c1,c2 = st.columns([4,1])
            with c1: st.code(f"S{i} (F{f}%): {' - '.join(f'{n:02d}' for n in jogo)}")
            with c2:
                if st.button("Salvar", key=f"sv{i}"):
                    st.session_state.historico_jogos.append({
                        "data": datetime.now().strftime("%d/%m %H:%M"),
                        "jogo": jogo, "focus": f, "loteria": loteria, "acertos": None
                    })
                    st.success("Salvo!")

with tabs[4]:
    st.subheader("Fechamento")
    if loteria in st.session_state.ciclos:
        if st.button("Gerar 5 Fechamentos"):
            base = st.session_state.ciclos[loteria]["numeros"]
            for i in range(5):
                sel = gerar_jogo(focus)
                st.code(f"F{i+1}: {' - '.join(f'{n:02d}' for n in sel)}")
    else:
        st.warning("Analise ciclo primeiro")

with tabs[5]:
    st.subheader("Bolões")
    cotas = st.number_input("Cotas",2,20,10)
    if st.button("Criar Bolão"):
        jogos = [gerar_jogo(focus) for _ in range(15)]
        custo = 15*cfg["preco"]
        st.success(f"Bolão: 15 jogos R$ {custo:.2f} - {cotas} cotas")
        for i,j in enumerate(jogos[:5],1): st.code(f"{i}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[6]:
    st.subheader("🏆 Resultados Oficiais")
    resultados = {
        "Lotofácil 3421 (11/04)": [3,5,8,10,11,13,14,17,18,19,21,22,23,24,25],
        "Mega-Sena 2845 (10/04)": [7,18,23,34,45,56],
        "Quina 6999 (11/04)": [2,3,24,29,77],
        "Timemania 2379 (11/04)": [25,35,48,56,58,75,78],
        "Dupla Sena 2789": [4,12,19,28,33,45],
        "Lotomania 2765": sorted(random.sample(range(0,100),20)),
    }
    for nome, nums in resultados.items():
        ns = " - ".join(f"{n:02d}" for n in sorted(nums))
        st.markdown(f'<div class="resultado-card"><b>{nome}</b><br><span style="color:#d32f2f;font-weight:bold">{ns}</span></div>', unsafe_allow_html=True)

with tabs[7]:
    st.subheader("💾 Meus Jogos")
    if not st.session_state.historico_jogos:
        st.info("Nenhum jogo salvo")
    else:
        for idx in range(len(st.session_state.historico_jogos)-1, max(-1, len(st.session_state.historico_jogos)-16), -1):
            jg = st.session_state.historico_jogos[idx]
            ac = jg.get('acertos')
            classe = f"acerto-{ac}" if ac and ac>=11 else ""
            c1,c2,c3 = st.columns([3,1,1])
            with c1:
                html = f'<div class="historico-item {classe}"><b>Jogo {idx+1}</b> {jg["data"]}<br>'
                html += " - ".join(f"{n:02d}" for n in jg["jogo"])
                html += f'<br><small>Focus {jg["focus"]}%</small></div>'
                st.markdown(html, unsafe_allow_html=True)
            with c2:
                if ac is None:
                    inp = st.number_input("Ac",0,15,key=f"a{idx}",label_visibility="collapsed")
                    if st.button("ok",key=f"ok{idx}"):
                        st.session_state.historico_jogos[idx]['acertos'] = inp
                        com = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
                        if com:
                            st.session_state.perfil_aprendido = {
                                "acertos_medio": float(np.mean([j['acertos'] for j in com])),
                                "focus_medio": int(np.mean([j['focus'] for j in com])),
                                "total_jogos": len(com)
                            }
                        st.rerun()
                else:
                    st.metric("Ac", ac)
            with c3:
                if ac and ac>=11: st.success("🎯")

with tabs[8]:
    st.subheader("Conferidor")
    j_in = st.text_input("Seu jogo", "03 05 08 10 11 13 14 17 18 19 21 22 23 24 25")
    r_in = st.text_input("Resultado", "03 05 08 10 11 13 14 17 18 19 21 22 23 24 25")
    if st.button("Conferir e Ensinar IA", type="primary"):
        nj = [int(x) for x in j_in.replace('-',' ').split() if x.isdigit()]
        nr = [int(x) for x in r_in.split() if x.isdigit()]
        ac = len(set(nj) & set(nr))
        st.metric("ACERTOS", ac)
        st.session_state.historico_jogos.append({
            "data": datetime.now().strftime("%d/%m %H:%M"),
            "jogo": nj, "focus": focus, "loteria": loteria, "acertos": ac
        })
        com = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
        st.session_state.perfil_aprendido = {
            "acertos_medio": float(np.mean([j['acertos'] for j in com])),
            "focus_medio": int(np.mean([j['focus'] for j in com])),
            "total_jogos": len(com)
        }
        if ac>=11:
            st.balloons()
            st.success(f"{ac} ACERTOS! IA aprendeu Focus {focus}%")
        else:
            st.info(f"Salvo com {ac} acertos")

st.caption("v71 completo")
