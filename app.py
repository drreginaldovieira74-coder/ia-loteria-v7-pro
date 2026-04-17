import streamlit as st
from datetime import datetime
import itertools

st.set_page_config(page_title="LotoElite v84.17", layout="wide")
st.title("LOTOELITE v84.17 - VALORES ATUALIZADOS 17/04/2026")

DNAS = {
    "Lotofácil": [4,6,10,14,17,19,20,24,25],
    "Mega-Sena": [14,32,37,39,42],
    "Quina": [4,10,14,19,20,25,32,37],
}

with st.sidebar:
    st.selectbox("Loteria", list(DNAS.keys()))
    if st.button("🔄 Atualizar Ciclo"):
        st.session_state['upd'] = datetime.now().strftime("%H:%M:%S")
    if 'upd' in st.session_state:
        st.success(f"Atualizado {st.session_state['upd']}")

tabs = st.tabs(["BALANÇO","RESULTADOS","MEUS JOGOS","AO VIVO","PREÇOS"])

with tabs[0]:
    st.header("BALANÇO")
    st.write("Lotofácil: MEIO | Mega: FIM | Quina: INÍCIO")

with tabs[1]:
    st.header("RESULTADOS")
    st.write("Mega 2997 (16/04): ACUMULOU R$51.745.849,62")
    st.write("Mega 2996: 07-09-27-38-49-52")
    st.write("Quina 7003 (16/04): 04-14-18-54-75 - ACUMULOU")

with tabs[2]:
    st.header("MEUS JOGOS")
    st.code("J1: 01-04-05-06-10-12-14-17-19-20-22-23-24-25-03")

with tabs[3]:
    st.header("AO VIVO - 17/04/2026")
    st.write("1. Mega-Sena: R$ 60.000.000")
    st.write("2. Quina: R$ 20.000.000")
    st.write("3. Lotofácil: R$ 2.000.000")
    st.write("4. +Milionária: R$ 35.000.000")
    st.write("5. Timemania: R$ 18.700.000")
    st.write("6. Dupla Sena: R$ 1.000.000")
    st.write("7. Lotomania: R$ 500.000")
    st.write("8. Dia de Sorte: R$ 300.000")
    st.write("9. Super Sete: R$ 450.000")

with tabs[4]:
    st.header("PREÇOS 2026")
    st.write("Mega R$6,00 | Lotofácil R$3,50 | Quina R$3,00 | Dupla R$3,00")
