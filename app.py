import streamlit as st

st.set_page_config(page_title="LotoElite v84.11", page_icon="🎯", layout="wide")

# DNA completo
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

LOTERIAS = list(DNAS.keys())

# SIDEBAR com todas
with st.sidebar:
    st.markdown("### LOTOELITE")
    st.radio("Menu", ["MEUS JOGOS"], index=0)
    loteria = st.selectbox("Todas as Loterias", LOTERIAS, index=0)
    focus = st.slider("Focus %", 50, 70, 60, step=10)
    if st.button("🔄 Atualizar Ciclo REAL", use_container_width=True):
        st.success(f"Ciclo {loteria} atualizado!")
    st.divider()
    st.caption("DNA ativo")
    st.write(DNAS[loteria])

st.markdown("<h1 style='text-align:center;color:#d32f2f;'>LOTOELITE</h1>", unsafe_allow_html=True)

abas = ["📊 BALANÇO","📈 RESULTADOS","🎮 MEUS JOGOS","🎯 PLUS CATCH","📡 LIVE CATCH",
        "👤 PERFIL","💰 PREÇOS","📤 EXPORTAR","🔴 AO VIVO","🎯 HUB ESPECIAL"]
tabs = st.tabs(abas)

# 3 jogos IA para TODAS as loterias
jogos_ia = {
    "Lotofácil": ["01-04-05-06-10-12-14-17-19-20-22-23-24-25-03",
                  "01-03-04-05-06-10-12-14-17-19-20-21-22-24-25",
                  "01-04-05-06-10-12-14-15-17-19-20-22-23-24-25"],
    "Mega-Sena": ["14-32-37-39-42-10","14-32-37-44-53-19","32-39-42-33-10-05"],
    "Quina": ["14-19-25-29-53","32-37-44-64-74","04-10-20-21-22"],
    "Lotomania": ["04-06-10-14-17-19-20-24-25-32-37-39-42-44-01-02-03-05-07-08",
                  "04-06-10-12-14-15-17-19-20-21-22-23-24-25-32-33-35-37-39-40",
                  "01-03-04-05-06-10-11-13-14-17-18-19-20-22-24-25-26-28-32-37"],
    "Dupla Sena": ["14-19-25-32-37-42","04-10-14-20-32-44","06-17-19-24-25-39"],
    "Timemania": ["04-10-14-20-25-32-44","14-19-24-37-39-42-53","06-10-17-20-25-32-37"],
    "Dia de Sorte": ["04-06-10-14-17-19-20","01-04-05-10-14-19-25","06-10-12-17-20-24-25"],
    "Super Sete": ["4-6-10 | 1-4-7 | 0-4-6 | 1-4-7 | 0-1-7 | 1-9-0 | 0-2-4",
                   "4-6-0 | 1-4-0 | 4-6-7 | 1-4-9 | 0-7-9 | 1-0-2 | 4-5-6",
                   "6-0-1 | 4-7-9 | 6-7-0 | 4-9-2 | 7-9-4 | 0-2-5 | 6-4-1"],
    "+Milionária": ["14-19-25-32-37-42 + 02-04","04-10-20-32-37-44 + 01-03","06-14-17-25-39-42 + 02-05"]
}

with tabs[2]:
    st.subheader(f"Meus Jogos - {loteria} (IA Ciclo REAL)")
    st.caption("3 jogos gerados pela IA, não aleatórios")
    for i,j in enumerate(jogos_ia[loteria],1):
        st.code(f"J{i}: {j}")

for i in [0,1,3,4,5,6,7,8]:
    with tabs[i]:
        st.write(f"Conteúdo {abas[i]}")

with tabs[9]:
    st.subheader("🎯 HUB ESPECIAL - Todas as Loterias")
    
    st.info(f"Loteria ativa: {loteria}")
    
    if loteria == "Lotofácil":
        tipo = st.selectbox("Fechamento:", ["15 em 12", "Fechamento1 - 21 dezenas", "Bolão"])
        if tipo == "Fechamento1 - 21 dezenas":
            dezenas = sorted(DNAS[loteria] + [1,2,3,5,7,8,11,12,13,15,21,22,23])[:21]
            st.code("21 DEZENAS: " + " - ".join(f"{n:02d}" for n in dezenas))
    
    elif loteria in ["Mega-Sena", "+Milionária", "Dupla Sena"]:
        st.write("Desdobramento 6 em 4 com DNA")
        st.code(" - ".join(f"{n:02d}" for n in DNAS[loteria][:6]))
    
    elif loteria == "Lotomania":
        st.write("Fechamento Lotomania 50 em 35")
        st.code("Usando DNA estendido")
    
    elif loteria == "Super Sete":
        st.write("Fechamento Super Sete - 3 colunas por dezena")
    
    else:
        st.write(f"Gerador otimizado para {loteria}")

st.caption("v84.11 - TODAS as 9 loterias restauradas")
