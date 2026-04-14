import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v68", layout="wide", page_icon="🎯")

# --- ESTILO ---
st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.2rem; font-weight:700;}
.focus-box {background:#e8f5e9; padding:10px; border-radius:8px; border-left:4px solid #2e7d32;}
</style>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎯 v68 COMPLETA")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania"])
    
    st.markdown("---")
    st.markdown("### 🎚️ FOCUS")
    focus = st.slider("Ajuste o foco", 0, 100, 40, 5, 
                      help="Leve=20, Moderado=40, Forte=60, Ultra=80, Máximo=95")
    
    if focus <= 25:
        nivel, cor = "Leve", "#81c784"
    elif focus <= 45:
        nivel, cor = "Moderado", "#4caf50"
    elif focus <= 65:
        nivel, cor = "Forte", "#ff9800"
    elif focus <= 85:
        nivel, cor = "Ultra", "#f57c00"
    else:
        nivel, cor = "Máximo", "#d32f2f"
    
    st.markdown(f'<div class="focus-box"><b>Focus: {nivel} ({focus}%)</b></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    qtd_jogos = st.number_input("Quantos jogos?", 1, 50, 5)
    st.caption("LotoFácil: 15 números | Mega: 6 | Quina: 5")

# --- HEADER ---
st.markdown('<div class="main-title">🎯 LOTOELITE v68 - FOCUS COMPLETO</div>', unsafe_allow_html=True)
st.success(f"✅ Versão 68 Ativa | Loteria: {loteria} | Focus: {nivel} ({focus}%)")

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Ciclo", "📈 Estatísticas", "🎲 Gerador", "📚 Histórico"])

with tab1:
    st.subheader(f"Ciclo - {loteria}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 ANALISAR", type="primary", use_container_width=True):
            st.session_state['analisado'] = True
    with col2:
        st.metric("Último concurso", "3421", "25/25")
    
    if st.session_state.get('analisado'):
        # Simulação de análise com Focus
        peso_quente = focus / 100
        st.info(f"Análise com peso quente = {peso_quente:.2f}")
        # Dados fake para demonstração
        nums = list(range(1, 26 if loteria=="Lotofácil" else 61))
        quentes = random.sample(nums, 10)
        st.write("**Números quentes detectados:**", sorted(quentes[:8]))

with tab2:
    st.subheader("Estatísticas")
    st.write("Distribuição por frequência (simulada com Focus)")
    df = pd.DataFrame({
        'Número': range(1, 26),
        'Freq': np.random.randint(5, 30, 25) * (1 + focus/200)
    })
    st.bar_chart(df.set_index('Número'))

with tab3:
    st.subheader("Gerador Inteligente com Focus")
    if st.button("Gerar Jogos", type="primary"):
        jogos = []
        max_num = 25 if loteria=="Lotofácil" else 60 if loteria=="Mega-Sena" else 80
        qtd_num = 15 if loteria=="Lotofácil" else 6 if loteria=="Mega-Sena" else 5
        
        # Base quente simulada
        base = list(range(1, max_num+1))
        quentes = base[:int(len(base)*0.4)]
        frios = base[int(len(base)*0.4):]
        
        for _ in range(qtd_jogos):
            n_quentes = int(qtd_num * focus / 100)
            n_frios = qtd_num - n_quentes
            jogo = sorted(random.sample(quentes, min(n_quentes, len(quentes))) + 
                   sorted(random.sample(frios, min(n_frios, len(frios))))
            # completa se faltar
            while len(jogo) < qtd_num:
                jogo.append(random.choice(base))
                jogo = sorted(list(set(jogo)))
            jogos.append(jogo[:qtd_num])
        
        for i, j in enumerate(jogos, 1):
            st.code(f"Jogo {i:02d}: {' - '.join(f'{n:02d}' for n in j)}")
        
        st.success(f"{len(jogos)} jogos gerados com Focus {nivel}")

with tab4:
    st.subheader("Histórico")
    st.info("Aqui entraria o histórico real da Caixa (sem CSV). Versão demo mostra últimos 5.")
    hist = pd.DataFrame({
        'Concurso': [3421,3420,3419,3418,3417],
        'Data': ['10/04','08/04','05/04','03/04','01/04'],
        'Dezenas': ['01-03-05-08-10-11-13-14-17-18-19-21-22-24-25']*5
    })
    st.dataframe(hist, use_container_width=True)

st.markdown("---")
st.caption(f"LOTOELITE v68 | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Focus funcionando em todas as abas")
