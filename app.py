def gerar_jogo_ciclo(config, analise, modo="AVANCADO"):
    faltantes, memoria = analise["faltantes"], analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    jogo = []
    ordenar_final = True

    if modo == "ULTRA_FOCUS":
        # Se tem exatamente o número de faltantes do jogo, não ordena pra variar
        if len(faltantes) >= total_jogo:
            faltantes_shuffled = random.sample(faltantes, total_jogo)
            jogo = faltantes_shuffled
            ordenar_final = False # Não ordena no ULTRA_FOCUS
        else:
            faltantes_shuffled = random.sample(faltantes, len(faltantes))
            jogo = faltantes_shuffled
            mem_shuffled = random.sample(memoria, len(memoria))
            jogo.extend([m for m in mem_shuffled if m not in jogo][:total_jogo - len(jogo)])
    
    elif modo == "SUPER_FOCUS":
        qtd_f = min(int(total_jogo * 0.6), len(faltantes))
        qtd_m = min(random.randint(m_min, m_max), len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))
    
    elif modo == "AVANCADO":
        qtd_f = min(int(total_jogo * 0.4), len(faltantes))
        qtd_m = min(m_min, len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))
    
    else: # MODERADO
        qtd_f = min(int(total_jogo * 0.3), len(faltantes))
        qtd_m = min(m_min - 1, len(memoria), total_jogo - qtd_f)
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        if qtd_m > 0 and len(mem_disp) > 0: 
            jogo.extend(random.sample(mem_disp, min(qtd_m, len(mem_disp))))

    quentes_disp = [q for q in analise["quentes"] if q not in jogo]
    while len(jogo) < total_jogo and len(quentes_disp) > 0:
        jogo.append(quentes_disp.pop(0))

    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo: 
            jogo.append(candidato)

    jogo = [int(x) for x in jogo[:total_jogo]]
    
    # Só ordena se não for ULTRA_FOCUS com faltantes suficientes
    if ordenar_final:
        jogo = sorted(jogo)
    
    return jogo
