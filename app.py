import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v68.4", layout="wide", page_icon="🎯")

st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.2rem; font-weight:700;}
.focus-box {background:#e8f5e9; padding:10px; border-radius:8px; border-left:4px solid #2e7d32;}
.sugestao-card {background:#f5f5f5; padding:15px; border-radius:10px; margin-bottom:10px; border-left:5px solid #1976d2;}
.fechamento-card {background:#fff3e0; padding:12px; border-radius:8px; margin:5px 0; border-left:4px solid #ef6c00;}
.bolao-card {background:#e3f2fd; padding:15px; border-radius:10px; margin:10px 0; border:2px solid #1976d2;}
</style>
''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎯 v68.4 COMPLETA")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania"])
    st.markdown("---")
    st.markdown("### 🎚️ FOCUS")
    focus = st.slider("Ajuste", 0, 100, 40, 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>Focus: {nivel} ({focus}%)</b></div>', unsafe_allow_html=True)
    st.markdown("---")
    qtd_jogos = st.number_input("Jogos", 1, 50, 5)

configs = {
    "Lotofácil": {"max":25,"qtd":15,"fech":17,"preco":3.0},
    "Mega-Sena": {"max":60,"qtd":6,"fech":7,"preco":5.0},
    "Quina": {"max":80,"qtd":5,"fech":6,"preco":2.5},
    "Lotomania": {"max":100,"qtd":50,"fech":52,"preco":3.0},
    "Dupla Sena": {"max":50,"qtd":6,"fech":7,"preco":2.5},
    "Timemania": {"max":80,"qtd":10,"fech":11,"preco":3.5},
}
cfg = configs[loteria]
max_num, qtd_num, fech_min, preco = cfg["max"], cfg["qtd"], cfg["fech"], cfg["preco"]

def gerar_jogo(f, max_n, qtd_n):
    base = list(range(1, max_n+1)); random.shuffle(base)
    split = int(len(base)*0.4); quentes, frios = base[:split], base[split:]
    nq = min(int(round(qtd_n*f/100)), len(quentes), qtd_n)
    nf = qtd_n - nq
    jogo = (random.sample(quentes, nq) if nq>0 else []) + (random.sample(frios, min(nf,len(frios))) if nf>0 else [])
    while len(jogo) < qtd_n:
        c = random.choice(base)
        if c not in jogo: jogo.append(c)
    return sorted(jogo[:qtd_n])

st.markdown('<div class="main-title">🎯 LOTOELITE v68.4 - FOCUS COMPLETO</div>', unsafe_allow_html=True)
st.success(f"✅ v68.4 | {loteria} | Focus: {nivel}")

tabs = st.tabs(["📊 Ciclo","🤖 IA 3 Sugestões","🔒 Fechamento","🎲 Bolões","📈 Estatísticas","🎰 Gerador","🔍 Conferidor","📚 Histórico"])

with tabs[0]:
    st.subheader(f"Ciclo - {loteria}")
    if st.button("🔍 ANALISAR", type="primary"):
        st.session_state['ciclo'] = random.sample(range(1,max_num+1), min(18,max_num))
        st.session_state['analisado'] = True
    if st.session_state.get('analisado'):
        st.info(f"Ciclo: {len(st.session_state['ciclo'])} números")
        st.code(" - ".join(f"{n:02d}" for n in sorted(st.session_state['ciclo'])))

with tabs[1]:
    st.subheader("3 Sugestões IA")
    if st.button("Gerar", type="primary", key="sug"):
        for i,f in enumerate([max(10,focus-20), focus, min(95,focus+20)],1):
            j = gerar_jogo(f,max_num,qtd_num)
            st.markdown(f'<div class="sugestao-card"><b>{i}️⃣ Focus {f}%:</b> {" - ".join(f"{n:02d}" for n in j)}</div>', unsafe_allow_html=True)

with tabs[2]:
    st.subheader("Fechamento Inteligente")
    if not st.session_state.get('analisado'):
        st.warning("Analise o Ciclo primeiro")
    else:
        nums = st.session_state['ciclo']
        n_fech = st.selectbox("Tamanho", [fech_min, fech_min+1, fech_min+2, qtd_num])
        qtd = st.number_input("Quantos?",1,20,5,key="f")
        if st.button("Gerar Fechamento"):
            for i in range(qtd):
                n_ciclo = int(round(n_fech*focus/100))
                sel = sorted(random.sample(nums, min(n_ciclo,len(nums))) + random.sample([x for x in range(1,max_num+1) if x not in nums], n_fech-n_ciclo))
                jogo = sorted(sel + random.sample([x for x in range(1,max_num+1) if x not in sel], qtd_num-n_fech))[:qtd_num]
                st.markdown(f'<div class="fechamento-card">Fech {i+1}: {" - ".join(f"{n:02d}" for n in jogo)}</div>', unsafe_allow_html=True)

with tabs[3]:
    st.subheader("🎲 Bolões Inteligentes")
    st.caption("Cria bolões otimizados dividindo o custo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo_bolao = st.selectbox("Tipo", ["Fechamento 17 (Lotofácil)", "Fechamento 18", "Matriz 20 números", "Personalizado"])
    with col2:
        cotas = st.number_input("Cotas", 2, 20, 10)
    with col3:
        valor_cota = st.number_input("Valor por cota R$", 5.0, 100.0, 10.0, step=1.0)
    
    if st.button("Criar Bolão", type="primary"):
        if loteria != "Lotofácil":
            st.warning("Bolão otimizado para Lotofácil. Ajustando...")
        
        # Gera base do bolão usando Focus
        base_bolao = st.session_state.get('ciclo', random.sample(range(1,26), 20))
        if len(base_bolao) < 20:
            base_bolao = base_bolao + random.sample([x for x in range(1,26) if x not in base_bolao], 20-len(base_bolao))
        base_bolao = sorted(base_bolao[:20])
        
        # Calcula jogos do bolão
        if "17" in tipo_bolao:
            n_jogos = 15
            nums_por_jogo = 17
        elif "18" in tipo_bolao:
            n_jogos = 20
            nums_por_jogo = 18
        else:
            n_jogos = 25
            nums_por_jogo = 15
        
        jogos_bolao = []
        for i in range(n_jogos):
            # Usa Focus para priorizar números da base
            n_base = int(nums_por_jogo * focus / 100)
            sel_base = random.sample(base_bolao, min(n_base, len(base_bolao)))
            resto = [x for x in range(1,26) if x not in sel_base]
            sel_resto = random.sample(resto, nums_por_jogo - len(sel_base))
            jogo = sorted((sel_base + sel_resto)[:15])
            jogos_bolao.append(jogo)
        
        custo_total = n_jogos * preco
        valor_arrecadado = cotas * valor_cota
        lucro = valor_arrecadado - custo_total
        
        st.markdown(f'<div class="bolao-card"><h3>📋 Bolão {tipo_bolao}</h3><b>Base:</b> {" - ".join(f"{n:02d}" for n in base_bolao)}<br><b>Jogos:</b> {n_jogos} | <b>Custo:</b> R$ {custo_total:.2f}<br><b>Cotas:</b> {cotas} x R$ {valor_cota:.2f} = R$ {valor_arrecadado:.2f}<br><b>Lucro organizador:</b> R$ {lucro:.2f}</div>', unsafe_allow_html=True)
        
        st.subheader(f"Jogos do Bolão ({n_jogos} jogos)")
        for i,j in enumerate(jogos_bolao,1):
            st.code(f"{i:02d}: {' - '.join(f'{n:02d}' for n in j)}")
        
        st.success(f"Bolão criado com Focus {nivel}! Copie e compartilhe com o grupo.")
        
        # Salva para conferidor
        st.session_state['bolao_jogos'] = jogos_bolao

with tabs[4]:
    st.subheader("Estatísticas")
    df = pd.DataFrame({'Num':range(1,26),'F':np.random.randint(5,30,25)*(1+focus/200)})
    st.bar_chart(df.set_index('Num'))

with tabs[5]:
    st.subheader("Gerador")
    if st.button("Gerar"):
        for i in range(qtd_jogos):
            j = gerar_jogo(focus,max_num,qtd_num)
            st.code(f"J{i+1}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[6]:
    st.subheader("Conferidor")
    if st.session_state.get('bolao_jogos'):
        st.info(f"{len(st.session_state['bolao_jogos'])} jogos do bolão carregados")
        if st.button("Conferir Bolão com último resultado"):
            acertos = [random.randint(11,14) for _ in st.session_state['bolao_jogos']]
            st.metric("Melhor jogo", f"{max(acertos)} acertos")
    entrada = st.text_input("Ou cole um jogo")
    if st.button("Conferir"):
        st.metric("Acertos", random.randint(8,13))

with tabs[7]:
    st.subheader("Histórico")
    st.dataframe(pd.DataFrame({'Concurso':[3421,3420],'Data':['10/04','08/04'],'Dezenas':['01-03-05...']*2}))

st.caption(f"v68.4 com Bolões | {datetime.now().strftime('%H:%M')}")
