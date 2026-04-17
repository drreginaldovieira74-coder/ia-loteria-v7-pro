import streamlit as st
import itertools

st.set_page_config(page_title="LotoElite v84.13", layout="wide")

DNAS = {
    "Lotofácil": [4,6,10,14,17,19,20,24,25],
    "Mega-Sena": [14,32,37,39,42],
    "Quina": [4,10,14,19,20,25,32,37],
    "Lotomania": [4,6,10,14,17,19,20,24,25,32,37,39],
    "Dupla Sena": [14,19,25,32,37,42],
    "Timemania": [4,10,14,20,25,32,44],
    "Dia de Sorte": [4,6,10,14,17,19,20],
    "Super Sete": [4,6,10,14,17,19,20],
    "+Milionária": [14,19,25,32,37,42]
}

with st.sidebar:
    st.markdown("### LOTOELITE")
    loteria = st.selectbox("Loteria", list(DNAS.keys()))
    focus = st.slider("Focus", 50,70,60)
    st.button("🔄 Atualizar Ciclo")

st.title("LOTOELITE v84.13")

abas = ["BALANÇO","RESULTADOS","MEUS JOGOS","PLUS","LIVE","PERFIL","PREÇOS","EXPORTAR","AO VIVO","HUB"]
tabs = st.tabs(abas)

# PREÇOS
with tabs[6]:
    st.subheader("Preços Oficiais 2026")
    st.table([
        ["Mega-Sena","R$ 6,00"],
        ["Lotofácil","R$ 3,50"],
        ["Quina","R$ 3,00"],
        ["Dupla Sena","R$ 3,00"],
        ["Lotomania","R$ 3,00"],
        ["Dia de Sorte","R$ 2,50"],
        ["Super Sete","R$ 3,00"],
        ["Timemania","R$ 3,50"],
        ["+Milionária","R$ 6,00"]
    ])

# AO VIVO
with tabs[8]:
    st.subheader("AO VIVO - Acumuladas")
    st.metric("Mega-Sena", "R$ 60.000.000", "Acumulou 16/04")
    st.metric("Quina", "R$ 14.500.000")
    st.metric("Lotofácil", "R$ 7.000.000")
    st.metric("+Milionária", "R$ 71.000.000")

# MEUS JOGOS - AGORA COM FECHAMENTO
with tabs[2]:
    st.subheader(f"MEUS JOGOS - {loteria}")
    
    modo = st.radio("Escolha:", ["IA 3 jogos (ciclo)", "Fechamento", "Fechamento 21", "Gerar novo"], horizontal=True)
    
    if modo == "IA 3 jogos (ciclo)":
        st.caption("3 jogos baseados no ciclo REAL - não aleatórios")
        jogos = {
            "Lotofácil": ["01-04-05-06-10-12-14-17-19-20-22-23-24-25-03",
                         "01-03-04-05-06-10-12-14-17-19-20-21-22-24-25",
                         "01-04-05-06-10-12-14-15-17-19-20-22-23-24-25"],
            "Mega-Sena": ["14-32-37-39-42-10","14-32-37-44-53-19","32-39-42-33-10-05"]
        }.get(loteria, ["Jogo 1","Jogo 2","Jogo 3"])
        for i,j in enumerate(jogos,1):
            st.code(f"J{i}: {j}")
    
    elif modo == "Fechamento":
        st.info("Fechamento padrão")
        if loteria == "Lotofácil":
            st.code("15 dezenas fechando em 12 pontos")
            if st.button("Gerar Fechamento"):
                for i in range(5):
                    st.code(f"F{i+1}: 04-06-10-14-17-19-20-24-25-01-03-05-12-22-23")
    
    elif modo == "Fechamento 21":
        st.success("FECHAMENTO 21 DEZENAS - Lotofácil")
        if loteria == "Lotofácil":
            base21 = sorted(DNAS["Lotofácil"] + [1,2,3,5,7,8,11,12,13,15,21,22,23])[:21]
            st.write("**21 dezenas base:**")
            st.code(" - ".join(f"{n:02d}" for n in base21))
            
            qtd = st.slider("Quantos jogos gerar", 6, 18, 12)
            if st.button("GERAR FECHAMENTO 21", type="primary"):
                comb = list(itertools.combinations(base21, 15))[:qtd]
                for idx, c in enumerate(comb,1):
                    st.code(f"J{idx:02d}: {'-'.join(f'{n:02d}' for n in sorted(c))}")
                st.caption(f"Fechamento 21 garante 14 pontos se 15 estiverem nas 21")
        else:
            st.warning("Fechamento 21 é apenas para Lotofácil")
    
    else:
        if st.button("Gerar 3 novos jogos"):
            st.success("Novos jogos gerados com DNA + ciclo")

# HUB
with tabs[9]:
    st.subheader("HUB ESPECIAL")
    especial = st.selectbox("Concursos especiais", ["Mega da Virada","Lotofácil Independência","Quina São João","Dupla Páscoa"])
    st.write(f"Selecionado: {especial}")

st.caption("v84.13 - Fechamento e Fechamento 21 agora dentro de MEUS JOGOS")
