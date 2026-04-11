import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
from itertools import combinations
import io

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO v52.2")
st.markdown("**8 Abas | Moldura | Colunas | Repetidas | PDF | Ciclo Corrigido**")

loteria_options = {
    "Lotofacil": {"nome": "Lotofacil", "total": 25, "sorteadas": 15, "mantidas": [9, 11], "ciclo_esperado": [4, 6], "fase_limites": [2, 4]},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "mantidas": [35, 40], "ciclo_esperado": [8, 12], "fase_limites": [4, 8]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3], "ciclo_esperado": [35, 50], "fase_limites": [15, 35]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4], "ciclo_esperado": [22, 30], "fase_limites": [10, 22]},
    "Milionaria": {"nome": "Milionaria", "total": 50, "sorteadas": 6, "mantidas": [3, 4], "ciclo_esperado": [18, 25], "fase_limites": [8, 18]}
}

if 'historico_perfil' not in st.session_state:
    st.session_state.historico_perfil = []

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]

st.success("**{}** - Ciclo {}-{} sorteios | Mantem {}-{} | Total {} dezenas".format(
    config['nome'], config['ciclo_esperado'][0], config['ciclo_esperado'][1],
    config['mantidas'][0], config['mantidas'][1], config['total']
))

arquivo = st.file_uploader("CSV de {}".format(config['nome']), type=["csv"])
if arquivo is None:
    st.warning("Envie o CSV pra continuar")
    st.stop()

try:
    df = pd.read_csv(arquivo, header=None)
    df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
    st.success("OK {} concursos carregados!".format(len(df)))
except Exception as e:
    st.error("Erro ao ler CSV: {}".format(e))
    st.stop()

def analisar_ciclo_completo(df, config):
    total = config["total"]
    ciclo_min, ciclo_max = config["ciclo_esperado"]
    lim_inicio, lim_meio = config["fase_limites"]
    
    ciclos = []
    ciclo_atual = []
    dezenas_vistas = set()

    for idx, row in df.iterrows():
        nums = [int(x) for x in row.values if 1 <= int(x) <= total]
        ciclo_atual.append(idx)
        dezenas_vistas.update(nums)
        if len(dezenas_vistas) >= total:
            ciclos.append({
                "inicio": ciclo_atual[0], "fim": ciclo_atual[-1],
                "duracao": len(ciclo_atual),
                "dezenas_final": set(nums)
            })
            ciclo_atual = []
            dezenas_vistas = set()

    faltantes = sorted(set(range(1, total+1)) - dezenas_vistas)
    progresso = len(dezenas_vistas) / total if total > 0 else 0.0
    progresso = float(max(0.0, min(1.0, progresso)))
    sorteios_ciclo = len(ciclo_atual)

    if sorteios_ciclo == 0: 
        fase = "ZERADO"
    elif sorteios_ciclo <= lim_inicio: 
        fase = "INICIO"
    elif sorteios_ciclo <= lim_meio: 
        fase = "MEIO"
    else: 
        fase = "FIM"

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    freq = np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:]
    quentes = [int(x) for x in np.argsort(freq)[-15:][::-1] + 1 if 1 <= x <= total]
    ultimo = [int(x) for x in df.iloc[-1].values if 1 <= int(x) <= total]

    return {
        "fase": fase, "faltantes": [int(x) for x in faltantes], "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "memoria": [int(x) for x in memoria],
        "ciclos_hist": ciclos, "previsao_fecha": max(0, ciclo_max - sorteios_ciclo),
        "quentes": quentes, "ultimo": ultimo, "ciclo_esperado": config["ciclo_esperado"]
    }

MOLDURA = {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}
COLUNAS = {1:[1,6,11,16,21], 2:[2,7,12,17,22], 3:[3,8,13,18,23], 4:[4,9,14,19,24], 5:[5,10,15,20,25]}

def aplicar_filtros(jogo, filtros, analise):
    if not filtros.get("ativo", False):
        return True, []
    
    reprovados = []
    fase = analise["fase"]
    
    if filtros.get("soma", {}).get("ativo") and fase in filtros["soma"].get("fases", ["MEIO", "FIM"]):
        s = sum(jogo)
        if not (filtros["soma"]["min"] <= s <= filtros["soma"]["max"]):
            reprovados.append("Soma")
    
    if filtros.get("pares", {}).get("ativo"):
        pares = len([x for x in jogo if x % 2 == 0])
        if not (filtros["pares"]["min"] <= pares <= filtros["pares"]["max"]):
            reprovados.append("Pares")
    
    if filtros.get("moldura", {}).get("ativo") and config["nome"] == "Lotofacil":
        m = len([n for n in jogo if n in MOLDURA])
        if not (filtros["moldura"]["min"] <= m <= filtros["moldura"]["max"]):
            reprovados.append("Moldura")
    
    if filtros.get("colunas", {}).get("ativo") and config["nome"] == "Lotofacil":
        c = len([col for col, nums in COLUNAS.items() if any(n in jogo for n in nums)])
        if c < filtros["colunas"]["min"]:
            reprovados.append("Colunas")
    
    if filtros.get("repetidas", {}).get("ativo"):
        r = len(set(jogo) & set(analise["ultimo"]))
        if not (filtros["repetidas"]["min"] <= r <= filtros["repetidas"]["max"]):
            reprovados.append("Repetidas")
    
    if filtros.get("sequencia_max", {}).get("ativo"):
        jogo_sorted = sorted(jogo)
        seq_max = 1
        seq_atual = 1
        for i in range(1, len(jogo_sorted)):
            if jogo_sorted[i] == jogo_sorted[i-1] + 1:
                seq_atual += 1
                seq_max = max(seq_max, seq_atual)
            else:
                seq_atual = 1
        if seq_max > filtros["sequencia_max"]["valor"]:
            reprovados.append("Seq")
    
    return len(reprovados) == 0, reprovados

def gerar_jogo_ciclo(config, analise, modo="AVANCADO", ordenar_visual=False, filtros=None):
    if filtros is None:
        filtros = {"ativo": False}
    
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    
    for _ in range(200):
        jogo = []
        
        if modo == "ULTRA_FOCUS" and len(faltantes) >= total_jogo:
            jogo = random.sample(faltantes, total_jogo)
        else:
            qtd_f = min(int(total_jogo * (0.6 if modo=="SUPER_FOCUS" else 0.4)), len(faltantes))
            if qtd_f > 0: 
                jogo.extend(random.sample(faltantes, qtd_f))
            mem_disp = [m for m in memoria if m not in jogo]
            qtd_m = min(random.randint(m_min, m_max), len(mem_disp), max(0, total_jogo - len(jogo)))
            if qtd_m > 0: 
                jogo.extend(random.sample(mem_disp, qtd_m))

        quentes_disp = [q for q in analise["quentes"] if q not in jogo]
        while len(jogo) < total_jogo and len(quentes_disp) > 0:
            jogo.append(quentes_disp.pop(0))

        while len(jogo) < total_jogo:
            candidato = random.randint(1, config["total"])
            if candidato not in jogo:
                jogo.append(candidato)

        jogo = [int(x) for x in jogo[:total_jogo]]
        
        passou, _ = aplicar_filtros(jogo, filtros, analise)
        if passou or not filtros.get("ativo"):
            return sorted(jogo) if ordenar_visual else jogo
    
    return sorted(jogo) if ordenar_visual else jogo

def desdobramento_inteligente(config, analise, dezenas_base):
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    base_inteligente = list(dict.fromkeys(faltantes + memoria + analise["quentes"]))[:dezenas_base]
    
    jogos = []
    if dezenas_base == 18 and len(base_inteligente) >= 18:
        for comb in combinations(range(12, 18), 3):
            idx = list(range(12)) + list(comb)
            jogos.append(sorted([base_inteligente[i] for i in idx]))
    elif dezenas_base == 20 and len(base_inteligente) >= 20:
        fixas = base_inteligente[:11]
        rotativas = base_inteligente[11:20]
        for comb in combinations(rotativas, 4):
            jogos.append(sorted(fixas + list(comb)))
    elif dezenas_base == 16 and len(base_inteligente) >= 16:
        for comb in combinations(range(16), 15):
            jogos.append(sorted([base_inteligente[i] for i in comb]))
    else:
        for _ in range(10):
            jogos.append(sorted(random.sample(base_inteligente, config["sorteadas"])))
    
    return jogos[:30]

def gerar_pdf(jogos, config):
    if not PDF_AVAILABLE:
        return None
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, 280*mm, "LOTOELITE PRO v52.2 - {}".format(config["nome"]))
    c.setFont("Helvetica", 10)
    y = 260
    for i, jogo in enumerate(jogos, 1):
        txt = "Jogo {:02d}: {}".format(i, " - ".join("{:02d}".format(n) for n in jogo))
        c.drawString(20*mm, y*mm, txt)
        y -= 8
        if y < 20:
            c.showPage()
            y = 280
    c.save()
    buffer.seek(0)
    return buffer

analise = analisar_ciclo_completo(df, config)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Gerador", "Filtros", "Desdobramento", "Estatisticas", 
    "Backtesting", "Meu Perfil", "Bankroll", "Fechamentos IA"
])

with tab1:
    st.subheader("Gerador de Jogos")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase", analise["fase"], "{}º".format(analise['sorteios_ciclo']))
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memoria", len(analise["memoria"]))
    c4.metric("Fecha em", "{}".format(analise['previsao_fecha']))
    st.progress(analise["progresso"])

    col_a, col_b = st.columns(2)
    with col_a:
        modo_focus = st.select_slider("Modo", ["MODERADO", "AVANCADO", "SUPER_FOCUS", "ULTRA_FOCUS"], value="AVANCADO")
    with col_b:
        ordenar = st.checkbox("Ordenar", value=False)
    
    qtd = st.slider("Quantos jogos?", 5, 50, 15)
    usar_filtros = st.checkbox("Aplicar filtros", value=False)

    if st.button("GERAR JOGOS", type="primary"):
        filtros_ativos = st.session_state.get('filtros_config', {"ativo": False}) if usar_filtros else {"ativo": False}
        jogos_gerados = [gerar_jogo_ciclo(config, analise, modo_focus, ordenar, filtros_ativos) for _ in range(qtd)]
        
        for i, jogo in enumerate(jogos_gerados, 1):
            st.code("Jogo {:02d}: {}".format(i, jogo))
        
        if PDF_AVAILABLE:
            pdf = gerar_pdf(jogos_gerados, config)
            st.download_button("Baixar PDF", pdf, "jogos_{}.pdf".format(config['nome']), "application/pdf")

with tab2:
    st.subheader("Filtros Avancados v52")
    filtros_config = {"ativo": st.checkbox("Ativar sistema de filtros", value=True)}
    
    if filtros_config["ativo"]:
        col1, col2 = st.columns(2)
        with col1:
            filtros_config["soma"] = {"ativo": True, "min": st.number_input("Soma min", 150, 250, 199), "max": st.number_input("Soma max", 150, 250, 210), "fases": ["MEIO", "FIM"]}
            filtros_config["pares"] = {"ativo": True, "min": st.slider("Pares min", 5, 10, 7), "max": st.slider("Pares max", 5, 10, 8)}
            filtros_config["repetidas"] = {"ativo": True, "min": st.slider("Repetidas min", 0, 10, 5), "max": st.slider("Repetidas max", 0, 10, 9)}
        
        with col2:
            if config["nome"] == "Lotofacil":
                filtros_config["moldura"] = {"ativo": st.checkbox("Moldura 5x5", True), "min": st.slider("Moldura min", 6, 14, 8), "max": st.slider("Moldura max", 6, 14, 11)}
                filtros_config["colunas"] = {"ativo": st.checkbox("Colunas", True), "min": st.slider("Min colunas", 3, 5, 4)}
            filtros_config["sequencia_max"] = {"ativo": True, "valor": st.slider("Max consecutivos", 1, 5, 2)}
    
    st.session_state['filtros_config'] = filtros_config

with tab3:
    st.subheader("Desdobramento Inteligente")
    dezenas_base = st.slider("Base", 16, 20, 18)
    
    if st.button("GERAR DESDOBRAMENTO", type="primary"):
        jogos_desd = desdobramento_inteligente(config, analise, dezenas_base)
        st.success("{} jogos gerados".format(len(jogos_desd)))
        
        for i, jogo in enumerate(jogos_desd[:20], 1):
            mold = len([n for n in jogo if n in MOLDURA]) if config["nome"]=="Lotofacil" else 0
            rep = len(set(jogo) & set(analise["ultimo"]))
            st.code("J{:02d} (M{} R{}): {}".format(i, mold, rep, jogo))

with tab4:
    st.subheader("Estatisticas")
    st.metric("Progresso", "{:.0%}".format(analise['progresso']))
    st.progress(analise["progresso"])
    st.write("**Faltantes:**", analise["faltantes"])
    st.write("**Memoria:**", analise["memoria"])
    st.write("**Ultimo:**", analise["ultimo"])

with tab5:
    st.subheader("Backtesting")
    if st.button("RODAR"):
        res = []
        for i in range(25, len(df)):
            an = analisar_ciclo_completo(df.iloc[:i], config)
            jogo = gerar_jogo_ciclo(config, an, "SUPER_FOCUS")
            resultado = set([int(x) for x in df.iloc[i].values])
            acertos = len(set(jogo) & resultado)
            res.append(acertos)
        st.metric("Media acertos", "{:.1f}".format(np.mean(res)))

with tab6:
    st.subheader("Meu Perfil")
    acertos = st.number_input("Acertos", 0, config["sorteadas"], 0)
    modo = st.selectbox("Modo", ["MODERADO", "AVANCADO", "SUPER_FOCUS", "ULTRA_FOCUS"])
    if st.button("Salvar"):
        st.session_state.historico_perfil.append({"acertos": acertos, "modo": modo, "fase": analise["fase"]})
        st.success("Salvo")

with tab7:
    st.subheader("Bankroll")
    banca = st.number_input("Banca R$", value=100.0)
    if analise["fase"] == "FIM":
        st.error("Aposte R$ {:.2f}".format(banca*0.4))
    elif analise["fase"] == "MEIO":
        st.warning("Aposte R$ {:.2f}".format(banca*0.2))
    else:
        st.info("Aposte R$ {:.2f}".format(banca*0.1))

with tab8:
    st.subheader("Fechamentos IA")
    if st.button("Gerar 3"):
        j1 = gerar_jogo_ciclo(config, analise, "ULTRA_FOCUS", True)
        j2 = gerar_jogo_ciclo(config, analise, "SUPER_FOCUS", True)
        j3 = gerar_jogo_ciclo(config, analise, "AVANCADO", True)
        st.code("Fechar Ciclo: {}".format(j1))
        st.code("Memoria: {}".format(j2))
        st.code("Ataque: {}".format(j3))
