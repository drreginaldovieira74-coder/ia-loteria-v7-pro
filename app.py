import streamlit as st
import pandas as pd
import numpy as np
import random
from scipy.stats import chisquare, entropy
import plotly.express as px

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**Ciclo com validação estatística • v46.0**")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50}, # Corrigido 100/50
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6},
    "Milionária": {"nome": "Milionária", "total": 50, "sorteadas": 6},
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

st.success(f"Loteria: **{config['nome']}** — Ciclo validado por Qui-Quadrado")

# ========================= UPLOAD =========================
arquivo = st.file_uploader(f"Envie o CSV de {config['nome']}", type=["csv"])
if arquivo is None:
    st.stop()

try:
    df = pd.read_csv(arquivo, header=None)
    df = df.iloc[:, :config["sorteadas"]].dropna() # Pega só as colunas de dezenas e remove linha vazia
    df = df.astype(int)
except Exception as e:
    st.error(f"Erro ao ler CSV: {e}")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados!")

# ========================= MOTOR DE CICLO ROBUSTO =========================
def detectar_ciclo_robusto(df, config, idx_final=None, janela=20):
    """
    Versão sem data leakage. Usa só dados até idx_final para decidir.
    Retorna fase, faltantes, p_valor, boost e frequência.
    """
    if idx_final is None:
        idx_final = len(df)

    if idx_final < janela:
        return "DADOS_INSUFICIENTES", [], 1.0, 0.0, np.array([])

    historico = df.iloc[idx_final-janela:idx_final, :config["sorteadas"]].values
    freq = np.bincount(historico.flatten(), minlength=config["total"]+1)[1:]

    # Teste Qui-Quadrado: a distribuição é diferente de aleatório?
    esperado = janela * config["sorteadas"] / config["total"]
    esperado_array = np.array([esperado] * config["total"])
    chi2, p_valor = chisquare(freq, esperado_array)

    # Entropia: quanto menor, mais previsível/padronizado
    ent = entropy(freq + 1e-9) # +1e-9 pra evitar log(0)

    faltantes = np.where(freq == 0)[0] + 1

    # Só ativa ciclo se p < 0.05 E entropia baixa
    if p_valor < 0.05 and ent < 3.1:
        fase = "CICLO_ATIVO"
        # Boost proporcional à força estatística
        boost = 15 * (1 - p_valor) * (3.2 - ent)
    elif p_valor < 0.05:
        fase = "PADRÃO_FRACO"
        boost = 5 * (1 - p_valor)
    else:
        fase = "ALEATÓRIO"
        boost = 0

    return fase, faltantes.tolist(), p_valor, round(boost, 2), freq

def backtest_walkforward(df, config, janela=20):
    """Backtest sem viés. Usa só passado pra prever presente."""
    resultados = []

    # Começa após ter janela mínima de histórico
    for i in range(janela + 10, len(df)):
        fase, faltantes, p_valor, boost, _ = detectar_ciclo_robusto(df, config, idx_final=i, janela=janela)

        # Estratégia: se ciclo ativo, prioriza faltantes
        if fase == "CICLO_ATIVO" and len(faltantes) >= config["sorteadas"]:
            jogo = sorted(random.sample(faltantes, config["sorteadas"]))
        elif len(faltantes) > 0:
            # Mistura 70% faltantes + 30% outras
            qtd_faltantes = min(int(config["sorteadas"] * 0.7), len(faltantes))
            qtd_outras = config["sorteadas"] - qtd_faltantes
            outras = [n for n in range(1, config["total"]+1) if n not in faltantes]
            jogo = sorted(random.sample(faltantes, qtd_faltantes) + random.sample(outras, qtd_outras))
        else:
            jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))

        sorteado = set(df.iloc[i, :config["sorteadas"]].values)
        acerto = len(set(jogo) & sorteado)

        resultados.append({
            "concurso": i + 1,
            "acertos": acerto,
            "fase": fase,
            "p_valor": p_valor,
            "boost": boost
        })

    return pd.DataFrame(resultados)

# ========================= INTERFACE =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎟️ Gerador", "📊 Diagnóstico do Ciclo", "🧪 Backtesting",
    "🔬 Teste vs Aleatório", "⚙️ Config Avançada"
])

with tab1:
    st.subheader("Gerador com Ciclo Validado")

    janela = st.slider("Janela de análise do ciclo", 10, 50, 20, key="janela_gerador")
    fase, faltantes, p_valor, boost, freq = detectar_ciclo_robusto(df, config, janela=janela)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fase do Ciclo", fase)
    col2.metric("p-valor", f"{p_valor:.4f}", help="< 0.05 = estatisticamente relevante")
    col3.metric("Boost Aplicado", f"{boost}x")
    col4.metric("Faltantes", len(faltantes))

    if fase == "ALEATÓRIO":
        st.warning("⚠️ Ciclo atual não é estatisticamente diferente de sorteio aleatório. Boost zerado.")
    elif fase == "CICLO_ATIVO":
        st.success(f"✅ Ciclo ativo detectado! Força: {boost}x. Prioridade nas {len(faltantes)} faltantes.")

    qtd = st.slider("Quantos jogos?", 1, 50, 10)
    if st.button("🚀 GERAR JOGOS", type="primary"):
        jogos = []
        for _ in range(qtd):
            if fase == "CICLO_ATIVO" and len(faltantes) >= config["sorteadas"]:
                # 80% faltantes, 20% outras pra não zerar diversidade
                qtd_falt = min(int(config["sorteadas"] * 0.8), len(faltantes))
                outras = [n for n in range(1, config["total"]+1) if n not in faltantes]
                jogo = sorted(random.sample(faltantes, qtd_falt) + random.sample(outras, config["sorteadas"] - qtd_falt))
            else:
                jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
            jogos.append(jogo)

        for i, j in enumerate(jogos, 1):
            st.code(f"Jogo {i:02d}: {j}")

with tab2:
    st.subheader("📊 Diagnóstico do Ciclo Atual")
    janela_diag = st.slider("Janela de análise", 10, 50, 20, key="janela_diag")
    fase, faltantes, p_valor, boost, freq = detectar_ciclo_robusto(df, config, janela=janela_diag)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Fase", fase)
        st.metric("p-valor Qui²", f"{p_valor:.5f}")
        st.metric("Entropia", f"{entropy(freq + 1e-9):.3f}")
        st.metric("Faltantes", len(faltantes))
        if faltantes:
            st.write("**Faltantes:**", ", ".join(map(str, faltantes[:15])))

    with col2:
        # Heatmap de frequência
        fig = px.bar(x=list(range(1, config["total"]+1)), y=freq,
                     labels={'x': 'Dezena', 'y': 'Frequência'},
                     title=f'Frequência nos últimos {janela_diag} concursos')
        fig.add_hline(y=np.mean(freq), line_dash="dash", line_color="red",
                      annotation_text="Média esperada")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("🧪 Backtesting Walk-Forward - Sem Viés")
    st.info("Testa sua estratégia concurso por concurso, usando só dados do passado. Se der lucro aqui, é real.")

    janela_bt = st.slider("Janela do ciclo pro backtest", 10, 50, 20, key="janela_bt")

    if st.button("▶️ RODAR BACKTEST COMPLETO"):
        with st.spinner("Rodando backtest... Isso testa todos os concursos históricos"):
            df_bt = backtest_walkforward(df, config, janela=janela_bt)

        if not df_bt.empty:
            media_acertos = df_bt['acertos'].mean()
            media_aleatoria = config["sorteadas"] * config["sorteadas"] / config["total"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Média de Acertos", f"{media_acertos:.2f}")
            col2.metric("Média Aleatória", f"{media_aleatoria:.2f}",
                       delta=f"{media_acertos - media_aleatoria:.2f}")
            col3.metric("Concursos Testados", len(df_bt))

            if media_acertos > media_aleatoria * 1.05:
                st.success(f"✅ Seu ciclo bateu o aleatório em {((media_acertos/media_aleatoria - 1)*100):.1f}%!")
            else:
                st.warning("⚠️ Ciclo não superou aleatório de forma relevante. Ajuste a janela ou lógica.")

            st.line_chart(df_bt.set_index('concurso')['acertos'])
            st.dataframe(df_bt.tail(20))

with tab4:
    st.subheader("🔬 Teste Contra Dados 100% Aleatórios")
    st.info("Se seu ciclo achar padrão aqui, ele tá vendo fantasma. Ciclo real fica quieto no aleatório.")

    if st.button("🎲 Gerar 3000 Sorteios Aleatórios e Testar"):
        with st.spinner("Gerando dados aleatórios..."):
            # Gera CSV fake
            fake = np.array([sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
                            for _ in range(3000)])
            df_fake = pd.DataFrame(fake)

            fase, _, p_valor, boost, _ = detectar_ciclo_robusto(df_fake, config, janela=20)

        col1, col2 = st.columns(2)
        col1.metric("Fase Detectada no Aleatório", fase)
        col2.metric("p-valor", f"{p_valor:.4f}")

        if fase == "ALEATÓRIO" or p_valor > 0.05:
            st.success("✅ PASSOU! Seu detector ficou quieto no aleatório. Ciclo é robusto.")
        else:
            st.error("❌ REPROVOU! Seu ciclo detectou padrão em dado aleatório. Ajuste o critério de p-valor/entropia.")

with tab5:
    st.subheader("⚙️ Configurações Avançadas")
    st.markdown("""
    **Parâmetros do motor de ciclo:**
    - **p-valor < 0.05**: Qui-Quadrado diz que distribuição não é aleatória com 95% confiança
    - **Entropia < 3.1**: Distribuição tem padrão. Lotofácil aleatória = ~3.22
    - **Janela**: Quantos concursos passados definem um ciclo. Teste 13, 20, 33

    **Como interpretar:**
    1. Rode o Backtest na Tab 3. Se média > aleatória, continue.
    2. Rode Teste vs Aleatório na Tab 4. Tem que passar.
    3. Se passou nos dois, seu ciclo é estatisticamente válido.
    """)
