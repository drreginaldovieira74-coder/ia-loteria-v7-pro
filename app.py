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
st.title("LOTOELITE PRO v53")
st.markdown("**Quadrantes 4x | Fibonacci | Heatmap | CSV Export | IA Preditor**")

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
    st.stop()

df = pd.read_csv(arquivo, header=None)
df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)

def analisar_ciclo(df, config):
    total = config["total"]
    ciclos = []
    vistas = set()
    atual = []
    for idx, row in df.iterrows():
        nums = [int(x) for x in row.values if 1 <= int(x) <= total]
        atual.append(idx)
        vistas.update(nums)
        if len(vistas) >= total:
            ciclos.append({"dezenas": set(nums), "duracao": len(atual)})
            atual = []
            vistas = set()
    faltantes = sorted(set(range(1, total+1)) - vistas)
    sorteios = len(atual)
    lim1, lim2 = config["fase_limites"]
    fase = "ZERADO" if sorteios==0 else "INICIO" if sorteios<=lim1 else "MEIO" if sorteios<=lim2 else "FIM"
    memoria = list(ciclos[-1]["dezenas"] & vistas) if ciclos else []
    progresso = max(0.0, min(1.0, len(vistas)/total))
    freq = np.bincount(df.tail(30).values.flatten(), minlength=total+1)[1:]
    quentes = [int(x) for x in np.argsort(freq)[-25:][::-1] + 1 if 1 <= x <= total]
    ultimo = [int(x) for x in df.iloc[-1].values if 1 <= int(x) <= total]
    return {"fase": fase, "faltantes": faltantes, "memoria": memoria, "quentes": quentes, "ultimo": ultimo, "progresso": progresso, "sorteios": sorteios, "ciclos": ciclos}

analise = analisar_ciclo(df, config)

# Definicoes Lotofacil
MOLDURA = {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}
QUADRANTES = {
    "Q1": {1,2,3,4,5,6,7,8,9,10},  # topo
    "Q2": {11,12,13,14,15},         # meio-esq
    "Q3": {16,17,18,19,20},         # meio-dir
    "Q4": {21,22,23,24,25}          # baixo
}
FIBONACCI = {1,2,3,5,8,13,21}
COLUNAS = {1:[1,6,11,16,21], 2:[2,7,12,17,22], 3:[3,8,13,18,23], 4:[4,9,14,19,24], 5:[5,10,15,20,25]}

def contar_quadrantes(jogo):
    return {q: len([n for n in jogo if n in nums]) for q, nums in QUADRANTES.items()}

def aplicar_filtros_v53(jogo, filtros, analise):
    if not filtros.get("ativo"):
        return True
    fase = analise["fase"]
    
    if filtros.get("soma", {}).get("ativo") and fase in filtros["soma"]["fases"]:
        if not (filtros["soma"]["min"] <= sum(jogo) <= filtros["soma"]["max"]):
            return False
    
    if filtros.get("pares", {}).get("ativo"):
        p = len([x for x in jogo if x%2==0])
        if not (filtros["pares"]["min"] <= p <= filtros["pares"]["max"]):
            return False
    
    if filtros.get("moldura", {}).get("ativo"):
        m = len([n for n in jogo if n in MOLDURA])
        if not (filtros["moldura"]["min"] <= m <= filtros["moldura"]["max"]):
            return False
    
    if filtros.get("quadrantes", {}).get("ativo"):
        qc = contar_quadrantes(jogo)
        for q, lim in filtros["quadrantes"]["limites"].items():
            if not (lim[0] <= qc[q] <= lim[1]):
                return False
    
    if filtros.get("fibonacci", {}).get("ativo"):
        f = len([n for n in jogo if n in FIBONACCI])
        if not (filtros["fibonacci"]["min"] <= f <= filtros["fibonacci"]["max"]):
            return False
    
    if filtros.get("colunas", {}).get("ativo"):
        c = len([col for col, nums in COLUNAS.items() if any(n in jogo for n in nums)])
        if c < filtros["colunas"]["min"]:
            return False
    
    if filtros.get("repetidas", {}).get("ativo"):
        r = len(set(jogo) & set(analise["ultimo"]))
        if not (filtros["repetidas"]["min"] <= r <= filtros["repetidas"]["max"]):
            return False
    
    if filtros.get("seq", {}).get("ativo"):
        js = sorted(jogo)
        maxseq = 1
        seq = 1
        for i in range(1, len(js)):
            if js[i] == js[i-1]+1:
                seq += 1
                maxseq = max(maxseq, seq)
            else:
                seq = 1
        if maxseq > filtros["seq"]["max"]:
            return False
    
    return True

def gerar_jogo_v53(config, analise, modo, filtros):
    falt = analise["faltantes"]
    mem = analise["memoria"]
    quentes = analise["quentes"]
    total = config["sorteadas"]
    mmin, mmax = config["mantidas"]
    
    for _ in range(300):
        jogo = []
        if modo == "ULTRA_FOCUS" and len(falt) >= total:
            jogo = random.sample(falt, total)
        else:
            qf = min(int(total*(0.65 if modo=="SUPER_FOCUS" else 0.45)), len(falt))
            if qf>0: jogo.extend(random.sample(falt, qf))
            mem_disp = [m for m in mem if m not in jogo]
            qm = min(random.randint(mmin, mmax), len(mem_disp), total-len(jogo))
            if qm>0: jogo.extend(random.sample(mem_disp, qm))
        
        for q in quentes:
            if len(jogo) >= total: break
            if q not in jogo: jogo.append(q)
        
        while len(jogo) < total:
            n = random.randint(1, config["total"])
            if n not in jogo: jogo.append(n)
        
        jogo = jogo[:total]
        if aplicar_filtros_v53(jogo, filtros, analise):
            return sorted(jogo)
    
    return sorted(jogo)

def preditor_ia(analise, config):
    # IA simples: pontua por faltantes + quentes + baixa frequencia no ciclo
    scores = {}
    for n in range(1, config["total"]+1):
        score = 0
        if n in analise["faltantes"]: score += 50
        if n in analise["memoria"]: score += 30
        if n in analise["quentes"][:10]: score += 20
        if n in FIBONACCI: score += 5
        scores[n] = score
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:config["sorteadas"]+5]
    return [n for n,_ in top]

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Gerador v53", "Filtros PRO", "Quadrantes", "Desdobramento", "Heatmap", 
    "IA Preditor", "Estatisticas", "Perfil", "Export"
])

with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Fase", analise["fase"])
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memoria", len(analise["memoria"]))
    c4.metric("Progresso", "{:.0%}".format(analise["progresso"]))
    st.progress(analise["progresso"])
    
    modo = st.select_slider("Modo", ["MODERADO","AVANCADO","SUPER_FOCUS","ULTRA_FOCUS"], value="SUPER_FOCUS")
    qtd = st.slider("Jogos", 5, 50, 20)
    
    if st.button("GERAR v53", type="primary"):
        filtros = st.session_state.get("filtros_v53", {"ativo": False})
        jogos = [gerar_jogo_v53(config, analise, modo, filtros) for _ in range(qtd)]
        st.session_state["ultimos_jogos"] = jogos
        
        for i,j in enumerate(jogos,1):
            q = contar_quadrantes(j) if config["nome"]=="Lotofacil" else {}
            info = "Q1:{} Q2:{} Q3:{} Q4:{}".format(q.get("Q1",0), q.get("Q2",0), q.get("Q3",0), q.get("Q4",0)) if q else ""
            st.code("J{:02d} {} | {}".format(i, j, info))

with tab2:
    st.subheader("Filtros PRO v53")
    f = {"ativo": st.checkbox("Ativar", True)}
    col1, col2, col3 = st.columns(3)
    
    with col1:
        f["soma"] = {"ativo": True, "min": st.number_input("Soma min", 150, 250, 195), "max": st.number_input("Soma max", 150, 250, 215), "fases": ["MEIO","FIM"]}
        f["pares"] = {"ativo": True, "min": st.slider("Pares", 5, 10, 7), "max": st.slider("Pares max", 5, 10, 8)}
        f["repetidas"] = {"ativo": True, "min": st.slider("Rep min", 0, 10, 6), "max": st.slider("Rep max", 0, 10, 9)}
    
    with col2:
        if config["nome"] == "Lotofacil":
            f["moldura"] = {"ativo": True, "min": st.slider("Mold min", 6, 14, 8), "max": st.slider("Mold max", 6, 14, 11)}
            f["colunas"] = {"ativo": True, "min": st.slider("Colunas", 3, 5, 4)}
            f["fibonacci"] = {"ativo": st.checkbox("Fibonacci", True), "min": st.slider("Fib min", 2, 6, 3), "max": st.slider("Fib max", 2, 8, 5)}
    
    with col3:
        f["seq"] = {"ativo": True, "max": st.slider("Max seq", 2, 4, 2)}
        if config["nome"] == "Lotofacil":
            f["quadrantes"] = {"ativo": st.checkbox("Quadrantes 4x", True), "limites": {
                "Q1": (3,6), "Q2": (2,4), "Q3": (2,4), "Q4": (3,6)
            }}
    
    st.session_state["filtros_v53"] = f

with tab3:
    st.subheader("Analise Quadrantes")
    if config["nome"] == "Lotofacil":
        st.write("**Q1 (1-10):** topo | **Q2 (11-15):** meio-esq | **Q3 (16-20):** meio-dir | **Q4 (21-25):** baixo")
        st.info("Padrao vencedor: Q1=4-5, Q2=3, Q3=3, Q4=4-5 (evita desbalancear)")
        
        if "ultimos_jogos" in st.session_state:
            for j in st.session_state["ultimos_jogos"][:5]:
                q = contar_quadrantes(j)
                st.write("Jogo {} -> Q1:{} Q2:{} Q3:{} Q4:{}".format(j, q["Q1"], q["Q2"], q["Q3"], q["Q4"]))

with tab4:
    st.subheader("Desdobramento 16-20")
    base = st.slider("Base", 16, 20, 20)
    if st.button("Desdobrar"):
        base_nums = list(dict.fromkeys(analise["faltantes"] + analise["memoria"] + analise["quentes"]))[:base]
        jogos = []
        if base == 20:
            fixas = base_nums[:11]
            for comb in combinations(base_nums[11:20], 4):
                jogos.append(sorted(fixas + list(comb)))
        elif base == 18:
            for comb in combinations(range(12,18),3):
                idx = list(range(12)) + list(comb)
                jogos.append(sorted([base_nums[i] for i in idx]))
        else:
            for _ in range(20):
                jogos.append(sorted(random.sample(base_nums, config["sorteadas"])))
        
        st.session_state["ultimos_jogos"] = jogos[:25]
        for i,j in enumerate(jogos[:25],1):
            st.code("J{:02d}: {}".format(i, j))

with tab5:
    st.subheader("Heatmap Colunas e Quadrantes")
    if config["nome"] == "Lotofacil" and len(df) > 20:
        ultimos_20 = df.tail(20).values.flatten()
        col_counts = {i:0 for i in range(1,6)}
        quad_counts = {q:0 for q in QUADRANTES.keys()}
        
        for n in ultimos_20:
            n = int(n)
            for col, nums in COLUNAS.items():
                if n in nums: col_counts[col] += 1
            for q, nums in QUADRANTES.items():
                if n in nums: quad_counts[q] += 1
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Colunas ultimos 20 concursos**")
            st.bar_chart(pd.DataFrame(list(col_counts.items()), columns=["Coluna","Freq"]).set_index("Coluna"))
        with c2:
            st.write("**Quadrantes ultimos 20**")
            st.bar_chart(pd.DataFrame(list(quad_counts.items()), columns=["Quad","Freq"]).set_index("Quad"))

with tab6:
    st.subheader("IA Preditor - Top Dezenas")
    top_ia = preditor_ia(analise, config)
    st.success("Top {} dezenas IA: {}".format(len(top_ia), top_ia))
    st.write("Baseado em: 50% faltantes + 30% memoria + 20% quentes + Fibonacci")
    
    if st.button("Gerar 3 jogos IA"):
        jogos_ia = []
        for _ in range(3):
            base = top_ia[:config["sorteadas"]+3]
            jogo = sorted(random.sample(base, config["sorteadas"]))
            jogos_ia.append(jogo)
        for i,j in enumerate(jogos_ia,1):
            st.code("IA {:d}: {}".format(i, j))

with tab7:
    st.write("**Faltantes ({}):**".format(len(analise["faltantes"])), analise["faltantes"])
    st.write("**Memoria ({}):**".format(len(analise["memoria"])), analise["memoria"])
    st.write("**Quentes:**", analise["quentes"][:15])
    st.write("**Ultimo:**", analise["ultimo"])
    st.write("**Fibonacci:**", sorted(FIBONACCI))

with tab8:
    st.subheader("Perfil")
    if st.button("Salvar acerto"):
        st.session_state.historico_perfil.append({"data": str(datetime.now())[:10], "fase": analise["fase"]})
        st.success("Salvo")

with tab9:
    st.subheader("Exportar")
    if "ultimos_jogos" in st.session_state:
        jogos = st.session_state["ultimos_jogos"]
        df_exp = pd.DataFrame(jogos)
        csv = df_exp.to_csv(index=False, header=False).encode('utf-8')
        st.download_button("CSV Jogos", csv, "jogos_v53.csv", "text/csv")
        
        if PDF_AVAILABLE:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20*mm, 280*mm, "LOTOELITE v53 - {}".format(config["nome"]))
            y = 260
            for i,j in enumerate(jogos,1):
                c.drawString(20*mm, y*mm, "J{:02d}: {}".format(i, "-".join("{:02d}".format(n) for n in j)))
                y -= 7
                if y < 20: c.showPage(); y = 280
            c.save()
            buffer.seek(0)
            st.download_button("PDF Volante", buffer, "volante_v53.pdf", "application/pdf")
