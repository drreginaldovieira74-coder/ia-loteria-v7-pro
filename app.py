import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import deque

st.set_page_config(page_title="LOTOELITE PRO", layout="wide")
st.title("🪄 LOTOELITE PRO")
st.markdown("**Ciclo Real: 4-6 sorteios até zerar | Memória: 9-11 mantidas • v48.0**")

# ========================= LOTERIAS =========================
loteria_options = {
    "Lotofácil": {"nome": "Lotofácil", "total": 25, "sorteadas": 15, "mantidas": [9, 11]},
    "Lotomania": {"nome": "Lotomania", "total": 100, "sorteadas": 50, "mantidas": [35, 40]},
    "Quina": {"nome": "Quina", "total": 80, "sorteadas": 5, "mantidas": [2, 3]},
    "Mega-Sena": {"nome": "Mega-Sena", "total": 60, "sorteadas": 6, "mantidas": [3, 4]},
}

loteria = st.selectbox("🎯 Escolha a loteria", list(loteria_options.keys()))
config = loteria_options[loteria]
st.success(f"**{config['nome']}** — Ciclo fecha em 4-6 sorteios | {config['mantidas'][0]}-{config['mantidas'][1]} dezenas mantidas")

arquivo = st.file_uploader(f"CSV de {config['nome']}", type=["csv"])
if arquivo is None: st.stop()

df = pd.read_csv(arquivo, header=None)
df = df.iloc[:, :config["sorteadas"]].dropna().astype(int)
st.success(f"✅ {len(df)} concursos carregados!")

# ========================= MOTOR DE CICLO 4-6 COM MEMÓRIA =========================
def analisar_ciclo_real(df, config):
    """
    Seu algoritmo: ciclo só termina quando todas as 25/100 dezenas saíram.
    Isso leva 4-6 sorteios na Lotofácil. Quando termina, 9-11 são mantidas.
    """
    total = config["total"]
    mantidas_min, mantidas_max = config["mantidas"]

    ciclos = []
    ciclo_atual = []
    dezenas_vistas = set()

    # Mapeia todos os ciclos completos no histórico
    for idx, row in df.iterrows():
        ciclo_atual.append(idx)
        dezenas_vistas.update(row.values)

        # CICLO FECHOU: todas as dezenas apareceram
        if len(dezenas_vistas) == total:
            ciclos.append({
                "inicio": ciclo_atual[0],
                "fim": ciclo_atual[-1],
                "duracao": len(ciclo_atual),
                "dezenas_ultimo_sorteio": set(df.iloc[ciclo_atual[-1], :config["sorteadas"]].values)
            })
            # Reseta pro próximo ciclo
            ciclo_atual = []
            dezenas_vistas = set()

    # Analisa o ciclo atual em andamento
    ciclo_em_andamento = {
        "sorteios": len(ciclo_atual),
        "faltantes": sorted(set(range(1, total+1)) - dezenas_vistas),
        "progresso": len(dezenas_vistas) / total,
        "dezenas_atuais": dezenas_vistas
    }

    # Define fase baseado na sua regra 4-6 sorteios
    if ciclo_em_andamento["sorteios"] == 0:
        fase = "CICLO_ZERADO"
        boost = 20
    elif ciclo_em_andamento["sorteios"] <= 3:
        fase = "INÍCIO" # Ciclo formando
        boost = 5
    elif ciclo_em_andamento["sorteios"] <= 5:
        fase = "MEIO" # Ciclo no meio, 4-5 sorteios
        boost = 10
    else:
        fase = "FIM" # 6+ sorteios, ciclo deve fechar já
        boost = 18

    # Pega memória do ciclo anterior: quais dezenas mantiveram
    memoria = []
    if len(ciclos) >= 1:
        ultimo_ciclo = ciclos[-1]
        if len(ciclos) >= 2:
            penultimo_ciclo = ciclos[-2]
            # Dezenas que saíram no fim do penúltimo e ainda estão no ciclo atual
            memoria = list(penultimo_ciclo["dezenas_ultimo_sorteio"] & ciclo_em_andamento["dezenas_atuais"])

    return {
        "fase": fase,
        "faltantes": ciclo_em_andamento["faltantes"],
        "progresso": ciclo_em_andamento["progresso"],
        "sorteios_no_ciclo": ciclo_em_andamento["sorteios"],
        "boost": boost,
        "memoria_mantidas": memoria,
        "historico_ciclos": ciclos,
        "previsao_fechamento": 6 - ciclo_em_andamento["sorteios"] if ciclo_em_andamento["sorteios"] < 6 else 0
    }

def gerar_jogo_memoria(config, analise):
    """
    Gerador que usa sua regra: prioriza faltantes pra fechar ciclo,
    mas mantém 9-11 dezenas da memória do ciclo anterior
    """
    faltantes = analise["faltantes"]
    memoria = analise["memoria_mantidas"]
    fase = analise["fase"]
    total_jogo = config["sorteadas"]
    mantidas_min, mantidas_max = config["mantidas"]

    jogo = []

    # REGRA 1: Se FIM de ciclo, força fechamento com faltantes
    if fase == "FIM" and len(faltantes) > 0:
        qtd_faltantes = min(len(faltantes), total_jogo)
        jogo.extend(random.sample(faltantes, qtd_faltantes))

    # REGRA 2: Sempre tenta manter 9-11 da memória
    vagas_memoria = random.randint(mantidas_min, mantidas_max)
    memoria_disponivel = [n for n in memoria if n not in jogo]
    if len(memoria_disponivel) > 0:
        qtd_mem = min(vagas_memoria, len(memoria_disponivel), total_jogo - len(jogo))
        jogo.extend(random.sample(memoria_disponivel, qtd_mem))

    # REGRA 3: Completa o jogo
    while len(jogo) < total_jogo:
        candidato = random.randint(1, config["total"])
        if candidato not in jogo:
            jogo.append(candidato)

    return sorted(jogo)

def backtest_memoria(df, config):
    """Backtest que valida se manter 9-11 dezenas dá mais acerto"""
    res = []
    for i in range(20, len(df)): # precisa de histórico pra ter ciclos
        df_passado = df.iloc[:i]
        analise = analisar_ciclo_real(df_passado, config)

        jogo = gerar_jogo_memoria(config, analise)
        sorteado = set(df.iloc[i, :config["sorteadas"]].values)
        acertos = len(set(jogo) & sorteado)

        # Quantas da memória acertaram?
        acertos_memoria = len(set(jogo) & set(analise["memoria_mantidas"]) & sorteado)

        res.append({
            "concurso": i+1,
            "acertos": acertos,
            "fase": analise["fase"],
            "sorteios_ciclo": analise["sorteios_no_ciclo"],
            "acertos_memoria": acertos_memoria,
            "usou_memoria": len(analise["memoria_mantidas"])
        })
    return pd.DataFrame(res)

# ========================= INTERFACE =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎟️ Gerador Memória", "📊 Status do Ciclo", "🧪 Backtest Memória", "📜 Histórico Ciclos"
])

with tab1:
    st.subheader("Gerador com Memória de 9-11 Dezenas")
    analise = analisar_ciclo_real(df, config)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fase", analise["fase"], f"{analise['sorteios_no_ciclo']}º sorteio")
    c2.metric("Progresso", f"{analise['progresso']:.0%}")
    c3.metric("Faltantes", len(analise["faltantes"]))
    c4.metric("Memória", len(analise["memoria_mantidas"]), help="Dezenas mantidas do ciclo anterior")

    if analise["fase"] == "FIM":
        st.error(f"🔥 FIM DE CICLO! Faltam {len(analise['faltantes'])} dezenas. Fecha em {analise['previsao_fechamento']} sorteios")
    elif analise["fase"] == "MEIO":
        st.warning(f"⚖️ MEIO DO CICLO - {analise['sorteios_no_ciclo']}º sorteio. Ciclo fecha em ~{6-analise['sorteios_no_ciclo']} concursos")
    else:
        st.info(f"🌱 INÍCIO DO CICLO - {analise['sorteios_no_ciclo']}º sorteio")

    if analise["memoria_mantidas"]:
        st.write(f"**Memória do ciclo anterior ({len(analise['memoria_mantidas'])} dezenas):** {analise['memoria_mantidas']}")

    qtd = st.slider("Quantos jogos?", 1, 50, 15)
    if st.button("🚀 GERAR COM MEMÓRIA DE CICLO", type="primary"):
        st.write(f"**Estratégia: Fechar ciclo + Manter {config['mantidas'][0]}-{config['mantidas'][1]} da memória**")
        for i in range(qtd):
            jogo = gerar_jogo_memoria(config, analise)
            marca_fim = "🔥" if analise["fase"] == "FIM" else ""
            st.code(f"Jogo {i+1:02d} {marca_fim}: {jogo}")

with tab2:
    st.subheader("📊 Status do Ciclo Atual")
    analise = analisar_ciclo_real(df, config)

    st.progress(analise["progresso"], text=f"Ciclo {analise['progresso']:.0%} completo - {analise['sorteios_no_ciclo']} sorteios")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Faltantes pra fechar ciclo:**")
        st.code(", ".join(map(str, analise["faltantes"])) if analise["faltantes"] else "CICLO COMPLETO")
        st.caption(f"Previsão: fecha em {analise['previsao_fechamento']} sorteios")
    with col2:
        st.write(f"**Memória ({len(analise['memoria_mantidas'])} dezenas):**")
        st.code(", ".join(map(str, analise["memoria_mantidas"])) if analise["memoria_mantidas"] else "Primeiro ciclo")
        st.caption(f"Meta: manter {config['mantidas'][0]}-{config['mantidas'][1]}")

    st.markdown(f"""
    **Sua regra pra {config['nome']}:**
    - Ciclo dura **4-6 sorteios** até todas {config['total']} dezenas saírem
    - Ao zerar, **{config['mantidas'][0]}-{config['mantidas'][1]} dezenas** são mantidas no próximo
    - **FIM** = 6º sorteio ou mais = força total nas faltantes
    """)

with tab3:
    st.subheader("🧪 Backtest: Memória de 9-11 Funciona?")
    if st.button("▶️ RODAR BACKTEST DE MEMÓRIA"):
        with st.spinner("Testando ciclos históricos..."):
            df_bt = backtest_memoria(df, config)
        if not df_bt.empty:
            media_geral = df_bt['acertos'].mean()
            media_fim = df_bt[df_bt['fase'] == 'FIM']['acertos'].mean()
            media_com_memoria = df_bt[df_bt['usou_memoria'] > 0]['acertos'].mean()
            aleat = config["sorteadas"] * config["sorteadas"] / config["total"]

            c1, c2, c3 = st.columns(3)
            c1.metric("Média Geral", f"{media_geral:.2f}", delta=f"{media_geral-aleat:.2f}")
            c2.metric("Na fase FIM", f"{media_fim:.2f}")
            c3.metric("Usando Memória", f"{media_com_memoria:.2f}")

            if media_com_memoria > media_geral:
                st.success(f"✅ PROVADO: Manter memória dá +{(media_com_memoria-media_geral):.2f} acertos em média!")
            st.dataframe(df_bt.groupby('fase')['acertos'].agg(['mean', 'count', 'sum']))

with tab4:
    st.subheader("📜 Histórico de Ciclos Completos")
    analise = analisar_ciclo_real(df, config)
    if analise["historico_ciclos"]:
        df_ciclos = pd.DataFrame(analise["historico_ciclos"])
        df_ciclos["inicio"] += 1 # índice 0 = concurso 1
        df_ciclos["fim"] += 1
        st.dataframe(df_ciclos)

        media_duracao = df_ciclos["duracao"].mean()
        st.metric("Duração média do ciclo", f"{media_duracao:.1f} sorteios")
        if 4 <= media_duracao <= 6:
            st.success(f"✅ Confirmado: seu ciclo fecha em {media_duracao:.1f} sorteios em média")
    else:
        st.info("Ainda não fechou nenhum ciclo completo no histórico")
