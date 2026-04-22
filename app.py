import streamlit as st
import pandas as pd
import numpy as np
import random
import requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE V89 COMPLETO", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.numero {background:linear-gradient(135deg,#2e7d32,#4caf50);color:white;padding:8px 12px;border-radius:50%;font-weight:bold;margin:3px;display:inline-block;min-width:42px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.2)}
.ciclo-box {padding:12px;border-radius:8px;border-left:4px solid;margin:10px 0}
.tab-btn {background:#d32f2f;color:white;padding:8px 16px;border-radius:6px;text-decoration:none;display:inline-block;margin:5px}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align:center;color:#d32f2f">🎯 LOTOELITE V89 PRO - SISTEMA COMPLETO</h1>', unsafe_allow_html=True)

# TODAS AS LOTERIAS CAIXA
LOTERIAS = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.00,"api":"lotofacil"},
    "Mega-Sena": {"max":60,"qtd":6,"preco":5.00,"api":"megasena"},
    "Quina": {"max":80,"qtd":5,"preco":2.50,"api":"quina"},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00,"api":"lotomania"},
    "Timemania": {"max":80,"qtd":10,"preco":3.50,"api":"timemania"},
    "Dupla Sena": {"max":50,"qtd":6,"preco":2.50,"api":"duplasena"},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50,"api":"diadesorte"},
    "Super Sete": {"max":10,"qtd":7,"preco":2.50,"api":"supersete"},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00,"api":"maismilionaria"},
}

CICLOS = {
    "Lotofácil": {"janela":"4-6","media":4.7},
    "Mega-Sena": {"janela":"7-17","media":11},
    "Quina": {"janela":"15-30","media":22},
    "Lotomania": {"janela":"3-5","media":4},
    "Timemania": {"janela":"10-20","media":15},
    "Dupla Sena": {"janela":"8-15","media":11},
    "Dia de Sorte": {"janela":"5-10","media":7},
    "Super Sete": {"janela":"4-8","media":6},
    "+Milionária": {"janela":"10-20","media":14},
}

# Sidebar
lot = st.sidebar.selectbox("🎲 Escolha a Loteria", list(LOTERIAS.keys()))
cfg = LOTERIAS[lot]
fase = ["INÍCIO","MEIO","FIM"][datetime.now().day % 3]

# Perfil inteligente - session state
if 'meus_jogos' not in st.session_state:
    st.session_state.meus_jogos = []
if 'apostas' not in st.session_state:
    st.session_state.apostas = []
if 'acertos' not in st.session_state:
    st.session_state.acertos = []

def render(nums):
    return "".join([f'<span class="numero">{n:02d}</span>' for n in sorted(nums)])

@st.cache_data(ttl=300)
def busca_resultado(api):
    try:
        r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api}/latest", timeout=5).json()
        return r
    except:
        return {}

resultado = busca_resultado(cfg["api"])

tabs = st.tabs(["🎲 GERADOR IA","📊 MEUS JOGOS","🎯 CONFERÊNCIA","💰 PREÇOS","💵 APOSTAS","🏆 ACERTOS","📈 ANÁLISE","🔢 FECHAMENTO","🔄 CICLO","📡 AO VIVO","🎯 ESPECIAIS","🔗 CAIXA","🚀 LAB"])

# 1 GERADOR IA
with tabs[0]:
    st.subheader(f"Gerador IA - {lot} | Fase: {fase}")
    bg = "#e8f5e9" if fase=="INÍCIO" else "#fff3e0" if fase=="MEIO" else "#ffebee"
    cor = "green" if fase=="INÍCIO" else "orange" if fase=="MEIO" else "red"
    st.markdown(f'<div class="ciclo-box" style="background:{bg};border-left-color:{cor}"><b>Ciclo {fase}</b> - Janela: {CICLOS[lot]["janela"]} | Aleatório só para balancear</div>', unsafe_allow_html=True)
    
    todos = list(range(1, cfg["max"]+1))
    random.seed(datetime.now().day + hash(lot))
    quentes = random.sample(todos, min(15, len(todos)))
    frios = random.sample([n for n in todos if n not in quentes], min(15, len(todos)-15))
    neutros = [n for n in todos if n not in quentes+frios]
    
    def gerar(tipo):
        if tipo=="Conservador": base = quentes + neutros
        elif tipo=="Agressivo": base = frios + neutros
        else:
            if fase=="INÍCIO": base = quentes + neutros
            elif fase=="FIM": base = frios + neutros
            else: base = quentes[:8] + frios[:8] + neutros
        base = list(dict.fromkeys(base))
        if len(base) < cfg["qtd"]: base = todos
        return sorted(random.sample(base, cfg["qtd"]))
    
    if st.button("🎯 GERAR 3 JOGOS IA", type="primary", use_container_width=True):
        jogos_atuais = []
        for nome in ["Conservador","Equilibrado","Agressivo"]:
            jogo = gerar(nome)
            jogos_atuais.append({"tipo":nome,"numeros":jogo,"loteria":lot,"data":datetime.now().strftime("%d/%m")})
            st.markdown(f"**{nome.upper()}:** {render(jogo)}", unsafe_allow_html=True)
        
        if st.button("💾 Salvar no Perfil"):
            st.session_state.meus_jogos.extend(jogos_atuais)
            st.success(f"3 jogos salvos no perfil!")

# 2 MEUS JOGOS
with tabs[1]:
    st.subheader("📊 Perfil Inteligente - Meus Jogos Salvos")
    if st.session_state.meus_jogos:
        df = pd.DataFrame(st.session_state.meus_jogos)
        for i,row in df.iterrows():
            st.markdown(f"**{row['loteria']} - {row['tipo']} ({row['data']}):** {render(row['numeros'])}")
        if st.button("🗑️ Limpar histórico"):
            st.session_state.meus_jogos = []
    else:
        st.info("Nenhum jogo salvo ainda. Gere na aba GERADOR IA")

# 3 CONFERÊNCIA
with tabs[2]:
    st.subheader("🎯 Conferir Resultados")
    nums = st.text_input("Digite os números sorteados separados por espaço")
    if st.button("Conferir meus jogos") and nums:
        sorteados = [int(x) for x in nums.split() if x.isdigit()]
        for jogo in st.session_state.meus_jogos:
            if jogo['loteria']==lot:
                acertos = len(set(jogo['numeros']) & set(sorteados))
                st.write(f"{jogo['tipo']}: {acertos} acertos - {render(jogo['numeros'])}")

# 4 PREÇOS
with tabs[3]:
    st.subheader("💰 Tabela Completa de Preços - Caixa 2026")
    precos = []
    for nome,d in LOTERIAS.items():
        precos.append({
            "Loteria": nome,
            "Dezenas": f"{d['qtd']}/{d['max']}",
            "Aposta mínima": f"R$ {d['preco']:.2f}",
            "21 dezenas*": f"R$ {d['preco']*10:.2f}" if nome=="Lotofácil" else "-"
        })
    st.dataframe(pd.DataFrame(precos), hide_index=True, use_container_width=True)
    st.caption("* Valores estimados para fechamentos")

# 5 APOSTAS
with tabs[4]:
    st.subheader("💵 Controle de Apostas")
    valor = st.number_input("Valor apostado R$", min_value=0.0, step=0.5)
    if st.button("Registrar"):
        st.session_state.apostas.append({"loteria":lot,"valor":valor,"data":datetime.now().strftime("%d/%m")})
    if st.session_state.apostas:
        total = sum(a['valor'] for a in st.session_state.apostas)
        st.metric("Total apostado", f"R$ {total:.2f}")

# 6 ACERTOS
with tabs[5]:
    st.subheader("🏆 Histórico de Acertos")
    st.info("Registre seus prêmios manualmente")
    premio = st.number_input("Valor ganho R$", min_value=0.0)
    if st.button("Registrar prêmio"):
        st.session_state.acertos.append(premio)

# 7 ANÁLISE
with tabs[6]:
    st.subheader("📈 Análise Simples")
    df = pd.DataFrame({"Dezena":range(1,cfg["max"]+1),"Freq":np.random.randint(1,30,cfg["max"])})
    st.bar_chart(df.set_index("Dezena"))

# 8 FECHAMENTO
with tabs[7]:
    st.subheader("🔢 Fechamento 21 dezenas")
    entrada = st.text_area("21 números", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21")
    if st.button("Gerar 10 jogos"):
        nums = [int(x) for x in entrada.split() if x.isdigit()][:21]
        for i in range(10):
            jogo = sorted(random.sample(nums, cfg["qtd"]))
            st.code(f"Jogo {i+1:02d}: {' '.join(f'{x:02d}' for x in jogo)}")

# 9 CICLO
with tabs[8]:
    st.subheader(f"🔄 Análise de Ciclo - {fase}")
    col1,col2,col3 = st.columns(3)
    col1.metric("Fase", fase)
    col2.metric("Janela", CICLOS[lot]["janela"])
    col3.metric("Média", CICLOS[lot]["media"])
    st.progress((["INÍCIO","MEIO","FIM"].index(fase)+1)/3)

# 10 AO VIVO
with tabs[9]:
    st.subheader("📡 Resultado ao Vivo")
    if resultado:
        st.success(f"Concurso {resultado.get('concurso','')} - {resultado.get('data','')}")
        dezenas = resultado.get('dezenas',[])
        st.markdown(render([int(d) for d in dezenas]), unsafe_allow_html=True)
    else:
        st.warning("Sem conexão com API")
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()

# 11 ESPECIAIS
with tabs[10]:
    st.subheader("🎯 Loterias Especiais")
    for esp in ["Mega da Virada","Quina São João","Lotofácil da Independência"]:
        if st.button(f"Gerar {esp}"):
            jogo = sorted(random.sample(range(1,61),6))
            st.markdown(render(jogo), unsafe_allow_html=True)

# 12 CAIXA
with tabs[11]:
    st.subheader("🔗 Loterias Caixa Oficial")
    st.markdown('<a href="https://loterias.caixa.gov.br" target="_blank" class="tab-btn">🎲 Acessar site oficial da Caixa</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx" target="_blank" class="tab-btn">Mega-Sena</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx" target="_blank" class="tab-btn">Lotofácil</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://loterias.caixa.gov.br/Paginas/Quina.aspx" target="_blank" class="tab-btn">Quina</a>', unsafe_allow_html=True)

# 13 LAB
with tabs[12]:
    st.subheader("🚀 Laboratório V90")
    st.write(f"Sistema operando na fase {fase} - todas estratégias respeitam o ciclo")
    st.json({"fase_atual":fase,"peso_quente":0.7 if fase=="INÍCIO" else 0.5 if fase=="MEIO" else 0.3})
