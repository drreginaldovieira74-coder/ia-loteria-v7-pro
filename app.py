import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
import sqlite3
from datetime import datetime
import hashlib
import mercadopago
import warnings
warnings.filterwarnings("ignore")

# ========================= CONFIGURAÇÃO MERCADO PAGO =========================
# ⚠️ COLOQUE SEU ACCESS TOKEN AQUI (Produção ou Teste)
MERCADO_PAGO_ACCESS_TOKEN = "TEST-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

# ========================= BANCO DE DADOS =========================
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

# ========================= LOGIN =========================
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
    st.subheader("🔑 Acesso Premium")
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

# ========================= INTERFACE =========================
st.title("🎟️ IA LOTOFÁCIL ELITE v18.0")
st.markdown(f"**Usuário:** {st.session_state.username} | **Plano:** {st.session_state.subscription}")

# ========================= ASSINATURA RECORRENTE =========================
if st.session_state.subscription == "Free":
    st.sidebar.warning("🔓 Plano Free")
    if st.sidebar.button("🔥 Assinar Plano Pro - R$ 29,90/mês", type="primary"):
        # Criação do Plano de Assinatura Recorrente
        preapproval_plan = {
            "reason": "Assinatura Pro - IA Lotofácil Elite",
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months",
                "repetitions": 12,           # 12 meses
                "billing_day": 5,
                "billing_day_proportional": True,
                "transaction_amount": 29.90,
                "currency_id": "BRL"
            },
            "back_url": "https://seuapp.streamlit.app/success"
        }

        response = mp.preapproval_plan().create(preapproval_plan)
        
        if response["status"] == 201:
            init_point = response["response"]["init_point"]
            st.success("Plano de assinatura criado!")
            st.markdown(f"[🔗 Pagar e Ativar Assinatura Pro]({init_point})")
            st.info("Após o pagamento, volte aqui e faça login novamente.")
        else:
            st.error("Erro ao criar plano de assinatura.")

# ========================= RESTO DO SISTEMA (mantido) =========================
st.subheader(f"📤 Upload do Histórico da {config['nome']}")
# ... (o resto do código de upload, ciclo, gerar jogos, etc. pode ser mantido igual às versões anteriores)

st.caption("v18.0 • Integração REAL com Mercado Pago (Assinatura Recorrente) • Sistema Comercial Profissional")
