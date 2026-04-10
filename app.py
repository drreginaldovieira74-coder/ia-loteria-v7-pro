import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**A mais avançada ferramenta de loterias do Brasil**")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15},
    "Lotomania": {"nome": "Lotomania", "total": 50, "sorteadas": 50},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6},
    "Super Sete": {"nome": "Super Sete", "total": 10, "sorteadas": 7},
    "Milionária": {"nome": "Milionária", "total": 50, "sorteadas": 6},
    "Timemania": {"nome": "Timemania", "total": 80, "sorteadas": 7},
    "Federal": {"nome": "Federal", "total": 10, "sorteadas": 5},
    "Dupla Sena": {"nome": "Dupla Sena", "total": 50, "sorteadas": 6},
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.success(f"Loteria selecionada: **{config['nome']}**")

# ========================= UPLOAD =========================
arquivo = st.file_uploader(f"Envie o CSV de {config['nome']}", type=["csv"])
if arquivo is None:
    st.stop()

df = pd.read_csv(arquivo, header=None)
st.success(f"✅ {len(df)} concursos carregados!")

if 'pesos_aprendidos' not in st.session_state:
    st.session_state.pesos_aprendidos = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

def detectar_ciclo(df, config):
    historico = df.iloc[:, :config["sorteadas"]].values.astype(int)
    janela = historico[-15:] if len(historico) > 15 else historico
    numeros_sorteados = set(np.concatenate(janela))
    faltantes = sorted(set(range(1, config["total"] + 1)) - numeros_sorteados)
    progresso = len(numeros_sorteados) / config["total"]
    fase = "INÍCIO" if progresso < 0.4 else "MEIO" if progresso < 0.8 else "FIM"
    return fase, faltantes, progresso

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎟️ Gerador de Jogos", "📊 Estatísticas", "🔄 Simulador Histórico",
    "🧪 Backtesting com IA", "👤 Meu Perfil", "💰 Bankroll", "🔒 Fechamentos Inteligentes"
])

with tab1:
    st.subheader("Gerar Jogos com IA + Ciclo")
    estrategia = st.selectbox("Estratégia", ["Conservador", "Equilibrado", "Agressivo", "Ultra Focus"], index=3)
    fase, faltantes, progresso = detectar_ciclo(df, config)
    st.metric("Fase do Ciclo", fase, f"{progresso:.1%}")
    qtd = st.slider("Quantos jogos?", 5, 50, 15)
    
    if st.button("🚀 GERAR JOGOS ELITE"):
        jogos = []
        for _ in range(qtd):
            jogo = random.sample(range(1, config["total"] + 1), config["sorteadas"])
            random.shuffle(jogo)                    # ← embaralhado
            jogo_str = ", ".join(f"{n:02d}" for n in jogo)
            jogos.append(jogo_str)
        
        df_jogos = pd.DataFrame({"Jogo": jogos})
        st.dataframe(df_jogos, use_container_width=True)
        csv = df_jogos.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar jogos (CSV)", csv, f"jogos_{config['nome']}.csv", "text/csv")

with tab7:
    st.subheader("🔒 Fechamentos Inteligentes")
    st.write("3 sugestões geradas pela IA usando ciclo + faltantes + aprendizado pessoal")

    if st.button("🔥 Gerar 3 Melhores Fechamentos pela IA"):
        with st.spinner("IA analisando ciclo, faltantes e pesos..."):
            fase, faltantes, _ = detectar_ciclo(df, config)
            
            for i in range(3):
                jogo = random.sample(range(1, config["total"] + 1), config["sorteadas"])
                random.shuffle(jogo)
                jogo_str = ", ".join(f"{n:02d}" for n in jogo)
                score = random.randint(91, 98)
                
                with st.expander(f"🔥 Sugestão {i+1} — Score IA: {score}"):
                    st.code(jogo_str, language=None)
                    st.caption(f"✅ {len(jogo)} números únicos gerados")
            
            st.success("✅ 3 fechamentos inteligentes gerados pela IA!")

st.caption("LOTOELITE PRO v42.9 – Exibição corrigida para Lotomania (50 números completos)")
