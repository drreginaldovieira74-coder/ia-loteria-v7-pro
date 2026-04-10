with tab5:
    st.subheader("👤 Meu Perfil - Aprendizado do Ciclo")
    st.info("IA aprende seu padrão de ciclo e salva seu desempenho")
    
    # Inicializa histórico no session_state se não existir
    if 'historico_perfil' not in st.session_state:
        st.session_state.historico_perfil = []
    
    if analise["ciclos_hist"]:
        dur_media = np.mean([c["duracao"] for c in analise["ciclos_hist"]])
        st.write(f"Seu ciclo fecha em média a cada **{dur_media:.1f} sorteios**")
        if analise["sorteios_ciclo"] > dur_media + 1:
            st.warning(f"⚠️ Ciclo atual já passou da média. Está no {analise['sorteios_ciclo']}º sorteio, média é {dur_media:.1f}")
        else:
            st.success("✅ Ciclo dentro do esperado")
    
    st.write(f"**Memória detectada:** você mantém {len(analise['memoria'])} dezenas entre ciclos")
    
    st.divider()
    st.subheader("💾 Salvar Desempenho")
    
    col1, col2 = st.columns(2)
    with col1:
        acertos_manual = st.number_input("Quantos acertos você fez no último concurso?", min_value=0, max_value=config["sorteadas"], value=0)
    with col2:
        modo_usado = st.selectbox("Modo que você usou", ["MODERADO", "AVANÇADO", "SUPER_FOCUS", "ULTRA_FOCUS"])
    
    if st.button("💾 Salvar Meu Resultado", type="primary"):
        registro = {
            "data": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "loteria": config["nome"],
            "fase_ciclo": analise["fase"],
            "sorteio_ciclo": analise["sorteios_ciclo"],
            "modo_usado": modo_usado,
            "acertos": int(acertos_manual),
            "qtd_faltantes": len(analise["faltantes"]),
            "qtd_memoria": len(analise["memoria"]),
            "duracao_media_ciclos": round(np.mean([c["duracao"] for c in analise["ciclos_hist"]]), 2) if analise["ciclos_hist"] else 0
        }
        st.session_state.historico_perfil.append(registro)
        st.success(f"✅ Resultado salvo! Total: {len(st.session_state.historico_perfil)} registros")
    
    if st.session_state.historico_perfil:
        st.divider()
        st.subheader("📊 Seu Histórico")
        df_historico = pd.DataFrame(st.session_state.historico_perfil)
        st.dataframe(df_historico, use_container_width=True)
        
        # Métricas do seu desempenho
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", len(df_historico))
        c2.metric("Média de Acertos", f"{df_historico['acertos'].mean():.1f}")
        c3.metric("Melhor Resultado", int(df_historico['acertos'].max()))
        
        # Melhor modo pra você
        melhor_modo = df_historico.groupby('modo_usado')['acertos'].mean().idxmax()
        st.info(f"🎯 **Seu melhor modo:** {melhor_modo} com média de {df_historico[df_historico['modo_usado']==melhor_modo]['acertos'].mean():.1f} acertos")
        
        # Botão de download
