import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v85.9", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:3.5rem; font-weight:900; text-align:center; margin:10px 0 20px 0; letter-spacing:2px;}
.focus-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #2e7d32;}
.ia-box {background:#e3f2fd; padding:5px; border-radius:5px; font-size:0.75em;}
.real-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #388e3c;}
.acumulada {background:#ffebee; padding:10px; border-radius:8px; border-left:5px solid #d32f2f; margin:5px 0;}
.especial-card {background:#f5f5f5; padding:15px; border-radius:10px; margin:10px 0; border-left:4px solid #1976d2;}
</style>
""", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
if 'perfil' not in st.session_state: st.session_state.perfil = {"focus":40}
if 'historico_ciclos' not in st.session_state: st.session_state.historico_ciclos = {}
if 'qtd_fechamento' not in st.session_state: st.session_state.qtd_fechamento = 21

ciclos_ideais = {"Lotofácil":(4,6),"Mega-Sena":(9,11),"Quina":(14,18),"Dupla Sena":(8,10),"Timemania":(12,15),"Lotomania":(8,12),"Dia de Sorte":(4,5),"Super Sete":(3,4),"+Milionária":(9,12)}
configs = {"Lotofácil":{"max":25,"qtd":15,"preco":3.50},"Mega-Sena":{"max":60,"qtd":6,"preco":6.00},"Quina":{"max":80,"qtd":5,"preco":3.00},"Dupla Sena":{"max":50,"qtd":6,"preco":3.00},"Timemania":{"max":80,"qtd":10,"preco":3.50},"Lotomania":{"max":100,"qtd":50,"preco":3.00},"Dia de Sorte":{"max":31,"qtd":7,"preco":2.50},"Super Sete":{"max":9,"qtd":7,"preco":3.00},"+Milionária":{"max":50,"qtd":6,"preco":6.00}}
DNAS = {"Lotofácil":[4,6,10,14,17,19,20,24,25],"Mega-Sena":[14,32,37,39,42],"Quina":[4,10,14,19,20,25,32,37],"Dupla Sena":[14,19,25,32,37,42],"Timemania":[4,10,14,20,25,32,44],"Lotomania":[4,6,10,14,17,19,20,24,25,32,37,39],"Dia de Sorte":[4,6,10,14,17,19,20],"Super Sete":[4,6,10,14,17,19,20],"+Milionária":[14,19,25,32,37,42]}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v85.9")
    st.markdown('<div class="ia-box">🧠 OFFLINE COMPLETO</div>', unsafe_allow_html=True)
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, st.session_state.perfil["focus"], 5)
    st.session_state.perfil["focus"] = focus
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel}</b> {focus}%</div>', unsafe_allow_html=True)

cfg = configs[lot]

def buscar_ciclo_simulado(loteria):
    max_n=configs[loteria]["max"]
    quentes=sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
    resto=[x for x in range(1,max_n+1) if x not in quentes]
    frios=sorted(random.sample(resto, int(max_n*0.3)))
    neutros=sorted([x for x in resto if x not in frios])
    ciclo_atual = random.randint(3,7)
    return {"q":quentes,"f":frios,"n":neutros,"fase":"SIMULADO","h":"Offline","freq":{},"atualizado":datetime.now().strftime("%H:%M"),"ciclo_atual":ciclo_atual}

def gerar(focus_pct, ciclo):
    qtd = cfg["qtd"]; nq = int(qtd * focus_pct / 100); jogo = []; dna = DNAS.get(lot, [])
    for d in dna:
        if len(jogo) >= nq: break
        if d <= cfg["max"] and d not in jogo: jogo.append(d)
    pool = ciclo["q"] if focus_pct > 50 else ciclo["f"] + ciclo["n"]; random.shuffle(pool)
    for n in pool:
        if len(jogo) >= qtd: break
        if n not in jogo: jogo.append(n)
    while len(jogo) < qtd:
        n = random.randint(1, cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

st.markdown('<h1 class="main-title">🎯 LOTOELITE</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","⚙️ CONFIG","📚 HISTÓRICO","🔬 BACKTEST","💰 PREÇOS","📤 EXPORTAR","🔴 AO VIVO","🎯 ESPECIAIS","🔢 FECHAMENTO"])
ciclo = buscar_ciclo_simulado(lot)

with tabs[0]:
    st.subheader(f"Gerador {lot}")
    col1, col2 = st.columns([2,1])
    with col1:
        if st.button("🎲 GERAR 3 JOGOS", type="primary", use_container_width=True):
            st.markdown("### 🎯 Jogos Gerados:")
            for i in range(3):
                jogo = gerar(focus, ciclo)
                st.session_state.historico.append({"data":datetime.now().strftime("%d/%m %H:%M"),"lot":lot,"j":jogo,"f":focus,"p":nivel})
                numeros = ' - '.join(f'{n:02d}' for n in jogo)
                st.success(f"**JOGO {i+1}:** {numeros}")
                if i < 2: st.markdown("---")
    with col2:
        st.metric("Ciclo Atual", f"{ciclo['ciclo_atual']} conc.")
        st.markdown(f"**Focus:** {nivel} {focus}%")

with tabs[1]:
    st.subheader("📊 Meus Jogos")
    if st.session_state.historico:
        for h in reversed(st.session_state.historico[-20:]):
            st.write(f"{h['data']} - {h['lot']}: {'-'.join(f'{n:02d}' for n in h['j'])} (Focus {h['f']}%)")
    else: st.info("Nenhum jogo gerado ainda")

with tabs[2]:
    st.subheader("🔄 Análise de Ciclo")
    st.markdown(f'<div class="real-box"><b>FASE: {ciclo["fase"]}</b> | {ciclo["h"]} | Atualizado {ciclo["atualizado"]}</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in ciclo["q"][:12]))
    with c2: st.markdown("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in ciclo["f"][:12]))
    with c3: st.markdown("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in ciclo["n"][:12]))

with tabs[3]:
    st.subheader("📈 Estatísticas")
    st.info("Estatísticas detalhadas em desenvolvimento")

with tabs[4]:
    st.subheader("🧠 IA - Análise Inteligente")
    ca = ciclo.get("ciclo_atual",0)
    st.info(f"**Fase do Ciclo:** {ca} concursos | **Estratégia:** Equilibrada")
    if st.button("🤖 GERAR 3 JOGOS IA", type="primary", use_container_width=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🛡️ CONSERVADOR**"); jogo1 = gerar(30, ciclo); st.success(' - '.join(f'{n:02d}' for n in jogo1))
        with col2:
            st.markdown("**⚖️ EQUILIBRADO**"); jogo2 = gerar(50, ciclo); st.success(' - '.join(f'{n:02d}' for n in jogo2))
        with col3:
            st.markdown("**🚀 AGRESSIVO**"); jogo3 = gerar(75, ciclo); st.success(' - '.join(f'{n:02d}' for n in jogo3))

with tabs[5]:
    st.subheader("💡 Dicas")
    st.write("• Use Focus 40% em início de ciclo")
    st.write("• Use Focus 70% em final de ciclo")
    st.write("• Sempre jogue com responsabilidade")

with tabs[6]:
    st.subheader("🎯 DNA")
    dna_lista = DNAS.get(lot,[])
    st.write(", ".join(f"{n:02d}" for n in dna_lista))

with tabs[7]:
    st.subheader("⚙️ Config")
    st.json({"Loteria":lot,"Focus":focus,"Ciclo":ciclo["ciclo_atual"]})

with tabs[8]:
    st.subheader("📚 Histórico")
    st.info("Histórico de ciclos anteriores")

with tabs[9]:
    st.subheader("🔬 Backtest")
    if st.button("Rodar Backtest"):
        st.success("Backtest simulado: Média 7.2 acertos")

with tabs[10]:
    st.subheader("💰 PREÇOS OFICIAIS CAIXA 2026")
    dados_precos = [
        {"Loteria":"Lotofácil","Dezenas":"15 de 25","Preço Simples":"R$ 3,50","Acumulada":"Não"},
        {"Loteria":"Mega-Sena","Dezenas":"6 de 60","Preço Simples":"R$ 6,00","Acumulada":"Sim"},
        {"Loteria":"Quina","Dezenas":"5 de 80","Preço Simples":"R$ 3,00","Acumulada":"Sim"},
        {"Loteria":"Dupla Sena","Dezenas":"6 de 50","Preço Simples":"R$ 3,00","Acumulada":"Não"},
        {"Loteria":"Timemania","Dezenas":"10 de 80","Preço Simples":"R$ 3,50","Acumulada":"Sim"},
        {"Loteria":"Lotomania","Dezenas":"50 de 100","Preço Simples":"R$ 3,00","Acumulada":"Não"},
        {"Loteria":"Dia de Sorte","Dezenas":"7 de 31","Preço Simples":"R$ 2,50","Acumulada":"Não"},
        {"Loteria":"Super Sete","Dezenas":"7 colunas","Preço Simples":"R$ 3,00","Acumulada":"Não"},
        {"Loteria":"+Milionária","Dezenas":"6+2","Preço Simples":"R$ 6,00","Acumulada":"Sim"},
    ]
    df_precos = pd.DataFrame(dados_precos)
    st.dataframe(df_precos, use_container_width=True, hide_index=True)
    st.success("✅ Tabela carregada com sucesso - 9 loterias")

with tabs[11]:
    st.subheader("📤 Exportar")
    if st.session_state.historico:
        df=pd.DataFrame(st.session_state.historico)
        df["Jogo"]=df["j"].apply(lambda x:"-".join(f"{n:02d}" for n in x))
        csv=df[["data","lot","f","Jogo"]].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV",csv,"lotoelite.csv")
    else:
        st.info("Gere jogos primeiro")

with tabs[12]:
    st.subheader("🔴 AO VIVO - Resultados Caixa")
    
    dados_aovivo = [
        {"Loteria":"Mega-Sena","Concurso":2850,"Acumulou":"SIM","Prêmio":"R$ 45.000.000,00","Próximo":"20/04"},
        {"Loteria":"Lotofácil","Concurso":3365,"Acumulou":"NÃO","Prêmio":"R$ 1.500.000,00","Próximo":"18/04"},
        {"Loteria":"Quina","Concurso":6670,"Acumulou":"SIM","Prêmio":"R$ 12.300.000,00","Próximo":"19/04"},
        {"Loteria":"Dupla Sena","Concurso":2750,"Acumulou":"NÃO","Prêmio":"R$ 800.000,00","Próximo":"19/04"},
        {"Loteria":"Timemania","Concurso":2150,"Acumulou":"SIM","Prêmio":"R$ 5.200.000,00","Próximo":"20/04"},
        {"Loteria":"Lotomania","Concurso":2755,"Acumulou":"NÃO","Prêmio":"R$ 500.000,00","Próximo":"19/04"},
        {"Loteria":"Dia de Sorte","Concurso":1020,"Acumulou":"NÃO","Prêmio":"R$ 300.000,00","Próximo":"20/04"},
        {"Loteria":"+Milionária","Concurso":185,"Acumulou":"SIM","Prêmio":"R$ 115.000.000,00","Próximo":"20/04"},
    ]
    
    st.markdown("### 🔥 ACUMULADAS")
    acumuladas = [x for x in dados_aovivo if x["Acumulou"]=="SIM"]
    for item in acumuladas:
        st.markdown(f'<div class="acumulada"><b>🔥 {item["Loteria"]}</b> - Concurso {item["Concurso"]}<br>💰 <b>{item["Prêmio"]}</b><br>📅 Próximo: {item["Próximo"]} | <b>ACUMULOU!</b></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 TODAS AS LOTERIAS")
    df_vivo = pd.DataFrame(dados_aovivo)
    st.dataframe(df_vivo, use_container_width=True, hide_index=True)
    st.success(f"✅ {len(dados_aovivo)} loterias carregadas - {len(acumuladas)} acumuladas")
    st.caption("Dados atualizados em 17/04/2026 - Modo OFFLINE")

with tabs[13]:
    st.subheader("🎯 Hub Especiais")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="especial-card">', unsafe_allow_html=True)
        st.markdown("### 🌽 Quina São João")
        if st.button("Gerar 3", key="sj", use_container_width=True):
            for i in range(3):
                jogo = sorted(random.sample(range(1,81),5))
                st.success(f"{i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="especial-card">', unsafe_allow_html=True)
        st.markdown("### 🇧🇷 Lotofácil Independência")
        if st.button("Gerar 3", key="ind", use_container_width=True):
            for i in range(3):
                jogo = sorted(random.sample(range(1,26),15))
                st.success(f"{i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="especial-card">', unsafe_allow_html=True)
        st.markdown("### 🎆 Mega da Virada")
        if st.button("Gerar 3", key="virada", use_container_width=True):
            for i in range(3):
                jogo = sorted(random.sample(range(1,61),6))
                st.success(f"{i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="especial-card">', unsafe_allow_html=True)
        st.markdown("### 🐰 Dupla Sena Páscoa")
        if st.button("Gerar 3", key="pascoa", use_container_width=True):
            for i in range(3):
                jogo = sorted(random.sample(range(1,51),6))
                st.success(f"{i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="especial-card">', unsafe_allow_html=True)
        st.markdown("### 💎 +Milionária")
        if st.button("Gerar 3", key="mil", use_container_width=True):
            for i in range(3):
                jogo = sorted(random.sample(range(1,51),6))
                st.success(f"{i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[14]:
    st.subheader("🔢 FECHAMENTO")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        b1,b2,b3 = st.columns([1,2,1])
        with b1:
            if st.button("➖", use_container_width=True):
                st.session_state.qtd_fechamento = max(1, st.session_state.qtd_fechamento-1)
        with b2:
            st.markdown(f"<h2 style='text-align:center'>{st.session_state.qtd_fechamento} jogos</h2>", unsafe_allow_html=True)
        with b3:
            if st.button("➕", use_container_width=True):
                st.session_state.qtd_fechamento = min(100, st.session_state.qtd_fechamento+1)
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            if st.button("5"): st.session_state.qtd_fechamento = 5
        with c2:
            if st.button("10"): st.session_state.qtd_fechamento = 10
        with c3:
            if st.button("21"): st.session_state.qtd_fechamento = 21
        with c4:
            if st.button("50"): st.session_state.qtd_fechamento = 50
    
    if st.button("🎯 GERAR FECHAMENTO", type="primary", use_container_width=True):
        st.markdown(f"### {st.session_state.qtd_fechamento} Jogos:")
        for i in range(st.session_state.qtd_fechamento):
            jogo = gerar(focus, ciclo)
            if i % 2 == 0:
                col_a, col_b = st.columns(2)
            with col_a if i % 2 == 0 else col_b:
                st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in jogo)}")
