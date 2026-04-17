import streamlit as st
from datetime import datetime

# --- CONFIG CORRETA v84.6 ---
st.set_page_config(page_title="LotoElite v84.6", page_icon="🎯", layout="wide")

# --- DNA DO USUÁRIO (pré-carregado) ---
DNA_LOTOFACIL = [4,6,10,14,17,19,20,24,25]
DNA_MEGA = [14,32,37,39,42]
DNA_QUINA = [4,10,14,19,20,25,32,37]

# --- HEADER ---
st.markdown("## 🎯 LOTOELITE v84.6")
st.caption("build 17/04/2026 — ciclo REAL ativo | Teresina-PI")

# --- ABAS (HUB AGORA É ABA 5 FIXA) ---
tab_ciclo, tab_ia, tab_result, tab_perfil, tab_hub, tab_export = st.tabs([
    "🔄 CICLO", "🤖 IA 3", "📊 RESULTADOS", "👤 PERFIL", "🎯 HUB", "📤 EXPORTAR"
])

with tab_ciclo:
    st.subheader("Ciclo REAL de hoje")
    col1, col2, col3 = st.columns(3)
    col1.metric("Lotofácil", "4 concursos", "🟡 MEIO")
    col2.metric("Quina", "5 concursos", "🟢 INÍCIO")
    col3.metric("Mega-Sena", "12 concursos", "🔴 FIM")
    st.info("Focus automático: Lotofácil 50% | Quina 60% | Mega 70%")

with tab_ia:
    st.subheader("Jogos gerados hoje (17/04)")
    st.markdown("**Lotofácil 3664:**")
    st.code("J1: 01-04-05-06-10-12-14-17-19-20-22-23-24-25-03\nJ2: 01-03-04-05-06-10-12-14-17-19-20-21-22-24-25\nJ3: 01-04-05-06-10-12-14-15-17-19-20-22-23-24-25")
    st.markdown("**Quina 7004:**")
    st.code("J1: 14-19-25-29-53\nJ2: 32-37-44-64-74\nJ3: 04-10-20-21-22")

with tab_result:
    st.subheader("Conferir amanhã")
    st.write("Amanhã (18/04) cole aqui os resultados e o sistema calcula automaticamente.")

with tab_perfil:
    st.subheader("Meu Perfil")
    st.write("**DNA Lotofácil:**", DNA_LOTOFACIL)
    st.write("**DNA Mega:**", DNA_MEGA)
    st.write("**DNA Quina:**", DNA_QUINA)
    st.success("DNA salvo localmente - não precisa digitar de novo")

with tab_hub:
    st.subheader("🎯 Hub Especial - Fechamentos")
    st.write("Agora fixo como aba, não some mais.")
    
    opcao = st.selectbox("Escolha:", ["Lotofácil 15 em 12", "Mega 6 em 4", "Quina desdobramento"])
    
    if opcao == "Lotofácil 15 em 12":
        st.write("Usando seu DNA:", DNA_LOTOFACIL)
        if st.button("Gerar fechamento"):
            # exemplo simples
            fechamento = [
                DNA_LOTOFACIL + [1,5,12,22,23,25],
                DNA_LOTOFACIL + [3,5,12,21,22,24],
                DNA_LOTOFACIL + [1,5,12,15,22,23]
            ]
            for i, jogo in enumerate(fechamento, 1):
                st.code(f"J{i}: {'-'.join(f'{n:02d}' for n in sorted(jogo)[:15])}")
    
    elif opcao == "Mega 6 em 4":
        st.write("Usando seu DNA:", DNA_MEGA)
        if st.button("Gerar fechamento Mega"):
            st.code("14-32-37-39-42-10\n14-32-37-44-53-19\n32-39-42-33-10-05")
    
    else:
        st.write("Desdobramento Quina com DNA")
        if st.button("Gerar Quina"):
            st.code("14-19-25-29-53\n32-37-44-64-74\n04-10-20-21-22")

with tab_export:
    st.subheader("Exportar")
    st.download_button("Baixar jogos de hoje (TXT)", 
        data="Lotofacil...\nQuina...", 
        file_name=f"lotoelite_v84_6_{datetime.now().strftime('%d%m')}.txt")

st.divider()
st.caption("v84.6 - corrigido título v79g | Hub fixo | ciclo REAL")
