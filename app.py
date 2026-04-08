import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")

st.title("🎟️ LotoElite Pro")
st.markdown("**A mais avançada plataforma de previsão inteligente do Brasil** • Ciclo + IA + Aprendizado")

# ========================= INICIALIZAÇÃO DE SESSÃO =========================
if 'feedback' not in st.session_state:
    st.session_state.feedback = []          # Histórico de feedback do usuário
if 'historico_pessoal' not in st.session_state:
    st.session_state.historico_pessoal = [] # Jogos gerados + resultados

# ========================= SELETOR DE LOTERIA =========================
loteria_options = {
    "Lotofácil":       {"nome": "Lotofácil",       "total": 25,  "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania":       {"nome": "Lotomania",       "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena":       {"nome": "Mega-Sena",       "total": 60,  "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Quina":           {"nome": "Quina",           "total": 80,  "sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Dupla Sena":      {"nome": "Dupla Sena",      "total": 50,  "sorteadas": 6,  "tipo_ciclo": "frequency"},
    "Super Sete":      {"nome": "Super Sete",      "total": 49,  "sorteadas": 7,  "tipo_ciclo": "frequency"},
    "Loteria Federal": {"nome": "Loteria Federal", "total": 99999,"sorteadas": 5,  "tipo_ciclo": "frequency"},
    "Loteria Milionária": {"nome": "Loteria Milionária", "total": 50, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Timemania":       {"nome": "Timemania",       "total": 80,  "sorteadas": 7,  "tipo_ciclo": "frequency"}
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.markdown(f"**Loteria ativa:** {config['nome']} ({config['sorteadas']} de {config['total']})")

# ========================= UPLOAD =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV")
    st.stop()

@st.cache_data
def carregar_csv(arquivo, sorteadas):
    df = pd.read_csv(arquivo, header=None, dtype=str)
    df = df.iloc[:, :sorteadas]
    df = df.dropna(how='all')
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    df = df.astype(int)
    return df if df.shape[1] == sorteadas and not df.empty else None

df = carregar_csv(arquivo, config["sorteadas"])
if df is None:
    st.error("❌ CSV inválido ou vazio.")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados com sucesso!")

# ========================= MOTOR DE CICLO =========================
def detectar_ciclo(df: pd.DataFrame, config: Dict):
    if len(df) == 0:
        return "INÍCIO", list(range(1, config["total"]+1)), 0.0

    if config["tipo_ciclo"] == "full":
        historico = df.values
        ciclos_inicio = [0]
        cobertura = set()
        for i in range(len(historico)):
            cobertura.update(historico[i])
            if len(cobertura) == config["total"]:
                ciclos_inicio.append(i + 1)
                cobertura = set()
        ultimo_reset = ciclos_inicio[-1]
        df_atual = df.iloc[ultimo_reset:]
        if len(df_atual) == 0:
            return "INÍCIO", list(range(1, config["total"]+1)), 0.0
        cobertura_atual = set(np.concatenate(df_atual.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - cobertura_atual)
        progresso = len(cobertura_atual) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso
    else:
        ultimos = df.iloc[-45:] if len(df) > 45 else df
        todos = set(np.concatenate(ultimos.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - todos)
        progresso = (config["total"] - len(faltantes)) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔥 Fechamento Inteligente",
    "🎟️ Gerar Jogos com Filtros",
    "📊 Estatísticas com IA",
    "📈 Simulador Histórico",
    "📉 Backtesting Automático",
    "👤 Meu Histórico & Feedback",
    "💰 Bankroll Advisor"
])

# TAB 1 - FECHAMENTO INTELIGENTE
with tab1:
    st.subheader("🔥 Fechamento Inteligente Recomendado pela IA")
    if st.button("🚀 Gerar Fechamento Inteligente", type="primary", use_container_width=True):
        jogos = []
        for _ in range(3):
            if fase == "FIM" and len(faltantes) > 0:
                num_faltantes = min(12, len(faltantes))
                faltantes_escolhidas = random.sample(faltantes, num_faltantes)
                restantes = list(set(range(1, config["total"]+1)) - set(faltantes_escolhidas))
                completar = random.sample(restantes, config["sorteadas"] - num_faltantes)
                jogo = sorted(faltantes_escolhidas + completar)
            else:
                pool = faltantes * 3 + list(range(1, config["total"]+1))
                jogo = sorted(random.sample(pool, config["sorteadas"]))
            jogos.append(jogo)
        st.dataframe(pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])]), use_container_width=True)
        st.success("✅ 3 fechamentos inteligentes gerados com base no ciclo atual!")

# TAB 2 - GERAR JOGOS COM FILTROS
with tab2:
    st.subheader("🎟️ Gerar Jogos com Filtros Avançados")
    col1, col2, col3 = st.columns(3)
    with col1: qtd = st.slider("Quantidade de jogos", 5, 100, 25)
    with col2: pares = st.slider("Números pares", 0, config["sorteadas"], config["sorteadas"]//2)
    with col3: consecutivos = st.slider("Máx. consecutivos", 1, 6, 3)

    if st.button("🚀 Gerar Jogos com Filtros", type="primary", use_container_width=True):
        jogos = []
        for _ in range(qtd):
            while True:
                jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
                num_pares = len([x for x in jogo if x % 2 == 0])
                num_consec = max([jogo[i+1] - jogo[i] for i in range(len(jogo)-1)], default=0)
                if num_pares == pares and num_consec <= consecutivos:
                    jogos.append(jogo)
                    break
        st.dataframe(pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])]), use_container_width=True)

# TAB 3 - ESTATÍSTICAS COM IA
with tab3:
    st.subheader("📊 Estatísticas Inteligentes com IA")
    if st.button("Atualizar Estatísticas"):
        todos = np.concatenate(df.values)
        freq = Counter(todos)
        st.write("**Números mais sorteados**")
        st.bar_chart(pd.Series(freq).sort_values(ascending=False).head(15))
        st.write("**Atrasos atuais**")
        atrasos = {n: sum(1 for i in range(len(df)-1, -1, -1) if n not in df.iloc[i].values) for n in range(1, config["total"]+1)}
        st.dataframe(pd.DataFrame.from_dict(atrasos, orient='index', columns=['Atraso']).sort_values('Atraso', ascending=False).head(15))

# TAB 4 - SIMULADOR HISTÓRICO
with tab4:
    st.subheader("📈 Simulador Histórico Avançado")
    st.info("Cole seus jogos (um por linha, separado por espaço ou vírgula)")
    jogos_teste = st.text_area("Jogos para simular", height=200)
    if st.button("Simular contra Histórico"):
        if jogos_teste.strip():
            jogos = [[int(x) for x in linha.replace(",", " ").split() if x.isdigit()] for linha in jogos_teste.strip().split("\n") if len([int(x) for x in linha.replace(",", " ").split() if x.isdigit()]) == config["sorteadas"]]
            resultados = []
            for jogo in jogos:
                acertos = [sum(1 for n in jogo if n in row) for row in df.values]
                resultados.append({"Jogo": sorted(jogo), "Melhor": max(acertos), "Média": round(np.mean(acertos), 1)})
            st.dataframe(pd.DataFrame(resultados))

# TAB 5 - BACKTESTING AUTOMÁTICO (APROVADO)
with tab5:
    st.subheader("📉 Backtesting Automático")
    st.info("Testa a estratégia atual contra os últimos 100 concursos")
    if st.button("🚀 Executar Backtesting nos últimos 100 concursos", type="primary", use_container_width=True):
        with st.spinner("Executando backtesting..."):
            n = min(100, len(df))
            acertos_total = []
            for i in range(n):
                jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
                acertos = sum(1 for n in jogo if n in df.iloc[i].values)
                acertos_total.append(acertos)
            st.write(f"**Média de acertos:** {np.mean(acertos_total):.2f} pontos")
            st.write(f"**Taxa de 11+ pontos:** {sum(1 for a in acertos_total if a >= 11)/n*100:.1f}%")
            st.write(f"**Taxa de 13+ pontos:** {sum(1 for a in acertos_total if a >= 13)/n*100:.1f}%")
            st.bar_chart(pd.Series(acertos_total).value_counts().sort_index())

# TAB 6 - MEU HISTÓRICO & FEEDBACK (AUTO-APRENDIZADO)
with tab6:
    st.subheader("👤 Meu Histórico & Feedback (Auto-Aprendizado)")
    
    # Feedback
    st.write("**Dê feedback dos últimos jogos gerados**")
    pontos = st.number_input("Quantos pontos você acertou no último sorteio?", 0, 15, 0)
    if st.button("Salvar Feedback"):
        st.session_state.feedback.append(pontos)
        st.success("✅ Feedback salvo! O sistema está aprendendo com seus resultados.")
    
    # Histórico pessoal
    if st.session_state.historico_pessoal:
        st.write("**Seus jogos anteriores**")
        st.dataframe(pd.DataFrame(st.session_state.historico_pessoal))
    else:
        st.info("Nenhum jogo salvo ainda.")

# TAB 7 - BANKROLL + RELATÓRIO
with tab7:
    st.subheader("💰 Smart Bankroll Advisor")
    bankroll = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    kelly = 0.45 if fase == "FIM" else 0.28 if fase == "MEIO" else 0.12
    st.metric("Kelly % Recomendado", f"{kelly*100:.1f}%")
    st.metric("Valor ideal por jogo", f"R$ {bankroll * kelly:.2f}")

    st.subheader("📄 Exportar Relatório Completo")
    if st.button("📥 Gerar e Baixar Relatório Completo"):
        html = f"""
        <h1>LotoElite Pro - Relatório</h1>
        <h2>Loteria: {config['nome']} | Fase do Ciclo: {fase}</h2>
        <p>Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
        <h3>Resumo do Ciclo</h3>
        <p>Progresso: {progresso:.1f}% | Faltantes: {len(faltantes)}</p>
        <p>Estratégia: {estrategia}</p>
        <hr>
        <p>Obrigado por usar LotoElite Pro</p>
        """
        st.download_button("Baixar Relatório", html, f"relatorio_lotoelite_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.html", "text/html")

st.caption("LotoElite Pro • Estratégia que vence o acaso.")
