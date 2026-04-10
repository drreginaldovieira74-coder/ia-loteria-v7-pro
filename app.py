import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import defaultdict

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("LOTOELITE PRO v49.9")
st.markdown("**Ciclo 4-6 sorteios | Memoria 9-11 | IA Ultra Focus**")

loteria_options = {
    "Lotofacil": {"nome": "Lotofacil", "total": 25, "sorteadas": 15, "mantidas": [9, 11]},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "mantidas": [35, 40]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4]},
    "Milionaria": {"nome": "Milionaria", "total": 50, "sorteadas": 6, "mantidas": [3, 4]},
}

loteria = st.selectbox("Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]
st.success("**{}** — Ciclo fecha em 4-6 sorteios | Mantem {}-{} dezenas".format(
    config['nome'], config['mantidas'][0], config['mantidas'][1]))

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
        fase = "ZERADO"
    elif sorteios_ciclo <= 3: 
        fase = "INICIO"
    elif sorteios_ciclo <= 5: 
        fase = "MEIO"
    else: 
        fase = "FIM"

    memoria = []
    if len(ciclos) >= 1:
        memoria = list(ciclos[-1]["dezenas_final"] & dezenas_vistas)

    quentes = [int(x) for x in np.argsort(np.bincount(df.tail(20).values.flatten(), minlength=total+1)[1:])[-15:][::-1] + 1]

    return {
        "fase": fase, "faltantes": [int(x) for x in faltantes], "progresso": progresso,
        "sorteios_ciclo": sorteios_ciclo, "memoria": [int(x) for x in memoria],
        "ciclos_hist": ciclos, "previsao_fecha": max(0, 6 - sorteios_ciclo),
        "quentes": quentes
    }

def gerar_jogo_ciclo(config, analise, modo="AVANCADO"):
    faltantes = analise["faltantes"]
    memoria = analise["memoria"]
    total_jogo = config["sorteadas"]
    m_min, m_max = config["mantidas"]
    jogo = []

    if modo == "ULTRA_FOCUS":
        if len(faltantes) >= total_jogo:
            jogo = random.sample(faltantes, total_jogo)
        else:
            jogo = random.sample(faltantes, len(faltantes))
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
    
    else:
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

    return [int(x) for x in jogo[:total_jogo]]

def fechamento_inteligente_3jogos(config, analise):
    faltantes, memoria, quentes = analise["faltantes"], analise["memoria"], analise["quentes"]
    jogos = []

    j1 = gerar_jogo_ciclo(config, analise, "ULTRA_FOCUS")
    jogos.append({"nome": "Fechar Ciclo", "jogo": j1, "estrategia": "100% faltantes + memoria"})

    base = memoria[:config["mantidas"][1]] if len(memoria) >= config["mantidas"][0] else memoria
    resto = [q for q in quentes if q not in base]
    j2 = sorted(base + random.sample(resto, min(len(resto), config["sorteadas"] - len(base))))
    jogos.append({"nome": "Memoria Pura", "jogo": j2, "estrategia": "{} mantidas + quentes".format(len(base))})

    if len(faltantes) >= config["sorteadas"]:
        j3 = sorted(random.sample(faltantes, config["sorteadas"]))
    else:
        j3 = sorted(faltantes + random.sample([q for q in quentes if q not in faltantes], config["sorteadas"] - len(faltantes)))
    jogos.append({"nome": "Ataque Faltantes", "jogo": j3, "estrategia": "Maximo de faltantes"})

    return jogos

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Gerador de Jogos", "Estatisticas", "Simulador Historico",
    "Backtesting com IA", "Meu Perfil", "Bankroll", "Fechamentos Inteligentes"
])

try:
    analise = analisar_ciclo_completo(df, config)
except Exception as e:
    st.error("Erro ao analisar ciclo: {}".format(e))
    st.stop()

with tab1:
    st.subheader("Gerador de Jogos – Ciclo 4-6 como Motor")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase do Ciclo", analise["fase"], "{}º sorteio".format(analise['sorteios_ciclo']))
    c2.metric("Faltantes", len(analise["faltantes"]))
    c3.metric("Memoria", len(analise["memoria"]))
    c4.metric("Fecha em", "{} concursos".format(analise['previsao_fecha']))

    if analise["fase"] == "FIM":
        st.error("FIM DE CICLO! {} faltantes. Hora de atacar!".format(len(analise['faltantes'])))
    elif analise["fase"] == "MEIO":
        st.warning("MEIO DO CICLO. {} sorteios pro fim".format(6-analise['sorteios_ciclo']))
    else:
        st.info("INICIO. Ciclo formando, {}º sorteio".format(analise['sorteios_ciclo']))

    modo_focus = st.select_slider("Modo Ultra Focus", ["MODERADO", "AVANCADO", "SUPER_FOCUS", "ULTRA_FOCUS"], value="AVANCADO")
    qtd = st.slider("Quantos jogos?", 5, 50, 15)

    if st.button("GERAR JOGOS COM CICLO FORTE", type="primary"):
        st.write("**Modo: {} | Fase: {}**".format(modo_focus, analise['fase']))
        for i in range(qtd):
            jogo = gerar_jogo_ciclo(config, analise, modo_focus)
            st.code("Jogo {:02d}: {}".format(i+1, jogo))

with tab2:
    st.subheader("Estatisticas do Ciclo")
    st.metric("Fase Atual", analise["fase"])
    st.metric("Progresso do Ciclo", "{:.0%}".format(analise['progresso']))
    st.progress(float(analise["progresso"]))
    st.write("**Faltantes pra fechar:**")
    st.code(", ".join(map(str, analise["faltantes"])) if analise["faltantes"] else "Ciclo completo")
    st.write("**Memoria {}-{}:**".format(config['mantidas'][0], config['mantidas'][1]))
    st.code(", ".join(map(str, analise["memoria"])) if analise["memoria"] else "Sem memoria")

    if analise["ciclos_hist"]:
        duracoes = [c["duracao"] for c in analise["ciclos_hist"]]
        st.metric("Duracao media dos ciclos", "{:.1f} sorteios".format(np.mean(duracoes)))
        if 4 <= np.mean(duracoes) <= 6:
            st.success("Confirmado: ciclo fecha em 4-6 sorteios em media")

with tab3:
    st.subheader("Simulador Historico por Ciclo")
    st.info("Simula como seria apostar em cada fase do ciclo")
    if st.button("Rodar Simulacao"):
        fases_res = defaultdict(list)
        for i in range(20, len(df)):
            an = analisar_ciclo_completo(df.iloc[:i], config)
            jogo = gerar_jogo_ciclo(config, an, "AVANCADO")
            acertos = len(set(jogo) & set([int(x) for x in df.iloc[i, :config["sorteadas"]].values]))
            fases_res[an["fase"]].append(acertos)
        for fase, acertos in fases_res.items():
            st.metric("Media na fase {}".format(fase), "{:.2f} acertos".format(np.mean(acertos)), "{} concursos".format(len(acertos)))

with tab4:
    st.subheader("Backtesting com IA - Memoria 9-11")
    st.info("Testa se manter memoria + forcar fim de ciclo da mais acerto")
    if st.button("RODAR BACKTEST COMPLETO"):
        res = []
        for i in range(25, len(df)):
            an = analisar_ciclo_completo(df.iloc[:i], config)
            jogo = gerar_jogo_ciclo(config, an, "SUPER_FOCUS")
            acertos = len(set(jogo) & set([int(x) for x in df.iloc[i, :config["sorteadas"]].values]))
            acertos_mem = len(set(jogo) & set(an["memoria"]) & set([int(x) for x in df.iloc[i, :config["sorteadas"]].values]))
            res.append({"fase": an["fase"], "acertos": acertos, "acertos_memoria": acertos_mem})
        df_bt = pd.DataFrame(res)
        st.dataframe(df_bt.groupby('fase')['acertos'].agg(['mean', 'count']))
        st.success("Media com memoria: {} acertos vieram da memoria".format(df_bt['acertos_memoria'].sum()))

with tab5:
    st.subheader("Meu Perfil - Aprendizado do Ciclo")
    st.info("IA aprende seu padrao de ciclo e salva seu desempenho")
    
    if 'historico_perfil' not in st.session_state:
        st.session_state.historico_perfil = []
    
    if analise["ciclos_hist"]:
        dur_media = np.mean([c["duracao"] for c in analise["ciclos_hist"]])
        st.write("Seu ciclo fecha em media a cada **{:.1f} sorteios**".format(dur_media))
        if analise["sorteios_ciclo"] > dur_media + 1:
            st.warning("Ciclo atual ja passou da media. Esta no {}º sorteio, media e {:.1f}".format(analise['sorteios_ciclo'], dur_media))
        else:
            st.success("Ciclo dentro do esperado")
    
    st.write("**Memoria detectada:** voce mantem {} dezenas entre ciclos".format(len(analise['memoria'])))
    
    st.divider()
    st.subheader("Salvar Desempenho")
    
    col1, col2 = st.columns(2)
    with col1:
        acertos_manual = st.number_input("Quantos acertos voce fez no ultimo concurso?", min_value=0, max_value=config["sorteadas"], value=0)
    with col2:
        modo_usado = st.selectbox("Modo que voce usou", ["MODERADO", "AVANCADO", "SUPER_FOCUS", "ULTRA_FOCUS"])
    
    if st.button("Salvar Meu Resultado", type="primary"):
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
        total_reg = len(st.session_state.historico_perfil)
        st.success("Resultado salvo! Total: {} registros".format(total_reg))
    
    if st.session_state.historico_perfil:
        st.divider()
        st.subheader("Seu Historico")
        df_historico = pd.DataFrame(st.session_state.historico_perfil)
        st.dataframe(df_historico, use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", len(df_historico))
        c2.metric("Media de Acertos", "{:.1f}".format(df_historico['acertos'].mean()))
        c3.metric("Melhor Resultado", int(df_historico['acertos'].max()))
        
        melhor_modo = df_historico.groupby('modo_usado')['acertos'].mean().idxmax()
        media_melhor = df_historico[df_historico['modo_usado']==melhor_modo]['acertos'].mean()
        st.info("Seu melhor modo: {} com media de {:.1f} acertos".format(melhor_modo, media_melhor))
        
        csv = df_historico.to_csv(index=False).encode('utf-8')
        nome_arquivo = "lotoelite_perfil_{}_{}.csv".format(config['nome'], pd.Timestamp.now().strftime('%Y%m%d'))
        st.download_button(
            label="Baixar Historico CSV",
            data=csv,
            file_name=nome_arquivo,
            mime="text/csv"
        )
        
        if st.button("Limpar Historico"):
            st.session_state.historico_perfil = []
            st.rerun()
    else:
        st.info("Salve seu primeiro resultado pra comecar a montar seu perfil")

with tab6:
    st.subheader("Bankroll - Estrategia por Fase")
    st.info("Sugestao de aposta baseada na fase do ciclo")
    banca = st.number_input("Sua banca R$", value=100.0)
    if analise["fase"] == "FIM":
        st.error("FIM DE CICLO: Aposte {:.2f} - 40% da banca. Maxima agressividade".format(banca*0.4))
    elif analise["fase"] == "MEIO":
        st.warning("MEIO: Aposte {:.2f} - 20% da banca".format(banca*0.2))
    else:
        st.info("INICIO: Aposte {:.2f} - 10% da banca. Modo observacao".format(banca*0.1))

with tab7:
    st.subheader("Fechamentos Inteligentes")
    st.info("IA escolhe 3 jogos matematicos baseado no ciclo 4-6 + memoria 9-11")
    if st.button("Gerar 3 Melhores Fechamentos pela IA", type="primary"):
        jogos_ia = fechamento_inteligente_3jogos(config, analise)
        for idx, j in enumerate(jogos_ia, 1):
            st.markdown("### Jogo IA {}: {}".format(idx, j['nome']))
            st.caption(j['estrategia'])
            st.code("{}".format(j['jogo']))
        st.success("3 jogos gerados com foco total no ciclo + memoria")
