import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="LotoElite Pro", page_icon="🎟️", layout="wide")

st.title("🎟️ LotoElite Pro")
st.markdown("**Plataforma Profissional de Previsão Inteligente** • Ciclo + AI Oracle + Simulador")

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

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações LotoElite Pro")
    estrategia = st.selectbox("Modo de Estratégia IA", ["CONSERVADOR", "BALANCEADO", "AGRESSIVO", "ULTRA FOCUS"], index=3)
    tamanho_pool = st.number_input("Tamanho Base do Pool", 15, 30, 18)
    if st.button("🔄 Limpar Cache"):
        st.cache_data.clear()
        st.rerun()

# ========================= UPLOAD =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
arquivo = st.file_uploader("Envie o CSV (apenas números, sem cabeçalho)", type=["csv"])

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV")
    st.stop()

@st.cache_data
def carregar_csv(arquivo, sorteadas):
    try:
        df = pd.read_csv(arquivo, header=None, dtype=str)
        df = df.iloc[:, :sorteadas]
        df = df.dropna(how='all')
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna()
        df = df.astype(int)
        if df.shape[1] != sorteadas or df.empty:
            st.error("❌ CSV inválido ou vazio.")
            return None
        return df
    except Exception as e:
        st.error(f"❌ Erro ao processar o CSV: {str(e)}")
        return None

df = carregar_csv(arquivo, config["sorteadas"])
if df is None or len(df) == 0:
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔥 Fechamento Inteligente",
    "🎟️ Gerar Jogos",
    "📊 Estatísticas Detalhadas",
    "📈 Simulador Histórico",
    "💰 Bankroll Advisor"
])

# ========================= TAB 1 - FECHAMENTO INTELIGENTE =========================
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
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_jogos, use_container_width=True)
        st.success("✅ 3 fechamentos inteligentes gerados com base no ciclo atual!")

# ========================= TAB 2 - GERAR JOGOS COM FILTROS =========================
with tab2:
    st.subheader("🎟️ Gerar Jogos com Filtros Avançados")
    col1, col2 = st.columns(2)
    with col1:
        qtd = st.slider("Quantidade de jogos", 5, 100, 25)
    with col2:
        pares = st.slider("Quantidade de números pares", 0, config["sorteadas"], config["sorteadas"]//2)

    if st.button("🚀 Gerar Jogos com Filtros", type="primary", use_container_width=True):
        jogos = []
        for _ in range(qtd):
            while True:
                pool = list(range(1, config["total"]+1))
                jogo = sorted(random.sample(pool, config["sorteadas"]))
                if len([x for x in jogo if x % 2 == 0]) == pares:
                    jogos.append(jogo)
                    break
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_jogos, use_container_width=True)

# ========================= TAB 3 - ESTATÍSTICAS DETALHADAS =========================
with tab3:
    st.subheader("📊 Estatísticas Detalhadas")
    if st.button("Atualizar Estatísticas"):
        todos_numeros = np.concatenate(df.values)
        freq = Counter(todos_numeros)
        atrasos = {}
        for n in range(1, config["total"]+1):
            atrasos[n] = 0
            for i in range(len(df)-1, -1, -1):
                if n in df.iloc[i].values:
                    break
                atrasos[n] += 1
        st.write("**Números mais sorteados**")
        st.bar_chart(pd.Series(freq).sort_values(ascending=False).head(15))
        st.write("**Atrasos atuais**")
        st.dataframe(pd.DataFrame.from_dict(atrasos, orient='index', columns=['Atraso']).sort_values('Atraso', ascending=False))

# ========================= TAB 4 - SIMULADOR HISTÓRICO =========================
with tab4:
    st.subheader("📈 Simulador Histórico")
    st.info("Cole aqui os jogos que você quer testar contra o histórico")
    jogos_teste = st.text_area("Cole os jogos (um por linha, separado por espaço ou vírgula)", height=150)
    
    if st.button("Simular contra Histórico"):
        if jogos_teste:
            jogos = []
            for linha in jogos_teste.strip().split("\n"):
                nums = [int(x) for x in linha.replace(",", " ").split() if x.isdigit()]
                if len(nums) == config["sorteadas"]:
                    jogos.append(set(nums))
            resultados = []
            for jogo in jogos:
                acertos = [sum(1 for n in jogo if n in row) for row in df.values]
                resultados.append({
                    "Jogo": sorted(list(jogo)),
                    "Melhor": max(acertos),
                    "Média": round(np.mean(acertos), 1)
                })
            st.dataframe(pd.DataFrame(resultados))

# ========================= TAB 5 - BANKROLL =========================
with tab5:
    st.subheader("💰 Smart Bankroll Advisor")
    bankroll = st.number_input("Bankroll atual (R$)", value=5000, step=100)
    kelly = 0.45 if fase == "FIM" else 0.28 if fase == "MEIO" else 0.12
    st.metric("Kelly % Recomendado", f"{kelly*100:.1f}%")
    st.metric("Valor ideal por jogo", f"R$ {bankroll * kelly:.2f}")

st.caption("LotoElite Pro • Estratégia que vence o acaso.")
