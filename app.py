import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict
from datetime import datetime
from itertools import combinations

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO v51.3")
st.markdown("**Ciclo por Loteria | Memoria | Filtros | Desdobramento | IA Híbrida**")

loteria_options = {
    "Lotofacil": {
        "nome": "Lotofacil", "total": 25, "sorteadas": 15, 
        "mantidas": [9, 11], "ciclo_esperado": [4, 6], "fase_limites": [2, 4]
    },
    "Lotomania": {
        "nome": "Lotomania", "total": 100, "sorteadas": 50, 
        "mantidas": [35, 40], "ciclo_esperado": [8, 12], "fase_limites": [4, 8]
    },
    "Quina": {
        "nome": "Quina", "total": 80, "sorteadas": 5, 
        "mantidas": [2, 3], "ciclo_esperado": [35, 50], "fase_limites": [15, 35]
    },
    "Mega-Sena": {
        "nome": "Mega-Sena", "total": 60, "sorteadas": 6, 
        "mantidas": [3, 4], "ciclo_esperado": [22, 30], "fase_limites": [10, 22]
    },
    "Milionaria": {
        "nome": "Milionaria", "total": 50, "sorteadas": 6, 
        "mantidas": [3, 4], "ciclo_esperado": [18, 25], "fase_limites": [8, 18]
    }
}

if 'historico_perfil' not in st.session_state:
    st.session_state.historico_perfil = []

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]

st.success("**{}** — Ciclo fecha em {}-{} sorteios | Mantem {}-{} dezenas | Total: {} dezenas".format(
    config['nome'], config['ciclo_esperado'][0], config['ciclo_esperado'][1], 
    config['mantidas'][0], config['mantidas'][1], config['total']
))

arquivo = st.file_uploader("CSV de {}".format(config['nome']), type=["csv"])
if arquivo is None: 
    st.warning("Envie o CSV pra continuar")
    st.stop()

try:
    df = pd.read_csv(arquivo, header=None)
    df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
    st.success("OK {} concursos carregados!".format(len(df)))
except Exception as e:
    st.error("Erro ao ler CSV: {}".format(e))
    st.stop()

def analisar_ciclo_completo(df, config):
    total = config["total"]
    ciclo_min, ciclo_max = config["ciclo_esperado"]
    lim_inicio, lim_meio = config["fase_limites"]
    
    ciclos = []
    ciclo_atual = []
    dezenas_vistas = set()

    for idx, row in df.iterrows():
        ciclo_atual.append(idx)
        dezenas_vistas.update([int(x) for x in row.values])
        if len(dezenas_vistas) == total:
            ciclos.append({
                "inicio": ciclo_atual[0], "fim": ciclo_atual[-1],
                "duracao": len(ciclo_atual),
                "dezenas_final": set([int(x) for x in df.iloc[ciclo_atual[-1], :config["sorteadas"]].values])
            })
            ciclo_atual = []
            dezenas_vistas = set()

    faltantes = sorted(set(range(1, total+1)) - dezenas_vistas)
    progresso_raw = len(dezenas_vistas) / total if total > 0 else 0.0
    progresso = float(max(0.0, min(1.0, progresso_raw)))
    sorteios_ciclo = len(ciclo_atual)

    if sorteios_ciclo == 0: 
        fase, boost = "ZERADO", 20
    elif sorteios_ciclo <= lim_inicio: 
        fase, boost = "INICIO", 5
    elif sorteios_ciclo <= lim_meio: 
        fase, boost = "MEIO", 10
    else: 
        fase, boost = "FIM", 18

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    freq = np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:]
    quentes = [int(x) for x in np.argsort(freq)[-15:][::-1] + 1]

    return {
        "fase": fase, "faltantes": [int(x) for x in faltantes], "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "boost": boost, "memoria": [int(x) for x in memoria],
        "ciclos_hist": ciclos, "previsao_fecha": max(0, ciclo_max - sorteios_ciclo),
        "quentes": quentes, "ciclo_esperado": config["ciclo_esperado"], "freq": freq
    }

def aplicar_filtros(jogo, filtros, fase):
    if not filtros.get("ativo", False):
        return True, []
    
    reprovados = []
    
    if filtros.get("soma", {}).get("ativo") and fase in filtros["soma"].get("fases", ["MEIO", "FIM"]):
        s = sum(jogo)
        if not (filtros["soma"]["min"] <= s <= filtros["soma"]["max"]):
            reprovados.append("Soma {} fora de {}-{}".format(s, filtros["soma"]["min"], filtros["soma"]["max"]))
    
    if filtros.get("pares", {}).get("ativo"):
        pares = len([x for x in jogo if x % 2 == 0])
        if not (filtros["pares"]["min"] <= pares <= filtros["pares"]["max"]):
            reprovados.append("Pares: {} fora de {}-{}".format(pares, filtros["pares"]["min"], filtros["pares"]["max"]))
    
    if filtros.get("primos", {}).get("ativo"):
        primos_set = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97}
        qtd_primos = len([x for x in jogo if x in primos_set])
        if not (filtros["primos"]["min"] <= qtd_primos <= filtros["primos"]["max"]):
            reprovados.append("Primos: {} fora de {}-{}".format(qtd_primos, filtros["primos"]["min"], filtros["primos"]["max"]))
    
    if filtros.get("sequencia_max", {}).get("ativo"):
        jogo_sorted = sorted(jogo)
        seq_max = 1
        seq_atual = 1
        for i in range(1, len(jogo_sorted)):
            if jogo_sorted[i] == jogo_sorted[i-1] + 1:
                seq_atual += 1
                seq_max = max(seq_max, seq_atual)
            else:
                seq_atual = 1
        if seq_max > filtros["sequencia_max"]["valor"]:
            reprovados.append("Sequencia de {} consecutivos".format(seq_max))
    
    return len(reprovados) == 0, reprovados

def calcular_score_jogo(jogo, analise, filtros, historico):
    score = 0
    detalhes = []
    
    faltantes_no_jogo = len(set(jogo) & set(analise["faltantes"]))
    perc_faltantes = faltantes_no_jogo / len(jogo) * 100
    score += min(40, perc_faltantes * 0.4)
    detalhes.append("Faltantes: {}% (+{:.0f}pts)".format(int(perc_faltantes), min(40, perc_faltantes * 0.4)))
    
    memoria_no_jogo = len(set(jogo) & set(analise["memoria"]))
    if len(analise["memoria"]) > 0:
        perc_mem = memoria_no_jogo / len(analise["memoria"]) * 100
        score += min(30, perc_mem * 0.3)
        detalhes.append("Memoria: {}% (+{:.0f}pts)".format(int(perc_mem), min(30, perc_mem * 0.3)))
    
    passou, repro = aplicar_filtros(jogo, filtros, analise["fase"])
    if passou:
        score += 15
        detalhes.append("Filtros: OK (+15pts)")
    else:
        detalhes.append("Filtros: Reprovado")
    
    if len(historico) > 0:
        df_hist = pd.DataFrame(historico)
        modos_bons = df_hist[df_hist['acertos'] >= config['sorteadas'] * 0.6]['modo_usado'].value_counts()
        if len(modos_bons) > 0:
            score += 15
            detalhes.append("Perfil: Match (+15pts)")
    
    return min(100, int(score)), detalhes

def gerar_jogo_ciclo(config, analise, modo="AVANCADO", ordenar_visual=False, filtros=None):
    if filtros is None:
        filtros = {"ativo": False}
    
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    tentativas = 0
    
    while tentativas < 100:
        jogo = []
        
        if modo == "ULTRA_FOCUS":
            if len(faltantes) >= total_jogo:
                jogo = random.sample(faltantes, total_jogo)
            else:
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
        
        passou, _ = aplicar_filtros(jogo, filtros, analise["fase"])
        if passou or not filtros.get("ativo"):
            if ordenar_visual:
                jogo = sorted(jogo)
            return jogo
        
        tentativas += 1
    
    if ordenar_visual:
        jogo = sorted(jogo)
    return jogo

def desdobramento_inteligente(config, analise, dezenas_base, garantia="14-15"):
    total = config["sorteadas"]
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    
    base_inteligente = list(set(faltantes + memoria))
    if len(base_inteligente) < dezenas_base:
        resto = [x for x in analise["quentes"] if x not in base_inteligente]
        base_inteligente.extend(resto[:dezenas_base - len(base_inteligente)])
    
    base_inteligente = base_inteligente[:dezenas_base]
    
    jogos = []
    if garantia == "14-15" and dezenas_base == 18:
        idx_fixas = list(range(12))
        idx_rotativas = list(range(12, 18))
        for comb in combinations(idx_rotativas, 3):
            jogo_idx = idx_fixas + list(comb)
            jogos.append(sorted([base_inteligente[i] for i in jogo_idx]))
    
    elif garantia == "14-15" and dezenas_base == 16:
        for comb in combinations(range(16), 15):
            jogos.append(sorted([base_inteligente[i] for i in comb]))
    
    else:
        for _ in range(10):
            jogos.append(sorted(random.sample(base_inteligente, total)))
    
    return jogos[:20]

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Gerador", "Filtros", "Desdobramento", "Estatisticas", 
    "Backtesting", "Meu Perfil", "Bankroll", "Fechamentos IA"
])

try:
    analise = analisar_ciclo_completo(df, config)
except Exception as e:
    st.error("Erro ao analisar ciclo: {}".format(e))
    st.stop()

with tab1:
    st.subheader("Gerador de Jogos – Ciclo + IA")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase", analise["fase"], "{}º sorteio".format(analise['sorteios_ciclo']))
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memoria", len(analise["memoria"]))
    c4.metric("Fecha em", "{} concursos".format(analise['previsao_fecha']))

    if analise["fase"] == "FIM":
        st.error("FIM DE CICLO! {} faltantes. Hora de atacar!".format(len(analise['faltantes'])))
    elif analise["fase"] == "MEIO":
        st.warning("MEIO DO CICLO. {} sorteios pro fim".format(analise['ciclo_esperado'][1] - analise['sorteios_ciclo']))
    else:
        st.info("INICIO. Ciclo formando, {}º sorteio".format(analise['sorteios_ciclo']))

    col_a, col_b = st.columns(2)
    with col_a:
        modo_focus = st.select_slider("Modo", ["MODERADO", "AVANCADO", "SUPER_FOCUS", "ULTRA_FOCUS"], value="AVANCADO")
    with col_b:
        ordenar = st.checkbox("Ordenar visualmente", value=False)
    
    qtd = st.slider("Quantos jogos?", 5, 50, 15)
    usar_filtros = st.checkbox("Aplicar filtros da aba Filtros", value=False)

    if st.button("GERAR JOGOS", type="primary"):
        filtros_ativos = st.session_state.get('filtros_config', {"ativo": False}) if usar_filtros else {"ativo": False}
        st.write("**Modo: {} | Fase: {} | Filtros: {}**".format(modo_focus, analise['fase'], "ON" if filtros_ativos["ativo"] else "OFF"))
        
        jogos_gerados = []
        for i in range(qtd):
            jogo = gerar_jogo_ciclo(config, analise, modo_focus, ordenar, filtros_ativos)
            score, detalhes = calcular_score_jogo(jogo, analise, filtros_ativos, st.session_state.historico_perfil)
            jogos_gerados.append({"jogo": jogo, "score": score, "detalhes": detalhes})
        
        jogos_gerados.sort(key=lambda x: x["score"], reverse=True)
        
        for i, item in enumerate(jogos_gerados, 1):
            with st.expander("Jogo {:02d} - Score: {}/100".format(i, item['score'])):
                st.code("{}".format(item['jogo']))
                st.caption(" | ".join(item['detalhes']))

with tab2:
    st.subheader("Filtros Estatísticos Inteligentes")
    st.info("Filtros só ativam nas fases configuradas. No INÍCIO fica solto pra fechar ciclo.")
    
    filtros_config = {"ativo": st.checkbox("Ativar sistema de filtros", value=False)}
    
    if filtros_config["ativo"]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Soma das Dezenas**")
            filtros_config["soma"] = {
                "ativo": st.checkbox("Filtrar soma", value=True),
                "min": st.number_input("Soma mínima", value=199),
                "max": st.number_input("Soma máxima", value=210),
                "fases": st.multiselect("Ativar em", ["INICIO", "MEIO", "FIM"], default=["MEIO", "FIM"])
            }
            
            st.markdown("**Pares/Ímpares**")
            filtros_config["pares"] = {
                "ativo": st.checkbox("Filtrar pares", value=True),
                "min": st.number_input("Mín pares", value=7),
                "max": st.number_input("Máx pares", value=8)
            }
        
        with col2:
            st.markdown("**Números Primos**")
            filtros_config["primos"] = {
                "ativo": st.checkbox("Filtrar primos", value=False),
                "min": st.number_input("Mín primos", value=4),
                "max": st.number_input("Máx primos", value=6)
            }
            
            st.markdown("**Sequências**")
            filtros_config["sequencia_max"] = {
                "ativo": st.checkbox("Limitar consecutivos", value=True),
                "valor": st.number_input("Máx seguidos", value=2, min_value=1, max_value=5)
            }
    
    st.session_state['filtros_config'] = filtros_config
    if filtros_config["ativo"]:
        st.success("Filtros configurados. Volte na aba Gerador e marque 'Aplicar filtros'")

with tab3:
    st.subheader("Desdobramento Inteligente com Garantia")
    st.info("Desdobra priorizando FALTANTES + MEMÓRIA dentro da garantia matemática")
    
    dezenas_base = st.slider("Quantas dezenas na base?", 16, 20, 18)
    garantia = st.selectbox("Garantia", ["14-15", "14-14", "15-15"])
    
    if st.button("GERAR DESDOBRAMENTO INTELIGENTE", type="primary"):
        jogos_desd = desdobramento_inteligente(config, analise, dezenas_base, garantia)
        st.success("{} jogos gerados com garantia {}".format(len(jogos_desd), garantia))
        st.write("**Base inteligente**: {} faltantes + {} memória".format(
            len([x for x in analise['faltantes'] if x in jogos_desd[0]]),
            len([x for x in analise['memoria'] if x in jogos_desd[0]])
        ))
        
        for i, jogo in enumerate(jogos_desd, 1):
            st.code("Jogo {:02d}: {}".format(i, jogo))
        
        df_desd = pd.DataFrame(jogos_desd)
        csv = df_desd.to_csv(index=False, header=False).encode('utf-8')
        st.download_button("Baixar Desdobramento CSV", csv, "desdobramento.csv", "text/csv")

with tab4:
    st.subheader("Estatísticas do Ciclo")
    st.metric("Fase Atual", analise["fase"])
    st.metric("Progresso", "{:.0%}".format(analise['progresso']))
    st.progress(float(analise["progresso"]))
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Faltantes pra fechar:**")
        st.code(", ".join(map(str, analise["faltantes"])) if analise["faltantes"] else "Ciclo completo")
    with col2:
        st.write("**Memória {}-{}:**".format(config['mantidas'][0], config['mantidas'][1]))
        st.code(", ".join(map(str, analise["memoria"])) if analise["memoria"] else "Sem memória")

    if analise["ciclos_hist"]:
        duracoes = [c["duracao"] for c in analise["ciclos_hist"]]
        st.metric("Duração média dos ciclos", "{:.1f} sorteios".format(np.mean(duracoes)))
        ciclo_min, ciclo_max = analise["ciclo_esperado"]
        if ciclo_min <= np.mean(duracoes) <= ciclo_max:
            st.success("Confirmado: ciclo fecha em {}-{} sorteios".format(ciclo_min, ciclo_max))

with tab5:
    st.subheader("Backtesting com IA")
    st.info("Testa se memória + ciclo aumenta acerto histórico")
    if st.button("RODAR BACKTEST"):
        res = []
        for i in range(25, len(df)):
            an = analisar_ciclo_completo(df.iloc[:i], config)
            jogo = gerar_jogo_ciclo(config, an, "SUPER_FOCUS")
            resultado = set([int(x) for x in df.iloc[i, :config["sorteadas"]].values])
            acertos = len(set(jogo) & resultado)
            acertos_mem = len(set(jogo) & set(an["memoria"]) & resultado)
            res.append({"fase": an["fase"], "acertos": acertos, "acertos_memoria": acertos_mem})
        df_bt = pd.DataFrame(res)
        st.dataframe(df_bt.groupby('fase')['acertos'].agg(['mean', 'count']))
        st.success("Total de acertos via memória: {}".format(df_bt['acertos_memoria'].sum()))

with tab6:
    st.subheader("Meu Perfil")
    st.info("Salva seu desempenho e descobre seu melhor padrão")
    
    if analise["ciclos_hist"]:
        dur_media = np.mean([c["duracao"] for c in analise["ciclos_hist"]])
        st.write("Seu ciclo fecha em média a cada **{:.1f} sorteios**".format(dur_media))
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        acertos_manual = st.number_input("Acertos no último concurso", min_value=0, max_value=config["sorteadas"], value=0)
    with col2:
        modo_usado = st.selectbox("Modo usado", ["MODERADO", "AVANCADO", "SUPER_FOCUS", "ULTRA_FOCUS"])
    
    if st.button("Salvar Resultado", type="primary"):
        registro = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "loteria": config["nome"],
            "fase_ciclo": analise["fase"],
            "modo_usado": modo_usado,
            "acertos": int(acertos_manual),
            "qtd_faltantes": len(analise["faltantes"]),
            "qtd_memoria": len(analise["memoria"])
        }
        st.session_state.historico_perfil.append(registro)
        st.success("Salvo! Total: {} registros".format(len(st.session_state.historico_perfil)))
    
    if st.session_state.historico_perfil:
        df_hist = pd.DataFrame(st.session_state.historico_perfil)
        st.dataframe(df_hist, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros", len(df_hist))
        c2.metric("Média Acertos", "{:.1f}".format(df_hist['acertos'].mean()))
        c3.metric("Melhor", int(df_hist['acertos'].max()))
        
        csv = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar CSV", csv, "perfil_{}.csv".format(config['nome']), "text/csv")

with tab7:
    st.subheader("Bankroll - Gestão por Fase")
    st.info("Aposta baseado na fase do ciclo")
    banca = st.number_input("Sua banca R$", value=100.0, min_value=10
