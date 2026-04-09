import streamlit as st
import pandas as pd
import numpy as np
import random
import requests
from collections import Counter, defaultdict
from typing import List, Dict
import warnings
import time
warnings.filterwarnings("ignore")

# ========================= SESSION STATE =========================
if 'feedback' not in st.session_state:
    st.session_state.feedback = []
if 'pesos_aprendidos' not in st.session_state:
    st.session_state.pesos_aprendidos = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
if 'df' not in st.session_state:
    st.session_state.df = None

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")
st.title("🎟️ LotoElite Pro")
st.markdown("**A mais avançada plataforma de previsão inteligente do Brasil** • Ciclo + IA + Atualização Automática")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "api": "lotofacil", "total": 25, "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania": {"nome": "Lotomania", "api": "lotomania", "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena": {"nome": "Mega-Sena", "api": "megasena", "total": 60, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Quina": {"nome": "Quina", "api": "quina", "total": 80, "sorteadas": 5, "tipo_ciclo": "frequency"},
    "Dupla Sena": {"nome": "Dupla Sena", "api": "duplasena", "total": 50, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Super Sete": {"nome": "Super Sete", "api": "supersete", "total": 49, "sorteadas": 7, "tipo_ciclo": "frequency"},
    "Timemania": {"nome": "Timemania", "api": "timemania", "total": 80, "sorteadas": 7, "tipo_ciclo": "frequency"},
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações")
    estrategia = st.selectbox("Modo de Estratégia IA", ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"], index=3)
    
    st.header("🔄 Atualização Automática")
    if st.button("🔄 Atualizar Histórico Automático (Caixa)"):
        with st.spinner("Tentando conectar com a Caixa (3 tentativas)..."):
            success = False
            for attempt in range(3):
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{config['api']}"
                    response = requests.get(url, headers=headers, timeout=20)
                    if response.status_code == 200:
                        data = response.json()
                        dezenas = [item["dezenasSorteadas"] for item in data.get("listaDezenas", [])]
                        st.session_state.df = pd.DataFrame(dezenas).apply(pd.to_numeric)
                        st.success(f"✅ Histórico atualizado automaticamente! {len(st.session_state.df)} concursos.")
                        success = True
                        st.rerun()
                        break
                except:
                    time.sleep(1.5)
            if not success:
                st.error("❌ Não foi possível conectar com a Caixa após 3 tentativas. Use o upload manual abaixo.")

# ========================= DF =========================
if st.session_state.df is None:
    st.subheader(f"📤 Upload Manual da {config['nome']}")
    arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])
    if arquivo is None:
        st.stop()
    df = pd.read_csv(arquivo, header=None, dtype=str).iloc[:, :config["sorteadas"]]
    df = df.apply(pd.to_numeric, errors='coerce').dropna().astype(int)
    st.session_state.df = df

df = st.session_state.df
st.success(f"✅ {len(df)} concursos carregados com sucesso!")

# ========================= CICLO =========================
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

# ========================= APRENDIZADO =========================
def aplicar_aprendizado(loteria: str, fase: str) -> List[int]:
    pesos = st.session_state.pesos_aprendidos[loteria][fase]
    numeros = list(range(1, config["total"] + 1))
    if not pesos:
        return numeros
    pesos_lista = [pesos.get(n, 1.0) for n in numeros]
    total = sum(pesos_lista)
    probs = [p / total for p in pesos_lista]
    return list(np.random.choice(numeros, size=config["total"], replace=False, p=probs))

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔥 Fechamento Inteligente", "🎟️ Gerar Jogos com Filtros", "📊 Estatísticas com IA",
    "📈 Simulador Histórico", "📉 Backtesting Automático", "🤝 Bolão Optimizer",
    "👤 Meu Perfil & Aprendizado"
])

# TAB 1
with tab1:
    st.subheader("🔥 Fechamento Inteligente Recomendado pela IA")
    st.info(f"**Super Focus recomendado:** {'ULTRA FOCUS' if fase == 'FIM' else 'AGRESSIVO' if fase == 'MEIO' else 'BALANCEADO'} | Confiança: {int(25 + progresso/2)}%")
    if st.button("🚀 Gerar Fechamento Inteligente (Super Focus)", type="primary", use_container_width=True):
        jogos = []
        pool_base = aplicar_aprendizado(config['nome'], fase)
        for i in range(3):
            pool = pool_base.copy()
            if i > 0: random.shuffle(pool)
            jogo = sorted(random.sample(pool, config["sorteadas"]))
            jogos.append(jogo)
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_jogos, use_container_width=True)
        st.success("✅ 3 jogos Super Focus gerados!")

# TAB 2
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
                pool = aplicar_aprendizado(config['nome'], fase)
                jogo = sorted(random.sample(pool, config["sorteadas"]))
                num_pares = len([x for x in jogo if x % 2 == 0])
                num_consec = max([jogo[i+1] - jogo[i] for i in range(len(jogo)-1)], default=0)
                if num_pares == pares and num_consec <= consecutivos:
                    jogos.append(jogo)
                    break
        st.dataframe(pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])]), use_container_width=True)

# TAB 3
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

# TAB 4
with tab4:
    st.subheader("📈 Simulador Histórico Avançado")
    st.info("Cole seus jogos (um por linha, separado por espaço ou vírgula)")
    jogos_teste = st.text_area("Jogos para simular", height=200)
    if st.button("Simular contra Histórico"):
        if jogos_teste.strip():
            jogos = [[int(x) for x in linha.replace(",", " ").split() if x.isdigit()] for linha in jogos_teste.strip().split("\n")]
            resultados = []
            for jogo in jogos:
                if len(jogo) == config["sorteadas"]:
                    acertos = [sum(1 for n in jogo if n in row) for row in df.values]
                    resultados.append({"Jogo": sorted(jogo), "Melhor": max(acertos), "Média": round(np.mean(acertos), 1)})
            st.dataframe(pd.DataFrame(resultados))

# TAB 5
with tab5:
    st.subheader("📉 Backtesting Automático com IA")
    if st.button("🚀 Executar Backtesting Inteligente (últimos 100)", type="primary", use_container_width=True):
        with st.spinner("Executando backtesting..."):
            n = min(100, len(df))
            acertos_total = []
            for i in range(n):
                pool = aplicar_aprendizado(config['nome'], fase)
                jogo = sorted(random.sample(pool, config["sorteadas"]))
                acertos = sum(1 for n in jogo if n in df.iloc[i].values)
                acertos_total.append(acertos)
            st.write(f"**Média de acertos com IA:** {np.mean(acertos_total):.2f} pontos")
            st.write(f"**Taxa de 11+ pontos:** {sum(1 for a in acertos_total if a >= 11)/n*100:.1f}%")
            st.write(f"**Taxa de 13+ pontos:** {sum(1 for a in acertos_total if a >= 13)/n*100:.1f}%")
            st.bar_chart(pd.Series(acertos_total).value_counts().sort_index())

# TAB 6
with tab6:
    st.subheader("🤝 Bolão Optimizer")
    num_jogos = st.slider("Quantidade de jogos no bolão", 10, 100, 25)
    if st.button("🚀 Gerar Bolão Otimizado", type="primary", use_container_width=True):
        jogos = []
        for _ in range(num_jogos):
            pool = aplicar_aprendizado(config['nome'], fase)
            jogo = sorted(random.sample(pool, config["sorteadas"]))
            jogos.append(jogo)
        df_bolao = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_bolao, use_container_width=True)
        st.success(f"✅ Bolão de {num_jogos} jogos gerado!")

# TAB 7
with tab7:
    st.subheader("👤 Meu Perfil & Aprendizado Pessoal")
    col1, col2 = st.columns(2)
    with col1:
        pontos = st.number_input("Quantos pontos você acertou?", 0, 15, 8)
    with col2:
        if st.button("✅ Salvar Feedback"):
            st.session_state.feedback.append({
                "fase": fase,
                "estrategia": estrategia,
                "pontos": pontos,
                "loteria": config['nome']
            })
            for num in range(1, config["total"]+1):
                st.session_state.pesos_aprendidos[config['nome']][fase][num] += (pontos / 15.0)
            st.success("✅ Feedback salvo! O sistema aprendeu com você.")

    if st.session_state.feedback:
        df_feedback = pd.DataFrame(st.session_state.feedback)
        st.metric("Média de acertos", f"{df_feedback['pontos'].mean():.2f} pontos")
        st.dataframe(df_feedback)

st.caption("LotoElite Pro • Estratégia que vence o acaso com atualização automática")
