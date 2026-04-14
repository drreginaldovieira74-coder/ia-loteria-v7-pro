import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v68.1", layout="wide", page_icon="🎯")

# --- ESTILO ---
st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.2rem; font-weight:700;}
.focus-box {background:#e8f5e9; padding:10px; border-radius:8px; border-left:4px solid #2e7d32;}
</style>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎯 v68.1 COMPLETA")
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

# --- CONFIG POR LOTERIA ---
configs = {
    "Lotofácil": {"max": 25, "qtd": 15},
    "Mega-Sena": {"max": 60, "qtd": 6},
    "Quina": {"max": 80, "qtd": 5},
    "Lotomania": {"max": 100, "qtd": 50},
    "Dupla Sena": {"max": 50, "qtd": 6},
    "Timemania": {"max": 80, "qtd": 10},
}
cfg = configs[loteria]
max_num = cfg["max"]
qtd_num = cfg["qtd"]

# --- HEADER ---
st.markdown('<div class="main-title">🎯 LOTOELITE v68.1 - FOCUS COMPLETO</div>', unsafe_allow_html=True)
st.success(f"✅ Versão 68.1 Ativa | Loteria: {loteria} | Focus: {nivel} ({focus}%)")

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Ciclo", "📈 Estatísticas", "🎲 Gerador", "📚 Histórico"])

with tab1:
    st.subheader(f"Ciclo - {loteria}")
    col1, col2 = st.columns([1,2])
    with col1:
        if st.button("🔍 ANALISAR", type="primary", use_container_width=True):
            st.session_state['analisado'] = True
    with col2:
        st.metric("Último concurso", "3421", "25/25")
    
    if st.session_state.get('analisado'):
        peso_quente = focus / 100
        st.info(f"Análise com peso quente = {peso_quente:.2f} | Números quentes terão {focus}% de prioridade")
        nums = list(range(1, max_num+1))
        quentes = random.sample(nums, min(12, max_num))
        st.write("**Números quentes detectados (demo):**", sorted(quentes[:8]))

with tab2:
    st.subheader("Estatísticas")
    st.write("Frequência simulada - muda com o Focus")
    df = pd.DataFrame({
        'Número': range(1, max_num+1),
        'Freq': np.random.randint(5, 30, max_num) * (1 + focus/150)
    })
    st.bar_chart(df.set_index('Número').head(30))

with tab3:
    st.subheader("Gerador Inteligente com Focus")
    st.caption(f"Gerando {qtd_num} números de 1 a {max_num}")
    
    if st.button("Gerar Jogos", type="primary"):
        jogos = []
        base = list(range(1, max_num+1))
        # define quentes e frios
        random.shuffle(base)
        split = int(len(base) * 0.4)
        quentes = base[:split]
        frios = base[split:]
        
        for _ in range(qtd_jogos):
            n_quentes = int(round(qtd_num * focus / 100))
            n_frios = qtd_num - n_quentes
            
            n_quentes = min(n_quentes, len(quentes), qtd_num)
            n_frios = min(n_frios, len(frios), qtd_num - n_quentes)
            
            parte_q = random.sample(quentes, n_quentes) if n_quentes > 0 else []
            parte_f = random.sample(frios, n_frios) if n_frios > 0 else []
            
            jogo = parte_q + parte_f
            
            # completa se faltou
            while len(jogo) < qtd_num:
                candidato = random.choice(base)
                if candidato not in jogo:
                    jogo.append(candidato)
            
            jogos.append(sorted(jogo[:qtd_num]))
        
        for i, j in enumerate(jogos, 1):
            numeros = ' - '.join(f'{n:02d}' for n in j)
            st.code(f"Jogo {i:02d}: {numeros}")
        
        st.success(f"{len(jogos)} jogos gerados com Focus {nivel} ({focus}%)")

with tab4:
    st.subheader("Histórico")
    st.info("Aqui entraria o histórico real da Caixa. Versão demo.")
    hist = pd.DataFrame({
        'Concurso': [3421,3420,3419,3418,3417],
        'Data': ['10/04','08/04','05/04','03/04','01/04'],
        'Dezenas': ['01-03-05-08-10-11-13-14-17-18-19-21-22-24-25']*5
    })
    st.dataframe(hist, use_container_width=True)

st.markdown("---")
st.caption(f"LOTOELITE v68.1 | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Erro de sintaxe corrigido")
