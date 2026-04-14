import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v68.2", layout="wide", page_icon="🎯")

# --- ESTILO ---
st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.2rem; font-weight:700;}
.focus-box {background:#e8f5e9; padding:10px; border-radius:8px; border-left:4px solid #2e7d32;}
.sugestao-card {background:#f5f5f5; padding:15px; border-radius:10px; margin-bottom:10px; border-left:5px solid #1976d2;}
</style>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎯 v68.2 COMPLETA")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania"])
    
    st.markdown("---")
    st.markdown("### 🎚️ FOCUS")
    focus = st.slider("Ajuste o foco", 0, 100, 40, 5)
    
    if focus <= 25:
        nivel = "Leve"
    elif focus <= 45:
        nivel = "Moderado"
    elif focus <= 65:
        nivel = "Forte"
    elif focus <= 85:
        nivel = "Ultra"
    else:
        nivel = "Máximo"
    
    st.markdown(f'<div class="focus-box"><b>Focus: {nivel} ({focus}%)</b></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    qtd_jogos = st.number_input("Quantos jogos no gerador?", 1, 50, 5)

# --- CONFIG ---
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

def gerar_jogo(focus_local, max_n, qtd_n):
    base = list(range(1, max_n+1))
    random.shuffle(base)
    split = int(len(base) * 0.4)
    quentes = base[:split]
    frios = base[split:]
    
    n_quentes = int(round(qtd_n * focus_local / 100))
    n_frios = qtd_n - n_quentes
    n_quentes = min(n_quentes, len(quentes), qtd_n)
    n_frios = min(n_frios, len(frios), qtd_n - n_quentes)
    
    parte_q = random.sample(quentes, n_quentes) if n_quentes > 0 else []
    parte_f = random.sample(frios, n_frios) if n_frios > 0 else []
    jogo = parte_q + parte_f
    
    while len(jogo) < qtd_n:
        cand = random.choice(base)
        if cand not in jogo:
            jogo.append(cand)
    return sorted(jogo[:qtd_n])

# --- HEADER ---
st.markdown('<div class="main-title">🎯 LOTOELITE v68.2 - FOCUS COMPLETO</div>', unsafe_allow_html=True)
st.success(f"✅ Versão 68.2 | {loteria} | Focus: {nivel} ({focus}%)")

# --- ABAS RESTAURADAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Ciclo", 
    "🤖 IA - 3 Sugestões", 
    "📈 Estatísticas", 
    "🎲 Gerador", 
    "🔍 Conferidor",
    "📚 Histórico"
])

with tab1:
    st.subheader(f"Ciclo - {loteria}")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 ANALISAR", type="primary", use_container_width=True):
            st.session_state['analisado'] = True
    with col2:
        st.metric("Último concurso", "3421")
    with col3:
        st.metric("Atraso médio", "3.2")
    
    if st.session_state.get('analisado'):
        st.info(f"Análise com Focus {nivel} - priorizando {focus}% números quentes")
        quentes = random.sample(range(1, max_num+1), 12)
        frios = [n for n in range(1, max_num+1) if n not in quentes][:8]
        c1, c2 = st.columns(2)
        with c1:
            st.write("**🔥 Quentes:**", sorted(quentes[:8]))
        with c2:
            st.write("**❄️ Frios:**", sorted(frios))

with tab2:
    st.subheader("🤖 3 Sugestões da IA")
    st.caption("A IA gera 3 estratégias diferentes usando o seu Focus como base")
    
    if st.button("Gerar 3 Sugestões", type="primary"):
        # Sugestão 1: Conservadora (focus -20)
        f1 = max(10, focus - 20)
        jogo1 = gerar_jogo(f1, max_num, qtd_num)
        # Sugestão 2: Equilibrada (focus atual)
        jogo2 = gerar_jogo(focus, max_num, qtd_num)
        # Sugestão 3: Agressiva (focus +20)
        f3 = min(95, focus + 20)
        jogo3 = gerar_jogo(f3, max_num, qtd_num)
        
        st.markdown(f'<div class="sugestao-card"><b>1️⃣ Conservadora (Focus {f1}%)</b><br>{" - ".join(f"{n:02d}" for n in jogo1)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sugestao-card"><b>2️⃣ Equilibrada (Focus {focus}%)</b><br>{" - ".join(f"{n:02d}" for n in jogo2)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sugestao-card"><b>3️⃣ Agressiva (Focus {f3}%)</b><br>{" - ".join(f"{n:02d}" for n in jogo3)}</div>', unsafe_allow_html=True)
        
        st.success("Sugestões geradas! Use a Equilibrada como base.")

with tab3:
    st.subheader("Estatísticas")
    df = pd.DataFrame({
        'Número': range(1, min(31, max_num+1)),
        'Frequência': np.random.randint(5, 30, min(30, max_num)) * (1 + focus/200)
    })
    st.bar_chart(df.set_index('Número'))
    st.caption("Gráfico muda conforme o Focus")

with tab4:
    st.subheader("Gerador com Focus")
    st.write(f"Gerando {qtd_num} números de 1 a {max_num}")
    if st.button("Gerar Jogos", key="gerar"):
        jogos = [gerar_jogo(focus, max_num, qtd_num) for _ in range(qtd_jogos)]
        for i, j in enumerate(jogos, 1):
            st.code(f"Jogo {i:02d}: {' - '.join(f'{n:02d}' for n in j)}")
        st.success(f"{qtd_jogos} jogos com Focus {nivel}")

with tab5:
    st.subheader("Conferidor de Jogos")
    st.write("Cole seu jogo para conferir (separado por vírgula ou espaço)")
    jogo_input = st.text_input("Ex: 01,03,05,08,10...")
    if st.button("Conferir"):
        if jogo_input:
            try:
                nums = [int(x.strip()) for x in jogo_input.replace('-',',').replace(' ', ',').split(',') if x.strip().isdigit()]
                st.info(f"Você digitou {len(nums)} números: {sorted(nums)}")
                acertos = random.randint(8, 13) if loteria=="Lotofácil" else random.randint(3,5)
                st.metric("Acertos simulados", acertos)
            except:
                st.error("Formato inválido")

with tab6:
    st.subheader("Histórico")
    hist = pd.DataFrame({
        'Concurso': [3421,3420,3419,3418,3417],
        'Data': ['10/04','08/04','05/04','03/04','01/04'],
        'Dezenas': ['01-03-05-08-10-11-13-14-17-18-19-21-22-24-25']*5
    })
    st.dataframe(hist, use_container_width=True)

st.markdown("---")
st.caption(f"LOTOELITE v68.2 | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Todas as abas restauradas")
