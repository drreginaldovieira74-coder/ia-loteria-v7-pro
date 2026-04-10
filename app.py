def gerar_jogo_ciclo(config, analise, modo="AVANCADO", ordenar_visual=False):
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    jogo = []

    if modo == "ULTRA_FOCUS":
        if len(faltantes) >= total_jogo:
            jogo = random.sample(faltantes, total_jogo)
        else:
            # Pega todas as faltantes que tem + completa com memoria
            jogo = faltantes.copy() if len(faltantes) > 0 else []
            mem_shuffled = random.sample(memoria, min(len(memoria), total_jogo - len(jogo)))
            jogo.extend([m for m in mem_shuffled if m not in jogo])
    
    elif modo == "SUPER_FOCUS":
        qtd_f = min(int(total_jogo * 0.6), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        qtd_m = min(random.randint(m_min, m_max), len(mem_disp), max(0, total_jogo - len(jogo)))
        if qtd_m > 0: 
            jogo.extend(random.sample(mem_disp, qtd_m))
    
    elif modo == "AVANCADO":
        qtd_f = min(int(total_jogo * 0.4), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        qtd_m = min(m_min, len(mem_disp), max(0, total_jogo - len(jogo)))
        if qtd_m > 0: 
            jogo.extend(random.sample(mem_disp, qtd_m))
    
    else:
        qtd_f = min(int(total_jogo * 0.3), len(faltantes))
        if qtd_f > 0: 
            jogo.extend(random.sample(faltantes, qtd_f))
        mem_disp = [m for m in memoria if m not in jogo]
        qtd_m = min(m_min - 1, len(mem_disp), max(0, total_jogo - len(jogo)))
        if qtd_m > 0: 
            jogo.extend(random.sample(mem_disp, qtd_m))

    quentes_disp = [q for q in analise["quentes"] if q not in jogo]
    while len(jogo) < total_jogo and len(quentes_disp) > 0:
        jogo.append(quentes_disp.pop(0))

    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo: 
            jogo.append(candidato)

    jogo = [int(x) for x in jogo[:total_jogo]]
    
    if ordenar_visual:
        jogo = sorted(jogo)
    
    return jogo

def fechamento_inteligente_3jogos(config, analise, ordenar_visual=False):
    faltantes, memoria, quentes = analise["faltantes"], analise["memoria"], analise["quentes"]
    total_jogo = config["sorteadas"]
    jogos = []

    j1 = gerar_jogo_ciclo(config, analise, "ULTRA_FOCUS", ordenar_visual)
    jogos.append({"nome": "Fechar Ciclo", "jogo": j1, "estrategia": "100% faltantes + memoria"})

    base = memoria[:config["mantidas"][1]] if len(memoria) >= config["mantidas"][0] else memoria
    resto = [q for q in quentes if q not in base]
    precisa = max(0, total_jogo - len(base))
    j2 = base + random.sample(resto, min(len(resto), precisa))
    if ordenar_visual:
        j2 = sorted(j2)
    jogos.append({"nome": "Memoria Pura", "jogo": j2, "estrategia": "{} mantidas + quentes".format(len(base))})

    if len(faltantes) >= total_jogo:
        j3 = random.sample(faltantes, total_jogo)
    else:
        j3 = faltantes.copy()
        resto_quentes = [q for q in quentes if q not in j3]
        precisa = total_jogo - len(j3)
        j3.extend(random.sample(resto_quentes, min(len(resto_quentes), precisa)))
    if ordenar_visual:
        j3 = sorted(j3)
    jogos.append({"nome": "Ataque Faltantes", "jogo": j3, "estrategia": "Maximo de faltantes"})

    return jogos
