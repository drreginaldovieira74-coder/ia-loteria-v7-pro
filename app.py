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
st.title("LOTOELITE PRO v52")
st.markdown("**Moldura 5x5 | Colunas | Repetidas | PDF Volante | Desdobramento 20**")

loteria_options = {
    "Lotofacil": {"nome": "Lotofacil", "total": 25, "sorteadas": 15, "mantidas": [9, 11], "ciclo_esperado": [4, 6], "fase_limites": [2, 4]},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "mantidas": [35, 40], "ciclo_esperado": [8, 12], "fase_limites": [4, 8]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3], "ciclo_esperado": [35, 50], "fase_limites": [15, 35]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4], "ciclo_esperado": [22, 30], "fase_limites": [10, 22]}
}

if 'historico_perfil' not in st.session_state:
    st.session_state.historico_perfil = []

loteria = st.selectbox("Loteria", list(loteria_options.keys()))
config = loteria_options[loteria]

arquivo = st.file_uploader("CSV {}".format(config['nome']), type=["csv"])
if arquivo is None:
    st.warning("Envie CSV")
    st.stop()

df = pd.read_csv(arquivo, header=None)
df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)

def analisar_ciclo(df, config):
    total = config["total"]
    ciclos = []
    vistas = set()
    atual = []
    for idx, row in df.iterrows():
        atual.append(idx)
        vistas.update([int(x) for x in row.values])
        if len(vistas) == total:
            ciclos.append({"fim": atual[-1], "duracao": len(atual), "dezenas": set([int(x) for x in df.iloc[atual[-1]].values])})
            atual = []
            vistas = set()
    faltantes = sorted(set(range(1, total+1)) - vistas)
    sorteios = len(atual)
    lim1, lim2 = config["fase_limites"]
    if sorteios == 0:
        fase = "ZERADO"
    elif sorteios <= lim1:
        fase = "INICIO"
    elif sorteios <= lim2:
        fase = "MEIO"
    else:
        fase = "FIM"
    memoria = []
    if ciclos:
        memoria = list(ciclos[-1]["dezenas"] & vistas)
    freq = np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:]
    quentes = [int(x) for x in np.argsort(freq)[-20:][::-1] + 1]
    ultimo = [int(x) for x in df.iloc[-1].values]
    return {"fase": fase, "faltantes": faltantes, "memoria": memoria, "quentes": quentes, "ultimo": ultimo, "progresso": len(vistas)/total, "sorteios": sorteios, "ciclos": ciclos}

analise = analisar_ciclo(df, config)

MOLDURA = {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}
COLUNAS = {1:[1,6,11,16,21], 2:[2,7,12,17,22], 3:[3,8,13,18,23], 4:[4,9,14,19,24], 5:[5,10,15,20,25]}

def contar_moldura(jogo):
    return len([n for n in jogo if n in MOLDURA])

def contar_colunas(jogo):
    return len([c for c, nums in COLUNAS.items() if any(n in jogo for n in nums)])

def contar_repetidas(jogo, ultimo):
    return len(set(jogo) & set(ultimo))

def aplicar_filtros_v52(jogo, filtros, analise):
    if not filtros.get("ativo"):
        return True
    fase = analise["fase"]
    if filtros.get("soma", {}).get("ativo") and fase in filtros["soma"]["fases"]:
        s = sum(jogo)
        if not (filtros["soma"]["min"] <= s <= filtros["soma"]["max"]):
            return False
    if filtros.get("pares", {}).get("ativo"):
        p = len([x for x in jogo if x%2==0])
        if not (filtros["pares"]["min"] <= p <= filtros["pares"]["max"]):
            return False
    if filtros.get("moldura", {}).get("ativo") and config["nome"] == "Lotofacil":
        m = contar_moldura(jogo)
        if not (filtros["moldura"]["min"] <= m <= filtros["moldura"]["max"]):
            return False
    if filtros.get("colunas", {}).get("ativo") and config["nome"] == "Lotofacil":
        c = contar_colunas(jogo)
        if c < filtros["colunas"]["min"]:
            return False
    if filtros.get("repetidas", {}).get("ativo"):
        r = contar_repetidas(jogo, analise["ultimo"])
        if not (filtros["repetidas"]["min"] <= r <= filtros["repetidas"]["max"]):
            return False
    if filtros.get("seq", {}).get("ativo"):
        js = sorted(jogo)
        seq = 1
        maxseq = 1
        for i in range(1, len(js)):
            if js[i] == js[i-1]+1:
                seq += 1
                maxseq = max(maxseq, seq)
            else:
                seq = 1
        if maxseq > filtros["seq"]["max"]:
            return False
    return True

def gerar_jogo(config, analise, modo, filtros):
    falt = analise["faltantes"]
    mem = analise["memoria"]
    quentes = analise["quentes"]
    total = config["sorteadas"]
    mmin, mmax = config["mantidas"]
    for _ in range(200):
        jogo = []
        if modo == "ULTRA_FOCUS":
            qf = min(len(falt), total)
            if qf >= total:
                jogo = random.sample(falt, total)
            else:
                jogo = falt.copy()
        elif modo == "SUPER_FOCUS":
            qf = min(int(total*0.6), len(falt))
            jogo.extend(random.sample(falt, qf) if qf>0 else [])
        else:
            qf = min(int(total*0.4), len(falt))
            jogo.extend(random.sample(falt, qf) if qf>0 else [])
        mem_disp = [m for m in mem if m not in jogo]
        qm = min(random.randint(mmin, mmax), len(mem_disp), total-len(jogo))
        if qm>0:
            jogo.extend(random.sample(mem_disp, qm))
        for q in quentes:
            if len(jogo) >= total:
                break
            if q not in jogo:
                jogo.append(q)
        while len(jogo) < total:
            n = random.randint(1, config["total"])
            if n not in jogo:
                jogo.append(n)
        jogo = jogo[:total]
        if aplicar_filtros_v52(jogo, filtros, analise):
            return sorted(jogo)
    return sorted(jogo)

def desdobrar_20(config, analise, base_n):
    base = list(dict.fromkeys(analise["faltantes"] + analise["memoria"] + analise["quentes"]))[:base_n]
    jogos = []
    if base_n == 18:
        for comb in combinations(range(12,18),3):
            idx = list(range(12)) + list(comb)
            jogos.append(sorted([base[i] for i in idx]))
    elif base_n == 20:
        fixas = base[:11]
        rot = base[11:20]
        for comb in combinations(rot,4):
            jogos.append(sorted(fixas + list(comb)))
    else:
        for _ in range(15):
            jogos.append(sorted(random.sample(base, config["sorteadas"])))
    return jogos[:30]

def gerar_pdf(jogos, config):
    if not PDF_AVAILABLE:
        return None
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, 280*mm, "LOTOELITE PRO v52 - {}".format(config["nome"]))
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

tab1, tab2, tab3, tab4 = st.tabs(["Gerador v52", "Filtros Avancados", "Desdobramento 20", "Estatisticas"])

with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Fase", analise["fase"])
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memoria", len(analise["memoria"]))
    c4.metric("Progresso", "{:.0%}".format(analise["progresso"]))
    st.progress(analise["progresso"])
    modo = st.select_slider("Modo", ["MODERADO","AVANCADO","SUPER_FOCUS","ULTRA_FOCUS"], value="SUPER_FOCUS")
    qtd = st.slider("Jogos", 5, 30, 15)
    if st.button("GERAR v52", type="primary"):
        filtros = st.session_state.get("filtros_v52", {"ativo": False})
        jogos = [gerar_jogo(config, analise, modo, filtros) for _ in range(qtd)]
        for i,j in enumerate(jogos,1):
            st.code("Jogo {:02d}: {}".format(i, j))
        if PDF_AVAILABLE:
            pdf = gerar_pdf(jogos, config)
            st.download_button("Baixar PDF Volante", pdf, "volante_{}.pdf".format(config["nome"]), "application/pdf")

with tab2:
    st.subheader("Filtros que Mr Loto nao tem")
    f = {"ativo": st.checkbox("Ativar Filtros v52", True)}
    col1, col2 = st.columns(2)
    with col1:
        f["soma"] = {"ativo": True, "min": st.number_input("Soma min", 180, 250, 199), "max": st.number_input("Soma max", 180, 250, 210), "fases": ["MEIO","FIM"]}
        f["pares"] = {"ativo": True, "min": st.slider("Pares min", 5, 10, 7), "max": st.slider("Pares max", 5, 10, 8)}
        f["repetidas"] = {"ativo": True, "min": st.slider("Repetidas min", 0, 5, 5), "max": st.slider("Repetidas max", 0, 10, 9)}
    with col2:
        if config["nome"] == "Lotofacil":
            f["moldura"] = {"ativo": st.checkbox("Filtrar Moldura", True), "min": st.slider("Moldura min", 6, 12, 8), "max": st.slider("Moldura max", 6, 14, 11)}
            f["colunas"] = {"ativo": st.checkbox("Filtrar Colunas", True), "min": st.slider("Min colunas preenchidas", 3, 5, 4)}
        f["seq"] = {"ativo": True, "max": st.slider("Max consecutivos", 2, 4, 2)}
    st.session_state["filtros_v52"] = f
    st.success("Filtros salvos. Fase atual: {}".format(analise["fase"]))

with tab3:
    st.subheader("Desdobramento Inteligente 18-20 dezenas")
    base = st.slider("Base", 16, 20, 20)
    if st.button("Desdobrar 20"):
        jogos = desdobrar_20(config, analise, base)
        st.info("{} jogos gerados. Base = faltantes + memoria".format(len(jogos)))
        for i,j in enumerate(jogos[:20],1):
            mold = contar_moldura(j) if config["nome"]=="Lotofacil" else 0
            rep = contar_repetidas(j, analise["ultimo"])
            st.code("J{:02d} (Mold:{} Rep:{}): {}".format(i, mold, rep, j))
        if PDF_AVAILABLE:
            pdf = gerar_pdf(jogos, config)
            st.download_button("PDF Desdobramento", pdf, "desdobramento.pdf", "application/pdf")

with tab4:
    st.write("**Faltantes:**", analise["faltantes"])
    st.write("**Memoria:**", analise["memoria"])
    st.write("**Ultimo concurso:**", analise["ultimo"])
    if config["nome"] == "Lotofacil":
        st.write("**Moldura (16 nums):**", sorted(MOLDURA))
