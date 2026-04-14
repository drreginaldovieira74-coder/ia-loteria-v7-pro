import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import io

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")

st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.6rem; font-weight:800; text-align:center;}
.focus-box {background:#e8f5e9; padding:12px; border-radius:8px; border-left:5px solid #2e7d32;}
</style>
''', unsafe_allow_html=True)

if 'historico_jogos' not in st.session_state:
    st.session_state.historico_jogos = []
if 'perfil_aprendido' not in st.session_state:
    st.session_state.perfil_aprendido = {"focus_medio": 40, "acertos_medio": 0, "total_jogos": 0, "melhor_focus": 40}
if 'ciclos' not in st.session_state:
    st.session_state.ciclos = {}
if 'sugestoes_atuais' not in st.session_state:
    st.session_state.sugestoes_atuais = []

configs = {
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00},
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50},
    "Quina": {"max":80,"qtd":5,"preco":3.00},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00},
    "Timemania": {"max":80,"qtd":10,"preco":3.50},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50},
    "Super Sete": {"max":9,"qtd":7,"preco":3.00},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00},
    "Loteca": {"max":14,"qtd":14,"preco":4.00},
}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE")
    loteria = st.selectbox("Loteria", list(configs.keys()), index=1)
    focus = st.slider("Focus", 0, 100, st.session_state.perfil_aprendido["focus_medio"], 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel} ({focus}%)</b></div>', unsafe_allow_html=True)

cfg = configs[loteria]

def gerar_jogo():
    return sorted(random.sample(range(1, cfg["max"]+1), cfg["qtd"]))

st.markdown('<div class="main-title">🎯 LOTOELITE</div>', unsafe_allow_html=True)
st.caption(f"{loteria} • R$ {cfg['preco']:.2f}")

tabs = st.tabs(["🧠 Perfil","📊 Gráfico","💰 Preços","📊 Ciclo","📍 Posição","🤖 IA 3","🔒 Fechamento","🔒 Fech 21","🎲 Bolões","🏆 Resultados","💾 Meus Jogos","🔍 Conferidor","📥 Exportar"])

with tabs[0]:
    c1,c2 = st.columns(2)
    with c1:
        st.metric("Jogos analisados", st.session_state.perfil_aprendido['total_jogos'])
        st.metric("Média acertos", f"{st.session_state.perfil_aprendido['acertos_medio']:.1f}")

with tabs[5]:
    if st.button("Gerar 3 Sugestões", type="primary"):
        st.session_state.sugestoes_atuais = [{"focus":f,"jogo":gerar_jogo()} for f in [max(10,focus-20),focus,min(95,focus+20)]]
    for i,s in enumerate(st.session_state.sugestoes_atuais,1):
        c1,c2 = st.columns([5,1])
        with c1: st.code(f"S{i} F{s['focus']}%: {' - '.join(f'{n:02d}' for n in s['jogo'])}")
        with c2:
            if st.button("💾", key=f"s{i}"):
                st.session_state.historico_jogos.append({"data":datetime.now().strftime("%d/%m %H:%M"),"jogo":s["jogo"],"focus":s["focus"],"loteria":loteria,"acertos":None,"preco":cfg["preco"]})

with tabs[6]:
    st.subheader("🔒 Fechamento Inteligente - QUANTIDADE LIVRE")
    st.caption("Agora você escolhe quantos jogos quer gerar para qualquer loteria")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        qtd_fechamento = st.number_input("Quantos jogos?", min_value=1, max_value=500, value=10, step=1, key="qtd_fech")
    with col2:
        usar_ciclo = st.checkbox("Usar números do Ciclo", value=False)
    with col3:
        st.metric("Custo total", f"R$ {qtd_fechamento * cfg['preco']:.2f}")
    
    if st.button("Gerar Fechamento", type="primary", key="btn_fech"):
        jogos_gerados = []
        
        # Se usar ciclo e tiver ciclo analisado
        base_numeros = None
        if usar_ciclo and loteria in st.session_state.ciclos:
            base_numeros = st.session_state.ciclos[loteria]
            st.info(f"Usando {len(base_numeros)} números do Ciclo como base")
        
        progress = st.progress(0)
        for i in range(qtd_fechamento):
            if base_numeros:
                # Gera priorizando números do ciclo
                n_base = int(cfg["qtd"] * focus / 100)
                sel_base = random.sample(base_numeros, min(n_base, len(base_numeros)))
                resto = [x for x in range(1, cfg["max"]+1) if x not in sel_base]
                sel_resto = random.sample(resto, cfg["qtd"] - len(sel_base))
                jogo = sorted(sel_base + sel_resto)
            else:
                jogo = gerar_jogo()
            
            jogos_gerados.append(jogo)
            progress.progress((i+1)/qtd_fechamento)
        
        st.success(f"{qtd_fechamento} jogos gerados para {loteria}!")
        
        # Mostra os jogos em colunas para economizar espaço
        cols = st.columns(2)
        for idx, jogo in enumerate(jogos_gerados):
            col_idx = idx % 2
            with cols[col_idx]:
                st.code(f"J{idx+1:03d}: {' - '.join(f'{n:02d}' for n in jogo)}")
        
        # Botão para salvar todos
        if st.button(f"💾 Salvar todos os {qtd_fechamento} jogos no histórico", key="save_all"):
            for jogo in jogos_gerados:
                st.session_state.historico_jogos.append({
                    "data": datetime.now().strftime("%d/%m %H:%M"),
                    "jogo": jogo, "focus": focus, "loteria": loteria,
                    "acertos": None, "preco": cfg["preco"]
                })
            st.balloons()
            st.success(f"{qtd_fechamento} jogos salvos em Meus Jogos!")

with tabs[7]:
    st.subheader("Fechamento 21")
    if loteria=="Lotofácil":
        base = st.multiselect("21 números", list(range(1,26)), list(range(1,22)), format_func=lambda x:f"{x:02d}")
        qtd = st.slider("Jogos",5,100,10)
        if st.button("Gerar Fech 21") and len(base)==21:
            for i in range(qtd):
                j = sorted(random.sample(base,15))
                st.code(f"J{i+1}: {' - '.join(f'{n:02d}' for n in j)}")
            st.success(f"Total R$ {qtd*3.5:.2f}")

# Outras abas simplificadas para focar no fechamento
with tabs[1]:
    df_l = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
    if len(df_l)>=2: st.line_chart(pd.DataFrame(df_l)['acertos'])

with tabs[2]:
    st.dataframe(pd.DataFrame([{"Loteria":k, "Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()]), hide_index=True)

with tabs[3]:
    if st.button("ANALISAR CICLO"): st.session_state.ciclos[loteria] = random.sample(range(1,cfg["max"]+1), 18)
    if loteria in st.session_state.ciclos: st.code(" - ".join(f"{n:02d}" for n in sorted(st.session_state.ciclos[loteria])))

with tabs[4]:
    st.dataframe(pd.DataFrame([{"Loteria":n, "Fase":random.choice(["Início","Meio","Fim"])} for n in configs]), hide_index=True)

with tabs[8]:
    jogos = st.number_input("Jogos bolão",5,100,15)
    if st.button("Criar Bolão"): st.info(f"{jogos} jogos = R$ {jogos*cfg['preco']:.2f}")

with tabs[9]:
    st.code("Lotofácil: 03-05-08-10-11-13-14-17-18-19-21-22-23-24-25")

with tabs[10]:
    for idx in range(len(st.session_state.historico_jogos)-1, max(-1,len(st.session_state.historico_jogos)-5), -1):
        jg = st.session_state.historico_jogos[idx]
        st.code(f"J{idx+1}: {' - '.join(f'{n:02d}' for n in jg['jogo'])}")

with tabs[11]:
    j = st.text_input("Jogo")
    r = st.text_input("Resultado")
    if st.button("Conferir"):
        ac = len(set([int(x) for x in j.split() if x.isdigit()]) & set([int(x) for x in r.split() if x.isdigit()]))
        st.metric("Acertos", ac)

with tabs[12]:
    if st.session_state.historico_jogos:
        df = pd.DataFrame(st.session_state.historico_jogos)
        out = io.BytesIO()
        df.to_excel(out, index=False)
        st.download_button("Baixar", out.getvalue(), "lotoelite.xlsx")
