import streamlit as st
st.title("🚨 TESTE - SE VOCE VE ISSO, GITHUB ATUALIZOU")
st.error("Versao de teste 14/04/2026 - 11h30")
st.write("Se ainda aparece v67.4, o Streamlit NAO esta lendo este repositorio")
focus = st.sidebar.select_slider("FOCUS TESTE", ["A","B","C"])
st.sidebar.success(f"Focus teste: {focus}")
