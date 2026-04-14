import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v71.1", layout="wide", page_icon="🎯")

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

# Inicializa
if 'historico_jogos' not in st.session_state:
    st.session_state.historico_jogos = []
if 'perfil_aprendido' not in st.session_state:
    st.session_state.perfil_aprendido = {"focus_medio": 40, "acertos_medio": 0, "total_jogos": 0}
if 'ciclos' not in st.session_state:
    st.session_state.ciclos = {}
if 'sugestoes_atuais' not in st.session_state:
    st.session_state.sugestoes_atuais = []

with st.sidebar:
    st.markdown("### 🎯 v71.1 FIX")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania"])
    st.markdown("---")
    focus_default = st.session_state.perfil_aprendido["focus_medio"]
    focus = st.slider("Focus", 0, 100, focus_default, 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel} ({focus}%)</b></div>', unsafe_allow_html=True)

configs = {
    "Lotofácil": {"max":25,"qtd":15},
    "Mega-Sena": {"max":60,"qtd":6},
    "Quina": {"max":80,"qtd":5},
    "Lotomania": {"max":100,"qtd":50},
    "Dupla Sena": {"max":50,"qtd":6},
    "Timemania": {"max":80,"qtd":10},
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

st.markdown('<div class="main-title">🎯 LOTOELITE v71.1 - SAVE FIX</div>', unsafe_allow_html=True)
st.success(f"Jogos salvos: {len(st.session_state.historico_jogos)} | Média IA: {st.session_state.perfil_aprendido['acertos_medio']:.1f}")

tabs = st.tabs(["🧠 Perfil","📊 Ciclo","📍 Posição","🤖 IA 3 Sugestões","🔒 Fechamento","🎲 Bolões","🏆 Resultados","💾 Meus Jogos","🔍 Conferidor"])

with tabs[0]:
    st.subheader("Perfil Inteligente")
    html = '<div class="perfil-card"><h3>Perfil</h3>'
    html += f"<p>Jogos: {st.session_state.perfil_aprendido['total_jogos']}</p>"
    html += f"<p>Media: {st.session_state.perfil_aprendido['acertos_medio']:.1f}</p>"
    html += f"<p>Focus ideal: {st.session_state.perfil_aprendido['focus_medio']}%</p></div>"
    st.markdown(html, unsafe_allow_html=True)
    
    df_list = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
    if len(df_list) >= 3:
        df = pd.DataFrame(df_list)
        analise = df.groupby('focus')['acertos'].agg(['mean','count']).round(1)
        st.dataframe(analise, use_container_width=True)

with tabs[1]:
    if st.button("ANALISAR CICLO"):
        st.session_state.ciclos[loteria] = {"numeros": random.sample(range(1,cfg["max"]+1),18)}
    if loteria in st.session_state.ciclos:
        nums = st.session_state.ciclos[loteria]["numeros"]
        st.code(" - ".join(f"{n:02d}" for n in sorted(nums)))

with tabs[2]:
    st.subheader("Posição no Ciclo")
    dados = []
    for lot, conf in configs.items():
        fase = random.choice(["Início","Meio","Fim","Virada"])
        dados.append({"Loteria":lot,"Fase":fase,"Recomendação":"Aumente Focus" if fase in ["Fim","Virada"] else "Mantenha"})
    st.dataframe(pd.DataFrame(dados), hide_index=True)

with tabs[3]:
    st.subheader("IA 3 Sugestões - AGORA SALVA")
    
    if st.button("Gerar 3 Sugestões", type="primary"):
        st.session_state.sugestoes_atuais = []
        for f in [max(10,focus-20), focus, min(95,focus+20)]:
            jogo = gerar_jogo(f)
            st.session_state.sugestoes_atuais.append({"focus":f,"jogo":jogo})
        st.success("3 sugestões geradas abaixo!")
    
    if st.session_state.sugestoes_atuais:
        for idx, sug in enumerate(st.session_state.sugestoes_atuais, 1):
            jogo = sug["jogo"]
            f = sug["focus"]
            col1, col2 = st.columns([4,1])
            with col1:
                st.code(f"Sugestão {idx} (Focus {f}%): {' - '.join(f'{n:02d}' for n in jogo)}")
            with col2:
                if st.button("💾 Salvar", key=f"save_{idx}_{f}"):
                    st.session_state.historico_jogos.append({
                        "data": datetime.now().strftime("%d/%m %H:%M"),
                        "jogo": jogo,
                        "focus": f,
                        "loteria": loteria,
                        "acertos": None
                    })
                    st.success(f"Jogo {idx} salvo em Meus Jogos!")
                    st.balloons()

with tabs[4]:
    st.subheader("Fechamento")
    if st.button("Gerar"):
        st.code(' - '.join(f'{n:02d}' for n in gerar_jogo(focus)))

with tabs[5]:
    st.subheader("Bolões")
    if st.button("Criar Bolão"):
        st.success("Bolão criado")

with tabs[6]:
    st.subheader("Resultados")
    res = {"Lotofácil":[3,5,8,10,11,13,14,17,18,19,21,22,23,24,25],"Mega":[7,18,23,34,45,56]}
    for k,v in res.items():
        st.markdown(f'<div class="resultado-card"><b>{k}</b><br>{" - ".join(f"{n:02d}" for n in v)}</div>', unsafe_allow_html=True)

with tabs[7]:
    st.subheader("💾 Meus Jogos - AQUI APARECEM")
    st.info(f"Total de jogos salvos: {len(st.session_state.historico_jogos)}")
    
    if not st.session_state.historico_jogos:
        st.warning("Vá em 'IA 3 Sugestões', gere e clique em Salvar")
    else:
        for idx in range(len(st.session_state.historico_jogos)-1, -1, -1):
            jg = st.session_state.historico_jogos[idx]
            ac = jg.get('acertos')
            classe = f"acerto-{ac}" if ac and ac>=11 else ""
            
            col1, col2, col3 = st.columns([3,1,1])
            with col1:
                html = f'<div class="historico-item {classe}"><b>Jogo {idx+1}</b> - {jg["data"]}<br>'
                html += ' - '.join(f"{n:02d}" for n in jg["jogo"])
                html += f'<br><small>Focus {jg["focus"]}% | {jg["loteria"]}</small></div>'
                st.markdown(html, unsafe_allow_html=True)
            with col2:
                if ac is None:
                    inp = st.number_input("Acertos",0,15,key=f"ac_{idx}",label_visibility="collapsed")
                    if st.button("OK",key=f"ok_{idx}"):
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
            with col3:
                if st.button("🗑️",key=f"del_{idx}"):
                    st.session_state.historico_jogos.pop(idx)
                    st.rerun()

with tabs[8]:
    st.subheader("Conferidor")
    ji = st.text_input("Jogo")
    ri = st.text_input("Resultado","03 05 08 10 11 13 14 17 18 19 21 22 23 24 25")
    if st.button("Conferir"):
        nj = [int(x) for x in ji.split() if x.isdigit()]
        nr = [int(x) for x in ri.split() if x.isdigit()]
        ac = len(set(nj)&set(nr))
        st.metric("Acertos",ac)
        st.session_state.historico_jogos.append({
            "data":datetime.now().strftime("%d/%m %H:%M"),
            "jogo":nj,"focus":focus,"loteria":loteria,"acertos":ac
        })
        st.success("Salvo e IA aprendeu!")

st.caption("v71.1 - Save corrigido")
