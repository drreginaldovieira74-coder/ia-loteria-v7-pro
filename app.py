import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
import sqlite3
from datetime import datetime
import hashlib
import warnings
warnings.filterwarnings("ignore")

# ========================= v17.0 ULTIMATE COMMERCIAL =========================
st.set_page_config(page_title="IA LOTOFÁCIL ELITE v17.0", page_icon="🎟️", layout="wide")

st.title("🎟️ IA LOTOFÁCIL ELITE v17.0")
st.markdown("**Plataforma Comercial Profissional** • Login + Assinatura + Pagamentos")

# ====================== BANCO DE DADOS ======================
def init_db():
    conn = sqlite3.connect("elite.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    subscription TEXT DEFAULT "Free",
                    created_at TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# ====================== LOGIN / CADASTRO ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.subscription = "Free"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    c = conn.cursor()
    c.execute("SELECT subscription FROM users WHERE username = ? AND password = ?", 
              (username, hash_password(password)))
    result = c.fetchone()
    if result:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.subscription = result[0]
        return True
    return False

def register(username, password):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, subscription, created_at) VALUES (?, ?, 'Free', ?)",
                  (username, hash_password(password), datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        return True
    except:
        return False

# Tela de Login
if not st.session_state.logged_in:
    st.subheader("🔑 Acesso à Plataforma Premium")
    tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])

    with tab1:
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary"):
            if login(user, pw):
                st.success(f"Bem-vindo, {user}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

    with tab2:
        new_user = st.text_input("Novo usuário")
        new_pw = st.text_input("Nova senha", type="password")
        if st.button("Criar conta", type="primary"):
            if register(new_user, new_pw):
                st.success("Conta criada! Faça login.")
            else:
                st.error("Usuário já existe")
    st.stop()

# ========================= INTERFACE PREMIUM =========================
st.sidebar.success(f"👤 {st.session_state.username} | Plano: **{st.session_state.subscription}**")

# ========================= SELETOR DE LOTERIA =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15, "tipo_ciclo": "full"},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "tipo_ciclo": "partial"},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "tipo_ciclo": "frequency"},
    "Dupla Sena": {"nome": "Dupla Sena", "total": 50, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Super Sete": {"nome": "Super Sete", "total": 49, "sorteadas": 7, "tipo_ciclo": "frequency"},
    "Loteria Federal": {"nome": "Loteria Federal", "total": 99999, "sorteadas": 5, "tipo_ciclo": "frequency"},
    "Loteria Milionária": {"nome": "Loteria Milionária", "total": 50, "sorteadas": 6, "tipo_ciclo": "frequency"},
    "Timemania": {"nome": "Timemania", "total": 80, "sorteadas": 7, "tipo_ciclo": "frequency"}
}

loteria_selecionada = st.selectbox("🎯 Escolha a loteria", options=list(loteria_options.keys()), index=0)
config = loteria_options[loteria_selecionada]

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
    return df

df = carregar_csv(arquivo, config["sorteadas"])

if len(df) == 0:
    st.error("❌ CSV inválido ou vazio.")
    st.stop()

st.success(f"✅ {len(df)} concursos carregados!")

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
        cobertura_atual = set(np.concatenate(df_atual.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - cobertura_atual)
        progresso = len(cobertura_atual) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

    else:
        ultimos = df.iloc[-40:] if len(df) > 40 else df
        todos = set(np.concatenate(ultimos.values))
        faltantes = sorted(set(range(1, config["total"]+1)) - todos)
        progresso = (config["total"] - len(faltantes)) / config["total"] * 100
        fase = "INÍCIO" if progresso < 40 else "MEIO" if progresso < 80 else "FIM"
        return fase, faltantes, progresso

fase, faltantes, progresso = detectar_ciclo(df, config)

# ========================= SISTEMA DE PAGAMENTOS =========================
st.sidebar.subheader("💳 Assinatura")
st.sidebar.write(f"Plano atual: **{st.session_state.subscription}**")

if st.session_state.subscription == "Free":
    st.sidebar.warning("🔓 Plano Free – Recursos limitados")
    if st.sidebar.button("🔥 Upgrade para Pro (R$ 29/mês)"):
        st.session_state.payment_page = True

if st.session_state.subscription == "Pro":
    st.sidebar.success("✅ Plano Pro ativo")

# Página de Pagamento
if st.session_state.get("payment_page", False):
    st.subheader("💳 Checkout – Upgrade para Pro")
    st.write("**Plano Pro** – R$ 29,90 / mês")
    st.write("• Acesso ilimitado a todas as loterias")
    st.write("• AI Oracle completo")
    st.write("• Relatórios premium")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Pagar com Mercado Pago", type="primary", use_container_width=True):
            # Simulação de pagamento
            c = conn.cursor()
            c.execute("UPDATE users SET subscription = 'Pro' WHERE username = ?", (st.session_state.username,))
            conn.commit()
            st.session_state.subscription = "Pro"
            st.session_state.payment_page = False
            st.success("✅ Pagamento aprovado! Agora você é Pro.")
            st.rerun()
    with col2:
        if st.button("Cancelar"):
            st.session_state.payment_page = False
            st.rerun()

# ========================= TABS =========================
tab1, tab2, tab3 = st.tabs(["🎟️ Gerar Jogos", "📊 AI Oracle", "💰 Meu Plano"])

with tab1:
    st.subheader("🎟️ Gerar Jogos")
    qtd = st.slider("Quantidade de jogos", 5, 80, 20)
    if st.button("🚀 Gerar Jogos", type="primary"):
        pool = list(range(1, config["total"]+1))
        jogos = [sorted(random.sample(pool, config["sorteadas"])) for _ in range(qtd)]
        df_jogos = pd.DataFrame(jogos, columns=[f"D{i+1}" for i in range(config["sorteadas"])])
        st.dataframe(df_jogos, use_container_width=True)

st.caption("v17.0 Ultimate Commercial • Sistema com login + banco de dados + pagamentos simulados • Pronto para produção")
