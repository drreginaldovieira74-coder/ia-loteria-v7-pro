if arquivo is not None:

    df = pd.read_csv(arquivo)

    concursos, fase, faltantes = analisar_ciclo(df)
    base = frequencia(df)

    st.subheader("📊 Ciclo")
    st.write(f"Concursos: {concursos}")
    st.write(f"Fase: {fase}")
    st.write(f"Faltantes: {faltantes}")

    st.subheader("🔥 Frequentes")
    st.write(base[:15])

    st.subheader("⚙️ Configuração")

    qtd_jogos = st.slider("Quantidade de jogos", 1, 20, 5)

    modo = st.selectbox(
        "Modo",
        ["Conservador", "Agressivo", "Ciclo Puro"]
    )

    if st.button("🔥 Melhor jogo"):
        jogo = melhor_jogo(base, faltantes, fase, modo)
        st.write(jogo)

    if st.button("🚀 Simular"):
        jogos = simular(base, faltantes, fase, modo)

        for j in jogos[:qtd_jogos]:
            st.write(j)

else:
    st.warning("📂 Envie um arquivo CSV da Lotofácil para iniciar.")
