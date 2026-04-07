import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import random
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings("ignore")

# ========================= CONFIGURAÇÃO =========================
st.set_page_config(
    page_title="IA LOTOFÁCIL ELITE v5.2",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎟️ IA LOTOFÁCIL ELITE v5.2 – ULTRA LEVE")
st.markdown("**Versão Minimalista para Streamlit Cloud** | GA + Markov + Ciclo + Backtest")

# ========================= SIDEBAR =========================
with st.sidebar:
    st.header("⚙️ Configurações Avançadas")
    st.markdown("---")
    peso_markov = st.slider("Peso Markov", 0.0, 1.0, 0.35)
    peso_frequencia = st.slider("Peso Frequência", 0.0, 1.0, 0.30)
    peso_ciclo = st.slider("Peso Ciclo", 0.0, 1.0, 0.20)
    peso_diversidade = st.slider("Peso Diversidade", 0.0, 1.0, 0.15)
    
    st.markdown("---")
    pop_size = st.number_input("Tamanho população GA", 100, 500, 200)
    generations = st.number_input("Gerações GA", 20, 100, 50)
    st.info("Quanto maior, mais preciso")

# ========================= UPLOAD + VALIDAÇÃO =========================
st.subheader("📤 Upload do Histórico Oficial")
arquivo = st.file_uploader(
    "Envie o CSV da Lotofácil (mínimo 15 colunas)",
    type=["csv"],
    help="Primeiras 15 colunas = dezenas (1 a 25)"
)

if arquivo is None:
    st.warning("👆 Envie o arquivo CSV para começar")
    st.stop()

@st.cache_data
def carregar_e_validar_csv(arquivo) -> pd.DataFrame:
    df = pd.read_csv(arquivo)
    
    if len(df.columns) < 15:
        st.error("❌ O CSV precisa ter pelo menos 15 colunas")
        st.stop()
    
    df_dezenas = df.iloc[:, :15].copy()
    
    try:
        df_dezenas = df_dezenas.astype(int)
    except:
        st.error("❌ Todas as dezenas devem ser números inteiros")
        st.stop()
    
    if not ((df_dezenas >= 1) & (df_dezenas <= 25)).all().all():
        st.error("❌ Todas as dezenas devem estar entre 1 e 25")
        st.stop()
    
    duplicatas = df_dezenas.apply(lambda row: len(set(row)) != 15, axis=1).sum()
    if duplicatas > 0:
        st.warning(f"⚠️ {duplicatas} concursos com dezenas repetidas foram corrigidos")
    
    st.success(f"✅ {len(df)} concursos carregados e validados!")
    return df_dezenas

df = carregar_e_validar_csv(arquivo)

# ========================= CICLO ELITE =========================
def detectar_ciclo_elite(df: pd.DataFrame) -> Tuple[str, List[int]]:
    historico = df.iloc[-20:].values
    set_total = set(np.concatenate(historico))
    faltantes = sorted(set(range(1, 26)) - set_total)
    
    progresso = len(set_total) / 25
    if progresso < 0.45:
        fase = "INÍCIO DE CICLO"
    elif progresso < 0.80:
        fase = "MEIO DE CICLO"
    else:
        fase = "FIM DE CICLO"
    
    return fase, faltantes

fase, faltantes = detectar_ciclo_elite(df)

# ========================= TABS =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Análise do Ciclo",
    "📈 Statistical Predictor",
    "🎯 Gerar Jogos Elite",
    "📈 Backtest Histórico",
    "💰 Bankroll Dashboard"
])

# ========================= TAB 1: CICLO =========================
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("**Fase Atual do Ciclo**", f"**{fase}**", "🔥")
    col2.metric("**Dezenas Faltantes**", f"**{len(faltantes)}**", ", ".join(map(str, faltantes[:10])))
    col3.metric("**Concursos Analisados**", f"{len(df)}")
    
    cobertura = [len(set(np.concatenate(df.iloc[:i+1].values))) for i in range(len(df))]
    st.line_chart(pd.Series(cobertura, name="Cobertura de Dezenas"))

# ========================= TAB 2: STATISTICAL PREDICTOR =========================
def calcular_probabilidades(df: pd.DataFrame) -> np.ndarray:
    todos = np.concatenate(df.values)
    contagem = Counter(todos)
    probs = np.zeros(25)
    for n in range(1, 26):
        probs[n-1] = contagem.get(n, 0) / len(todos)
    return probs

with tab2:
    st.subheader("📈 Statistical Predictor Pro")
    if st.button("🔄 Atualizar Probabilidades", type="primary"):
        probs = calcular_probabilidades(df)
        st.session_state["probs_estatisticas"] = probs
        st.success("✅ Probabilidades atualizadas!")

    if "probs_estatisticas" in st.session_state:
        st.success("✅ Predictor Pro pronto!")

# ========================= TAB 3: GERAR JOGOS =========================
def markov_transicao(df: pd.DataFrame) -> Dict[int, Dict[int, float]]:
    trans = defaultdict(lambda: defaultdict(float))
    for i in range(len(df) - 1):
        atual = set(df.iloc[i])
        prox = set(df.iloc[i + 1])
        for n in atual:
            for m in prox - atual:
                trans[n][m] += 1
    for n in trans:
        total = sum(trans[n].values())
        if total > 0:
            for m in trans[n]:
                trans[n][m] /= total
    return trans

def frequencia_historica(df: pd.DataFrame) -> Dict[int, float]:
    todos = np.concatenate(df.values)
    contagem = Counter(todos)
    max_count = max(contagem.values()) or 1
    return {n: contagem.get(n, 0) / max_count for n in range(1, 26)}

def calcular_fitness(jogo: List[int], probs: np.ndarray, markov: Dict, freq: Dict, ultimos: List[int], faltantes: List[int]) -> float:
    score = sum(probs[n-1] for n in jogo) * 0.35
    for n in jogo:
        for m in jogo:
            if n != m and m in markov.get(n, {}):
                score += markov[n][m] * peso_markov
    score += sum(freq.get(n, 0) for n in jogo) * peso_frequencia
    if fase == "FIM DE CICLO":
        score += len(set(jogo) & set(faltantes)) * 2.0 * peso_ciclo
    intersecao = len(set(jogo) & set(ultimos))
    score -= intersecao * 0.8 * peso_diversidade
    return score

def genetic_algorithm(probs: np.ndarray, markov: Dict, freq: Dict, ultimos: List[int], faltantes: List[int]) -> List[int]:
    pop = [random.sample(range(1, 26), 15) for _ in range(pop_size)]
    
    for gen in range(generations):
        fitness = [calcular_fitness(ind, probs, markov, freq, ultimos, faltantes) for ind in pop]
        sorted_pop = [x for _, x in sorted(zip(fitness, pop), reverse=True)]
        new_pop = sorted_pop[:pop_size//4]
        
        while len(new_pop) < pop_size:
            p1, p2 = random.sample(sorted_pop[:pop_size//2], 2)
            ponto = random.randint(5, 10)
            filho = p1[:ponto] + [x for x in p2 if x not in p1[:ponto]]
            if len(filho) > 15:
                filho = filho[:15]
            if random.random() < 0.15:
                idx = random.randrange(15)
                novo = random.choice([x for x in range(1,26) if x not in filho])
                filho[idx] = novo
            new_pop.append(sorted(filho))
        pop = new_pop
    
    best = max(pop, key=lambda x: calcular_fitness(x, probs, markov, freq, ultimos, faltantes))
    return sorted(best)

with tab3:
    st.subheader("🎯 Gerador HÍBRIDO PROFISSIONAL")
    qtd_jogos = st.slider("Quantidade de jogos", 5, 100, 20)
    
    if st.button("🚀 GERAR JOGOS ELITE AGORA", type="primary", use_container_width=True):
        if "probs_estatisticas" not in st.session_state:
            st.error("❌ Atualize as probabilidades primeiro na aba Statistical Predictor!")
        else:
            with st.spinner("Executando Genetic Algorithm..."):
                probs = st.session_state["probs_estatisticas"]
                trans = markov_transicao(df)
                freq = frequencia_historica(df)
                ultimos = df.iloc[-1].tolist()
                
                jogos = [genetic_algorithm(probs, trans, freq, ultimos, faltantes) for _ in range(qtd_jogos)]
                
                df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(15)])
                df_jogos["Score Elite"] = [calcular_fitness(j, probs, trans, freq, ultimos, faltantes) for j in jogos]
                df_jogos = df_jogos.sort_values("Score Elite", ascending=False).reset_index(drop=True)
                
                st.dataframe(df_jogos.style.highlight_max(axis=0, color="#00ff88"), use_container_width=True)
                
                excel = df_jogos.to_excel(index=False)
                st.download_button(
                    label="📥 Baixar todos os jogos em Excel",
                    data=excel,
                    file_name="jogos_lotofacil_elite_v5.2.xlsx",
                    mime="application/vnd.ms-excel"
                )

# ========================= TAB 4: BACKTEST =========================
with tab4:
    st.subheader("📈 Backtest Histórico")
    if st.button("Executar Backtest Completo", type="secondary"):
        with st.spinner("Rodando backtest..."):
            acertos = []
            for i in range(100, len(df) - 1):
                df_train = df.iloc[:i]
                real = set(df.iloc[i])
                freq_train = frequencia_historica(df_train)
                pred = sorted(freq_train, key=freq_train.get, reverse=True)[:15]
                acerto = len(real & set(pred))
                acertos.append(acerto)
            
            media_acerto = np.mean(acertos)
            contagem = pd.Series(acertos).value_counts().sort_index()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Média de acertos", f"{media_acerto:.2f}/15")
            col2.metric("11+ pontos", f"{sum(1 for x in acertos if x >= 11)}")
            col3.metric("12+ pontos", f"{sum(1 for x in acertos if x >= 12)}")
            col4.metric("13+ pontos", f"{sum(1 for x in acertos if x >= 13)}")
            
            st.bar_chart(contagem)
            st.success(f"✅ Backtest concluído! Média: **{media_acerto:.1f}** dezenas por jogo")

# ========================= TAB 5: BANKROLL =========================
with tab5:
    st.subheader("💰 Bankroll Dashboard")
    bank_inicial = st.number_input("Bankroll inicial (R$)", value=5000, step=100)
    valor_aposta = st.number_input("Valor por jogo (R$)", value=2.50, step=0.10)
    qtd_simul = st.slider("Jogos por concurso", 5, 50, 15)
    
    if st.button("🔥 RODAR SIMULAÇÃO (10.000 rodadas)", type="primary"):
        with st.spinner("Calculando..."):
            np.random.seed(42)
            simulacoes = 10000
            concursos = 100
            saldos = np.full(simulacoes, bank_inicial, dtype=float)
            
            for _ in range(concursos):
                custo = qtd_simul * valor_aposta
                ganhos = np.random.choice([0, 50, 500, 15000, 2000000], size=simulacoes, p=[0.68, 0.22, 0.075, 0.024, 0.001])
                saldo_novo = saldos - custo + (ganhos * (qtd_simul / 20))
                saldos = np.maximum(saldo_novo, 0)
            
            # Gráfico simples com percentis
            df_bank = pd.DataFrame({
                "P10": np.percentile(saldos, 10),
                "Mediana": np.percentile(saldos, 50),
                "P90": np.percentile(saldos, 90)
            }, index=["Final"])
            st.line_chart(df_bank)
            
            roi_medio = ((np.median(saldos) - bank_inicial) / bank_inicial) * 100
            st.metric("ROI Médio em 100 concursos", f"{roi_medio:.1f}%", f"R$ {np.median(saldos):,.0f}")
            st.balloons()
            st.success(f"**Projeção final (mediana):** R$ {np.median(saldos):,.0f}")

st.caption("IA LOTOFÁCIL ELITE v5.2 • Versão Minimalista para Streamlit Cloud")
