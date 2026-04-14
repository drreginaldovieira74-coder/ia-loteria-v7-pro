import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import io

st.set_page_config(page_title="LOTOELITE v74", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:2.4rem; font-weight:800;}
.focus-box {background:#e8f5e9; padding:12px; border-radius:8px; border-left:5px solid #2e7d32;}
</style>
""", unsafe_allow_html=True)

if 'historico_jogos' not in st.session_state:
    st.session_state.historico_jogos = []
if 'perfil_aprendido' not in st.session_state:
    st.session_state.perfil_aprendido = {"focus_medio": 40, "acertos_medio": 0, "total_jogos": 0, "melhor_focus": 40}
if 'ciclos' not in st.session_state:
    st.session_state.ciclos = {}
if 'sugestoes_atuais' not in st.session_state:
    st.session_state.sugestoes_atuais = []

with st.sidebar:
    st.markdown("### 🎯 v74 PREÇOS OFICIAIS")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania", "Dia de Sorte", "Super Sete", "+Milionária", "Loteca"])
    focus = st.slider("Focus", 0, 100, st.session_state.perfil_aprendido["focus_medio"], 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel} ({focus}%)</b></div>', unsafe_allow_html=True)

# PREÇOS OFICIAIS ATUALIZADOS PELO USUÁRIO - 2026
configs = {
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00,"min":6,"max_aposta":15},
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50,"min":15,"max_aposta":20},
    "Quina": {"max":80,"qtd":5,"preco":3.00,"min":5,"max_aposta":15},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00,"min":50,"max_aposta":50},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00,"min":6,"max_aposta":15},
    "Timemania": {"max":80,"qtd":10,"preco":3.50,"min":10,"max_aposta":10},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50,"min":7,"max_aposta":15},
    "Super Sete": {"max":9,"qtd":7,"preco":3.00,"min":7,"max_aposta":21},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00,"min":6,"max_aposta":12},
    "Loteca": {"max":14,"qtd":14,"preco":4.00,"min":14,"max_aposta":14},
}
cfg = configs[loteria]

def gerar_jogo(f):
    base = list(range(1, cfg["max"]+1))
    random.shuffle(base)
    nq = min(int(round(cfg["qtd"]*f/100)), int(len(base)*0.4), cfg["qtd"])
    jogo = random.sample(base, cfg["qtd"])
    return sorted(jogo)

st.markdown('<div class="main-title">🎯 LOTOELITE v74 - PREÇOS OFICIAIS 2026</div>', unsafe_allow_html=True)
st.success(f"{loteria} | Aposta: R$ {cfg['preco']:.2f} | Jogos salvos: {len(st.session_state.historico_jogos)}")

tabs = st.tabs(["💰 Preços","🧠 Perfil","📊 Gráfico","🤖 IA 3","🔒 Fech 21","🎲 Bolões","💾 Meus Jogos","📥 Exportar"])

with tabs[0]:
    st.subheader("💰 Tabela Oficial de Preços - 2026")
    
    dados_precos = []
    for nome, c in configs.items():
        dados_precos.append({
            "Loteria": nome,
            "Preço": f"R$ {c['preco']:.2f}",
            "Dezenas Base": c["qtd"],
            "Volante": f"1-{c['max']}"
        })
    
    df = pd.DataFrame(dados_precos)
    st.dataframe(df, hide_index=True, use_container_width=True)
    
    st.info("✅ Preços atualizados conforme informado: Mega R$6, Quina R$3, Dupla R$3, Super Sete R$3, +Milionária R$6, Loteca R$4")

with tabs[1]:
    col1,col2 = st.columns(2)
    with col1:
        st.metric("Jogos analisados", st.session_state.perfil_aprendido['total_jogos'])
        st.metric("Média acertos", f"{st.session_state.perfil_aprendido['acertos_medio']:.1f}")
    with col2:
        st.metric("Melhor Focus", f"{st.session_state.perfil_aprendido.get('melhor_focus',40)}%")
        st.metric("Focus atual", f"{focus}%")

with tabs[2]:
    df_list = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
    if len(df_list) >= 2:
        df = pd.DataFrame(df_list)
        st.line_chart(df['acertos'])

with tabs[3]:
    if st.button("Gerar 3 Sugestões", type="primary"):
        st.session_state.sugestoes_atuais = [{"focus":f,"jogo":gerar_jogo(f)} for f in [max(10,focus-20), focus, min(95,focus+20)]]
    for i,s in enumerate(st.session_state.sugestoes_atuais,1):
        c1,c2 = st.columns([4,1])
        with c1: st.code(f"S{i} (R${cfg['preco']:.2f}): {' - '.join(f'{n:02d}' for n in s['jogo'])}")
        with c2:
            if st.button("Salvar",key=f"s{i}"):
                st.session_state.historico_jogos.append({"data":datetime.now().strftime("%d/%m %H:%M"),"jogo":s["jogo"],"focus":s["focus"],"loteria":loteria,"acertos":None,"preco":cfg['preco']})
                st.success("Salvo!")

with tabs[4]:
    st.subheader("Fechamento 21 - Lotofácil")
    if loteria == "Lotofácil":
        base = st.multiselect("21 números", list(range(1,26)), default=list(range(1,22)), format_func=lambda x: f"{x:02d}")
        qtd = st.number_input("Jogos",5,50,10)
        if st.button("Gerar") and len(base)==21:
            jogos = [sorted(random.sample(base,15)) for _ in range(qtd)]
            for i,j in enumerate(jogos,1): st.code(f"J{i}: {' - '.join(f'{n:02d}' for n in j)}")
            st.success(f"Total: R$ {qtd * 3.50:.2f}")

with tabs[5]:
    st.subheader("Bolões com Preços Reais")
    col1,col2 = st.columns(2)
    with col1:
        jogos_bolao = st.number_input("Jogos",5,50,15)
    with col2:
        cotas = st.number_input("Cotas",2,20,10)
    
    if st.button("Calcular Bolão", type="primary"):
        custo_total = jogos_bolao * cfg['preco']
        valor_cota = custo_total / cotas
        
        st.markdown(f"""
        ### Bolão {loteria}
        - **Jogos:** {jogos_bolao}
        - **Preço unitário:** R$ {cfg['preco']:.2f}
        - **Custo total:** R$ {custo_total:.2f}
        - **Cotas:** {cotas} x R$ {valor_cota:.2f}
        """)
        
        jogos = [gerar_jogo(focus) for _ in range(min(5,jogos_bolao))]
        for i,j in enumerate(jogos,1):
            st.code(f"{i}: {' - '.join(f'{n:02d}' for n in j)}")

with tabs[6]:
    st.subheader("Meus Jogos")
    total_gasto = sum(j.get('preco',0) for j in st.session_state.historico_jogos)
    st.metric("Total investido", f"R$ {total_gasto:.2f}", f"{len(st.session_state.historico_jogos)} jogos")
    
    for idx in range(len(st.session_state.historico_jogos)-1, max(-1,len(st.session_state.historico_jogos)-10), -1):
        jg = st.session_state.historico_jogos[idx]
        preco = jg.get('preco', configs.get(jg['loteria'],{}).get('preco',0))
        ac = jg.get('acertos')
        c1,c2 = st.columns([4,1])
        with c1:
            st.code(f"J{idx+1} {jg['loteria']} R${preco:.2f}: {' - '.join(f'{n:02d}' for n in jg['jogo'])}")
        with c2:
            if ac is None:
                inp = st.number_input("Ac",0,20,key=f"a{idx}",label_visibility="collapsed")
                if st.button("OK",key=f"ok{idx}"):
                    st.session_state.historico_jogos[idx]['acertos'] = inp
                    st.rerun()
            else:
                st.metric("", f"{ac}")

with tabs[7]:
    st.subheader("Exportar")
    if st.session_state.historico_jogos:
        df = pd.DataFrame(st.session_state.historico_jogos)
        df['jogo_str'] = df['jogo'].apply(lambda x: ' - '.join(f"{n:02d}" for n in x))
        df['preco'] = df.apply(lambda r: r.get('preco', configs.get(r['loteria'],{}).get('preco',0)), axis=1)
        df_exp = df[['data','loteria','preco','focus','acertos','jogo_str']]
        df_exp.columns = ['Data','Loteria','Preço R$','Focus','Acertos','Jogo']
        
        total = df_exp['Preço R$'].sum()
        st.metric("Total investido", f"R$ {total:.2f}")
        st.dataframe(df_exp, hide_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='Jogos')
        st.download_button("📥 Baixar Excel", output.getvalue(), f"lotoelite_{datetime.now().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

st.caption("v74 - Preços oficiais 2026 aplicados")
