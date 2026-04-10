import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**Ciclo com validação estatística • v46.4 - Estável**")

# ========================= FUNÇÕES SEM SCIPY =========================
def qui_quadrado_manual(freq_obs, freq_esp):
    chi2 = np.sum((freq_obs - freq_esp) ** 2 / (freq_esp + 1e-9))
    return chi2

def p_valor_aproximado(chi2, gl):
    # Tabela de valores críticos 95% confiança
    criticos = {24: 36.4, 49: 66.3, 59: 77.9, 79: 100.7, 99: 123.2}
    critico = criticos.get(gl, 40)
    if chi2 > critico * 1.5: return 0.01
    elif chi2 > critico: return 0.04
    else: return 0.5

def entropia(x):
    x = x[x > 0]
    if len(x) == 0: return 0
    p = x / np.sum(x)
    return -np.sum(p * np.log(p))

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6},
}

loteria = st.selectbox("🎯 Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]
st.success(f"Loteria: **{config['nome']}**")

arquivo = st.file_uploader(f"Envie o CSV de {config['nome']}", type=["csv"])
if arquivo is None:
    st.stop()

df = pd.read_csv(arquivo, header=None)
df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
st.success(f"✅ {len(df)} concursos carregados!")

# ========================= MOTOR DE CICLO =========================
def detectar_ciclo(df, config, idx_final=None, janela=20):
    if idx_final is None: idx_final = len(df)
    if idx_final < janela: return "DADOS_INSUFICIENTES", [], 1.0, 0.0, np.array([])

    historico = df.iloc[idx_final-janela:idx_final, :config["sorteadas"]].values
    freq = np.bincount(historico.flatten(), minlength=config["total"]+1)[1:]
    esperado = janela * config["sorteadas"] / config["total"]
    esperado_array = np.array([esperado] * config["total"])

    chi2 = qui_quadrado_manual(freq, esperado_array)
    p_valor = p_valor_aproximado(chi2, config["total"] - 1)
    ent = entropia(freq + 1e-9)
    faltantes = np.where(freq == 0)[0] + 1

    if p_valor < 0.05 and ent < 3.1:
        fase = "CICLO_ATIVO"
        boost = 15 * (1 - p_valor) * (3.2 - ent)
    elif p_valor < 0.05:
        fase = "PADRÃO_FRACO"
        boost = 5 * (1 - p_valor)
    else:
        fase = "ALEATÓRIO"
        boost = 0
    return fase, faltantes.tolist(), p_valor, round(boost, 2), freq

def backtest(df, config, janela=20):
    res = []
    for i in range(janela + 10, len(df)):
        fase, faltantes, p_valor, boost, _ = detectar_ciclo(df, config, idx_final=i, janela=janela)
        if fase == "CICLO_ATIVO" and len(faltantes) >= config["sorteadas"]:
            jogo = sorted(random.sample(faltantes, config["sorteadas"]))
        elif len(faltantes) > 0:
            qtd_f = min(int(config["sorteadas"] * 0.7), len(faltantes))
            outras = [n for n in range(1, config["total"]+1) if n not in faltantes]
            jogo = sorted(random.sample(faltantes, qtd_f) + random.sample(outras, config["sorteadas"] - qtd_f))
        else:
            jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
        sorteado = set(df.iloc[i, :config["sorteadas"]].values)
        res.append({"concurso": i+1, "acertos": len(set(jogo) & sorteado), "fase": fase, "p_valor": p_valor})
    return pd.DataFrame(res)

# ========================= ABAS VOLTARAM =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎟️ Gerador", "📊 Diagnóstico", "🧪 Backtesting", "🔬 Teste Aleatório"
])

with tab1:
    st.subheader("Gerador com Ciclo Validado")
    janela = st.slider("Janela do ciclo", 10, 50, 20, key="j1")
    fase, faltantes, p_valor, boost, freq = detectar_ciclo(df, config, janela=janela)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase", fase)
    c2.metric("p-valor", f"{p_valor:.2f}")
    c3.metric("Boost", f"{boost}x")
    c4.metric("Faltantes", len(faltantes))

    if fase == "CICLO_ATIVO":
        st.success(f"✅ Ciclo ativo! Priorize as {len(faltantes)} faltantes")
    else:
        st.warning("⚠️ Sem ciclo estatístico. Jogando no aleatório")

    qtd = st.slider("Quantos jogos?", 1, 50, 10, key="q1")
    if st.button("🚀 GERAR JOGOS", type="primary"):
        for i in range(qtd):
            if fase == "CICLO_ATIVO" and len(faltantes) >= config["sorteadas"]:
                qtd_f = min(int(config["sorteadas"] * 0.8), len(faltantes))
                outras = [n for n in range(1, config["total"]+1) if n not in faltantes]
                jogo = sorted(random.sample(faltantes, qtd_f) + random.sample(outras, config["sorteadas"] - qtd_f))
            else:
                jogo = sorted(random.sample(range(1, config["total"]+1), config["sorteadas"]))
            st.code(f"Jogo {i+1:02d}: {jogo}")

with tab2:
    st.subheader("📊 Diagnóstico do Ciclo")
    janela = st.slider("Janela", 10, 50, 20, key="j2")
    fase, faltantes, p_valor, boost, freq = detectar_ciclo(df, config, janela=janela)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Fase", fase)
        st.metric("p-valor", f"{p_valor:.2f}")
        st.metric("Entropia", f"{entropia(freq + 1e-9):.3f}")
        st.metric("Faltantes", len(faltantes))
        if faltantes: st.write("**Faltantes:**", ", ".join(map(str, faltantes[:20])))
    with c2:
        df_freq = pd.DataFrame({'Dezena': range(1, config["total"]+1), 'Freq': freq})
        st.bar_chart(df_freq.set_index('Dezena'))
        st.caption(f"Média esperada: {np.mean(freq):.2f}")

with tab3:
    st.subheader("🧪 Backtesting Walk-Forward")
    st.info("Testa o ciclo concurso por concurso usando só o passado")
    janela = st.slider("Janela do ciclo", 10, 50, 20, key="j3")
    if st.button("▶️ RODAR BACKTEST"):
        with st.spinner("Rodando..."):
            df_bt = backtest(df, config, janela=janela)
        if not df_bt.empty:
            media = df_bt['acertos'].mean()
            aleat = config["sorteadas"] * config["sorteadas"] / config["total"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Média Acertos", f"{media:.2f}")
            c2.metric("Média Aleatória", f"{aleat:.2f}", delta=f"{media - aleat:.2f}")
            c3.metric("Testados", len(df_bt))
            if media > aleat * 1.05:
                st.success(f"✅ Bateu o aleatório em {((media/aleat - 1)*100):.1f}%!")
            else:
                st.warning("⚠️ Não superou aleatório")
            st.line_chart(df_bt.set_index('concurso')['acertos'])

with tab4:
    st.subheader("🔬 Teste Contra Aleatório")
    st.info("Se detectar ciclo aqui, seu critério tá errado")
    if st.button("🎲 Testar com 3000 Sorteios Aleatórios"):
        with st.spinner("Gerando..."):
            fake = np.array([sorted(random.sample(range(1, config["total"]+1), config["sorteadas"])) for _ in range(3000)])
            df_fake = pd.DataFrame(fake)
            fase, _, p_valor, _, _ = detectar_ciclo(df_fake, config, janela=20)
        c1, c2 = st.columns(2)
        c1.metric("Fase no Aleatório", fase)
        c2.metric("p-valor", f"{p_valor:.2f}")
        if fase == "ALEATÓRIO" or p_valor > 0.05:
            st.success("✅ PASSOU! Não vê fantasma no aleatório")
        else:
            st.error("❌ REPROVOU! Ajuste o critério")
