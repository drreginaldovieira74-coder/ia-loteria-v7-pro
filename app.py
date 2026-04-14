import streamlit as st
import pandas as pd
import random
from collections import Counter

st.set_page_config(page_title="LOTOELITE COMPLETO v66", layout="wide")

st.title("🎯 LOTOELITE COMPLETO v66")
st.caption("Todas as loterias + Sistema de Ciclos")

# INICIALIZAÇÃO DE TODAS AS LOTERIAS
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'lotofacil': pd.DataFrame([
            {"c":3660,"d":"13/04/2026","n":[1,2,5,6,7,8,10,11,12,14,17,18,22,23,24]},
            {"c":3659,"d":"11/04/2026","n":[3,5,6,7,8,9,10,11,13,14,15,16,17,23,25]},
        ]),
        'lotomania': pd.DataFrame([
            {"c":2909,"d":"08/04/2026","n":[6,10,12,14,15,18,21,23,31,40,45,47,55,69,70,73,77,87,91,93]},
        ]),
        'megasena': pd.DataFrame([
            {"c":2845,"d":"12/04/2026","n":[7,15,23,34,45,56]},
        ]),
        'quina': pd.DataFrame([
            {"c":6701,"d":"12/04/2026","n":[12,24,36,48,72]},
        ]),
        'duplasena': pd.DataFrame([
            {"c":2798,"d":"11/04/2026","n1":[3,14,25,36,47,50],"n2":[5,16,27,38,49,51]},
        ]),
        'timemania': pd.DataFrame([
            {"c":2187,"d":"12/04/2026","n":[4,11,18,25,32,39,46],"time":"FLAMENGO"},
        ]),
        'diadesorte': pd.DataFrame([
            {"c":1023,"d":"10/04/2026","n":[2,8,14,19,23,27,31],"mes":"JUNHO"},
        ]),
        'loteca': pd.DataFrame([]),
        'federal': pd.DataFrame([]),
        'supersete': pd.DataFrame([]),
    }

# MENU DE LOTERIAS
loteria = st.sidebar.selectbox(
    "🎲 Escolha a Loteria",
    ["Lotofácil", "Lotomania", "Mega-Sena", "Quina", "Dupla Sena", 
     "Timemania", "Dia de Sorte", "Loteca", "Federal", "Super Sete"]
)

# CICLOS POR LOTERIA
ciclos_config = {
    "Lotofácil": {"min":4, "max":6, "mantem":"9-11", "total":25, "dezenas":15},
    "Lotomania": {"min":8, "max":12, "mantem":"15-18", "total":100, "dezenas":20},
    "Mega-Sena": {"min":6, "max":10, "mantem":"2-3", "total":60, "dezenas":6},
    "Quina": {"min":5, "max":8, "mantem":"2-3", "total":80, "dezenas":5},
    "Dupla Sena": {"min":6, "max":9, "mantem":"3-4", "total":50, "dezenas":6},
    "Timemania": {"min":7, "max":11, "mantem":"2-3", "total":80, "dezenas":7},
    "Dia de Sorte": {"min":5, "max":8, "mantem":"2-3", "total":31, "dezenas":7},
}

config = ciclos_config.get(loteria, {"min":5, "max":8, "mantem":"?", "total":0, "dezenas":0})

st.sidebar.markdown(f"### Ciclo {loteria}")
st.sidebar.info(f"**Ciclo:** {config['min']}-{config['max']} concursos\n**Mantém:** {config['mantem']} dezenas")

# ABAS (8 ABAS)
t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs([
    "🔄 CICLO", "📊 Resultados", "🎯 Dashboard", "🤖 IA", 
    "🔥 Ultra", "📈 Stats", "🧬 Padrões", "⚙️ Config"
])

# SELECIONAR DADOS
key = loteria.lower().replace("-", "").replace(" ", "").replace("é","e")
if key == "duplasena": key = "duplasena"
elif key == "diadesorte": key = "diadesorte"
elif key == "megasena": key = "megasena"
elif key == "timemania": key = "timemania"
elif key == "supersete": key = "supersete"
else: key = key[:9]

df = st.session_state.dados.get(key, pd.DataFrame())

# ABA 1: CICLO
with t1:
    st.header(f"🔄 Ciclo Real - {loteria}")
    st.success(f"Ciclo natural: {config['min']}-{config['max']} concursos | Mantém {config['mantem']} dezenas")
    
    if not df.empty and 'n' in df.columns:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ciclo = st.slider("Analisar últimos", config['min'], config['max'], (config['min']+config['max'])//2)
            
            if st.button("ANALISAR CICLO", type="primary", use_container_width=True):
                ultimos = df.tail(ciclo)
                todas = []
                for _, r in ultimos.iterrows():
                    if isinstance(r['n'], list):
                        todas.extend(r['n'])
                
                freq = Counter(todas)
                unicas = len(freq)
                
                st.session_state.ciclo_atual = {
                    'loteria': loteria,
                    'ciclo': ciclo,
                    'unicas': unicas,
                    'total': config['total'],
                    'freq': freq,
                    'faltantes': [n for n in range(1, config['total']+1) if n not in freq]
                }
        
        with col2:
            if 'ciclo_atual' in st.session_state and st.session_state.ciclo_atual['loteria'] == loteria:
                info = st.session_state.ciclo_atual
                perc = info['unicas'] / info['total'] * 100
                st.metric("Cobertura", f"{info['unicas']}/{info['total']}", f"{perc:.1f}%")
                st.progress(perc/100)
        
        with col3:
            if 'ciclo_atual' in st.session_state and st.session_state.ciclo_atual['loteria'] == loteria:
                falt = len(st.session_state.ciclo_atual['faltantes'])
                st.metric("Faltam fechar", falt)
                if falt <= 5:
                    st.warning("Fim de ciclo!")
    else:
        st.info(f"Carregue dados de {loteria} na aba Config")

# ABA 2: RESULTADOS
with t2:
    st.header(f"Resultados - {loteria}")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Sem dados de {loteria}. Importe na aba Config.")

# ABA 3: DASHBOARD
with t3:
    st.header("Dashboard Geral")
    
    cols = st.columns(5)
    loterias_dash = ["Lotofácil", "Lotomania", "Mega-Sena", "Quina", "Dupla Sena"]
    
    for i, lot in enumerate(loterias_dash):
        with cols[i]:
            key_dash = lot.lower().replace("-", "").replace(" ", "")
            if key_dash == "megasena": key_dash = "megasena"
            elif key_dash == "duplasena": key_dash = "duplasena"
            
            df_dash = st.session_state.dados.get(key_dash, pd.DataFrame())
            st.metric(lot, f"{len(df_dash)} jogos", "Carregado" if len(df_dash) > 0 else "Vazio")

# ABA 4: IA
with t4:
    st.header(f"🤖 IA - {loteria}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("IA 1: Ciclo")
        if st.button("Gerar", key="ia1", use_container_width=True):
            nums = sorted(random.sample(range(1, config['total']+1), config['dezenas']))
            st.success(" ".join(f"{n:02d}" for n in nums))
    
    with col2:
        st.subheader("IA 2: Equilibrado")
        if st.button("Gerar", key="ia2", use_container_width=True):
            nums = sorted(random.sample(range(1, config['total']+1), config['dezenas']))
            st.success(" ".join(f"{n:02d}" for n in nums))
    
    with col3:
        st.subheader("IA 3: Agressivo")
        if st.button("Gerar", key="ia3", use_container_width=True):
            nums = sorted(random.sample(range(1, config['total']+1), config['dezenas']))
            st.success(" ".join(f"{n:02d}" for n in nums))

# ABA 5: ULTRA
with t5:
    st.header("🔥 Ultra Focus")
    st.write(f"Ultra focado em {loteria} - Ciclo {config['min']}-{config['max']}")

# ABA 6-7: STATS E PADRÕES
with t6:
    st.header("Estatísticas")
with t7:
    st.header("Padrões")

# ABA 8: CONFIG
with t8:
    st.header("⚙️ Configuração - Todas as Loterias")
    
    st.subheader("Importar dados")
    lot_import = st.selectbox("Loteria para importar", list(ciclos_config.keys()))
    
    up = st.file_uploader(f"CSV {lot_import}", type=['csv','xlsx'])
    if up:
        try:
            df_new = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            key_imp = lot_import.lower().replace("-", "").replace(" ", "").replace("é","e")
            if key_imp == "megasena": key_imp = "megasena"
            elif key_imp == "duplasena": key_imp = "duplasena"
            elif key_imp == "diadesorte": key_imp = "diadesorte"
            
            st.session_state.dados[key_imp] = df_new
            st.success(f"✓ {len(df_new)} concursos de {lot_import} carregados!")
            st.rerun()
        except Exception as e:
            st.error(str(e))
    
    st.divider()
    st.write("**Loterias configuradas:**")
    for lot, cfg in ciclos_config.items():
        st.write(f"- {lot}: ciclo {cfg['min']}-{cfg['max']}, mantém {cfg['mantem']}")

st.sidebar.divider()
st.sidebar.caption("v66 - Todas as loterias + Ciclos")
