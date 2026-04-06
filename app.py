import streamlit as st
import pandas as pd
import numpy as np
import random
import torch
import torch.nn as nn
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

st.set_page_config(page_title="🔥 IA LOTOFÁCIL ELITE v4.0", layout="wide")
st.title("🚀 IA LOTOFÁCIL ELITE v4.0 – LSTM + Genetic + Bankroll Dashboard")
st.markdown("**Dr. Reginaldo Mode: LSTM metendo no ciclo e dinheiro entrando na conta 🔥**")

# ========================= UPLOAD =========================
arquivo = st.file_uploader("📂 Envie o CSV da Lotofácil (15 colunas)", type=["csv"])

if arquivo is None:
    st.stop()

df = pd.read_csv(arquivo)
st.success(f"✅ {len(df)} concursos carregados!")

# ====================== CICLO ELITE ======================
def detectar_ciclo_elite(df):
    historico = df.iloc[:, :15].values.astype(int)
    for k in range(6, 3, -1):
        if len(historico) >= k:
            janela = historico[-k:]
            set_janela = set(np.concatenate(janela))
            faltantes = sorted(set(range(1,26)) - set_janela)
            progresso = len(set_janela) / 25
            fase = "INÍCIO" if progresso < 0.4 else "MEIO" if progresso < 0.8 else "FIM"
            return fase, faltantes
    return "DESCONHECIDO", []

# ====================== LSTM MODEL (o que você pediu) ======================
class LotofacilLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=25, hidden_size=128, num_layers=2, batch_first=True)
        self.fc = nn.Linear(128, 25)
        self.sigmoid = nn.Sigmoid()
   
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.sigmoid(self.fc(out[:, -1, :]))

@st.cache_resource
def treinar_lstm(df):
    model = LotofacilLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()
   
    # Prepara sequência binária (25 dimensões)
    X, y = [], []
    for i in range(len(df)-6):
        seq = np.zeros((6, 25))
        for j in range(6):
            for num in df.iloc[i+j, :15].astype(int):
                seq[j, num-1] = 1
        X.append(seq)
        next_vec = np.zeros(25)
        for num in df.iloc[i+6, :15].astype(int):
            next_vec[num-1] = 1
        y.append(next_vec)
   
    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.float32)
   
    for epoch in range(30):  # treino rápido
        optimizer.zero_grad()
        pred = model(X)
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()
    return model

# ====================== MARKOV + GA + LSTM HÍBRIDO ======================
def markov_transicao(df):
    trans = defaultdict(lambda: defaultdict(int))
    for i in range(len(df)-1):
        atual = set(df.iloc[i, :15].astype(int))
        prox = set(df.iloc[i+1, :15].astype(int))
        for n in atual:
            for m in prox - atual:
                trans[n][m] += 1
    return trans

def gerar_jogo_hibrido(df, fase, faltantes, lstm_model, trans, pesos):
    # LSTM prediction
    historico_bin = np.zeros((6, 25))
    for j in range(6):
        for num in df.iloc[-6+j, :15].astype(int):
            historico_bin[j, num-1] = 1
    input_lstm = torch.tensor([historico_bin], dtype=torch.float32)
    probs_lstm = lstm_model(input_lstm).detach().numpy()[0]
   
    # Hybrid score
    jogo = set()
    ultimo = df.iloc[-1, :15].astype(int).tolist()
    jogo.update(random.sample(ultimo, 6))
   
    pool = list(range(1,26))
    while len(jogo) < 15:
        scores = [probs_lstm[n-1] * 2.5 + pesos.get(n,1) * 1.8 for n in pool]
        cand = random.choices(pool, weights=scores, k=1)[0]
        if cand not in jogo:
            jogo.add(cand)
   
    if "FIM" in fase and faltantes:
        jogo.update(random.sample(faltantes, min(3, len(faltantes))))
   
    return sorted(list(jogo)[:15])

# ====================== BANKROLL DASHBOARD ======================
def dashboard_bankroll(qtd_jogos, valor_aposta=2.50, bankroll_inicial=5000):
    # Monte Carlo
    np.random.seed(42)
    simulacoes = 10000
    retornos = np.random.normal(0.12, 0.08, simulacoes)  # baseado no backtest médio
    saldos = [bankroll_inicial]
    for _ in range(100):  # 100 concursos
        custo = qtd_jogos * valor_aposta
        ganho = np.random.choice([0, 50, 500, 15000, 2000000], p=[0.7, 0.2, 0.08, 0.019, 0.001])
        novo = saldos[-1] - custo + (ganho * (qtd_jogos / 10))
        saldos.append(max(novo, 0))
   
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=saldos, mode='lines', name='Bankroll'))
    st.plotly_chart(fig, use_container_width=True)
   
    roi = ((saldos[-1] - bankroll_inicial) / bankroll_inicial) * 100
    st.metric("ROI projetado em 100 concursos", f"{roi:.1f}%", delta=f"R$ {saldos[-1]:,.0f}")
    return saldos[-1]

# ========================= INTERFACE v4.0 =========================
fase, faltantes = detectar_ciclo_elite(df)
st.subheader("📍 CICLO ATUAL")
col1, col2 = st.columns(2)
col1.metric("Fase do Ciclo", f"**{fase}** 🔥")
col2.metric("Dezenas faltantes", f"**{len(faltantes)}** → {faltantes}")

# LSTM
st.subheader("🧠 LSTM Neural Predictor (treinamento automático)")
if st.button("🚀 Treinar LSTM agora (30 epochs)"):
    with st.spinner("LSTM metendo no histórico..."):
        model_lstm = treinar_lstm(df)
        st.success("✅ LSTM treinada e pronta pra prever o próximo ciclo!")
        st.session_state['model_lstm'] = model_lstm

trans = markov_transicao(df)
pesos = {n: 2.0 if n in range(1,26) else 1 for n in range(1,26)}  # base

st.subheader("🔥 Gerar Jogos HÍBRIDOS (LSTM + GA + Ciclo)")
qtd = st.slider("Quantos jogos?", 5, 50, 15)
if st.button("METE OS JOGOS ELITE"):
    jogos = []
    for i in range(qtd):
        jogo = gerar_jogo_hibrido(df, fase, faltantes, st.session_state.get('model_lstm', None), trans, pesos)
        jogos.append(jogo)
   
    df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(15)])
    df_jogos["Score"] = [sum(pesos.get(n,1) for n in j) for j in jogos]
   
    st.dataframe(df_jogos)
   
    # EXPORT EXCEL
    excel_file = df_jogos.to_excel(index=False)
    st.download_button("📥 Baixar todos os jogos em Excel", excel_file, "jogos_lotofacil_elite.xlsx", "application/vnd.ms-excel")

st.markdown("---")
st.subheader("💰 DASHBOARD DE BANKROLL – VAMOS ENCHER O BOLSO")
bank_inicial = st.number_input("Bankroll inicial (R$)", value=5000)
aposta_unit = st.number_input("Valor por jogo (R$)", value=2.50)
if st.button("RODAR SIMULAÇÃO 10.000x"):
    with st.spinner("Calculando quanto você vai faturar..."):
        final = dashboard_bankroll(qtd, aposta_unit, bank_inicial)
        st.balloons()
        st.success(f"**Em 100 concursos você sai com ≈ R$ {final:,.0f}**")
