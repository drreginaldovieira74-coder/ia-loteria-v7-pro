import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests

st.set_page_config(page_title="LOTOELITE v85.5", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:3.5rem; font-weight:900; text-align:center; margin:10px 0 20px 0; letter-spacing:2px;}
.focus-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #2e7d32;}
.ia-box {background:#e3f2fd; padding:5px; border-radius:5px; font-size:0.75em;}
.real-box {background:#e8f5e9; padding:8px; border-radius:6px; border-left:4px solid #388e3c;}
.acumulada {background:#ffebee; padding:10px; border-radius:8px; border-left:5px solid #d32f2f; margin:5px 0;}
</style>
""", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
if 'perfil' not in st.session_state: st.session_state.perfil = {"focus":40}
if 'ciclos' not in st.session_state: st.session_state.ciclos = {}
if 'sugestoes_por_loteria' not in st.session_state: st.session_state.sugestoes_por_loteria = {}
if 'dados_caixa' not in st.session_state: st.session_state.dados_caixa = {}
if 'ao_vivo' not in st.session_state: st.session_state.ao_vivo = []
if 'historico_ciclos' not in st.session_state: st.session_state.historico_ciclos = {}

ciclos_ideais = {"Lotofácil":(4,6),"Mega-Sena":(9,11),"Quina":(14,18),"Dupla Sena":(8,10),"Timemania":(12,15),"Lotomania":(8,12),"Dia de Sorte":(4,5),"Super Sete":(3,4),"+Milionária":(9,12)}
configs = {"Lotofácil":{"max":25,"qtd":15,"preco":3.50,"api":"lotofacil"},"Mega-Sena":{"max":60,"qtd":6,"preco":6.00,"api":"megasena"},"Quina":{"max":80,"qtd":5,"preco":3.00,"api":"quina"},"Dupla Sena":{"max":50,"qtd":6,"preco":3.00,"api":"duplasena"},"Timemania":{"max":80,"qtd":10,"preco":3.50,"api":"timemania"},"Lotomania":{"max":100,"qtd":50,"preco":3.00,"api":"lotomania"},"Dia de Sorte":{"max":31,"qtd":7,"preco":2.50,"api":"diadesorte"},"Super Sete":{"max":9,"qtd":7,"preco":3.00,"api":"supersete"},"+Milionária":{"max":50,"qtd":6,"preco":6.00,"api":"maismilionaria"}}
DNAS = {"Lotofácil":[4,6,10,14,17,19,20,24,25],"Mega-Sena":[14,32,37,39,42],"Quina":[4,10,14,19,20,25,32,37],"Dupla Sena":[14,19,25,32,37,42],"Timemania":[4,10,14,20,25,32,44],"Lotomania":[4,6,10,14,17,19,20,24,25,32,37,39],"Dia de Sorte":[4,6,10,14,17,19,20],"Super Sete":[4,6,10,14,17,19,20],"+Milionária":[14,19,25,32,37,42]}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v85.5")
    st.markdown('<div class="ia-box">🧠 v85.5 RADAR FIX</div>', unsafe_allow_html=True)
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, st.session_state.perfil["focus"], 5)
    st.session_state.perfil["focus"] = focus
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel}</b> {focus}%</div>', unsafe_allow_html=True)

cfg = configs[lot]

def buscar_ciclo_real(loteria):
    try:
        api_nome = configs[loteria]["api"]; max_n = configs[loteria]["max"]
        base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api_nome}"
        latest = requests.get(base, timeout=10).json()
        num_atual = latest.get("numero", 0) or latest.get("numeroDoConcurso",0)
        freq = {i:0 for i in range(1, max_n+1)}; buscados = 0; draws=[]
        for i in range(num_atual, max(num_atual-80, 0), -1):
            try:
                r = requests.get(f"{base}/{i}", timeout=3)
                if r.status_code!= 200: continue
                d = r.json(); dezenas = d.get("listaDezenas") or d.get("dezenas") or []
                nums=[]
                for dz in dezenas:
                    try:
                        n=int(dz)
                        if 1 <= n <= max_n:
                            freq[n]+=1; nums.append(n)
                    except: pass
                if nums: draws.append(nums)
                buscados+=1
                if buscados>=80: break
            except: continue
        seen=set(); ciclo_atual=0
        for dr in draws:
            seen.update(dr); ciclo_atual+=1
            if len(seen)>=max_n: break
        ordenados = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        q_q=int(max_n*0.35); q_f=int(max_n*0.3)
        quentes=sorted([n for n,_ in ordenados[:q_q]]); frios=sorted([n for n,_ in ordenados[-q_f:]])
        neutros=sorted([n for n in range(1,max_n+1) if n not in quentes and n not in frios])
        resultado = {"q":quentes,"f":frios,"n":neutros,"fase":"REAL","h":f"{buscados} concursos","freq":freq,"atualizado":datetime.now().strftime("%H:%M"),"ciclo_atual":ciclo_atual}
        if loteria not in st.session_state.historico_ciclos: st.session_state.historico_ciclos[loteria] = []
        hist = st.session_state.historico_ciclos[loteria]
        if not hist or hist[-1]["ciclo_atual"]!= ciclo_atual:
            hist.append({"data": datetime.now().strftime("%d/%m %H:%M"), "ciclo_atual": ciclo_atual, "concurso": num_atual})
            st.session_state.historico_ciclos[loteria] = hist[-20:]
        return resultado
    except:
        max_n=configs[loteria]["max"]; quentes=sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
        resto=[x for x in range(1,max_n+1) if x not in quentes]; frios=sorted(random.sample(resto, int(max_n*0.3)))
        neutros=sorted([x for x in resto if x not in frios]); return {"q":quentes,"f":frios,"n":neutros,"fase":"OFFLINE","h":"Random","freq":{},"ciclo_atual":0}

def gerar(focus_pct, ciclo):
    qtd = cfg["qtd"]; nq = int(qtd * focus_pct / 100); jogo = []; dna = DNAS.get(lot, [])
    ca = ciclo.get("ciclo_atual",0); ideal = ciclos_ideais.get(lot,(0,0)); prioriza_frios = ca < ideal[0]*0.8 if ideal[0] else False
    dna_q = [d for d in dna if d in ciclo["q"]]; dna_f = [d for d in dna if d in ciclo["f"]]; dna_n = [d for d in dna if d not in ciclo["q"] and d not in ciclo["f"]]
    dna_prio = dna_f + dna_n + dna_q if prioriza_frios else dna_q + dna_n + dna_f
    for d in dna_prio:
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

def buscar_ao_vivo():
    try:
        resultados = []
        for nome, cfg_l in configs.items():
            try:
                base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{cfg_l['api']}"
                d = requests.get(base, timeout=5).json()
                acumulado = d.get("acumulado", False); prox = d.get("dataProximoConcurso",""); premio = d.get("valorEstimadoProximoConcurso",0)
                resultados.append({"Loteria":nome,"Concurso":d.get("numero",0),"Acumulou":"SIM" if acumulado else "NÃO","Prêmio_fmt":f"R$ {premio:,.2f}".replace(",","X").replace(".",",").replace("X","."),"Próximo Sorteio":prox,"acumulado_bool":acumulado})
            except: continue
        return resultados
    except: return []

st.markdown('<h1 class="main-title">🎯 LOTOELITE</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","⚙️ CONFIG","📚 HISTÓRICO","🔬 BACKTEST","💰 PREÇOS","📤 EXPORTAR","🔴 AO VIVO","🎯 ESPECIAIS"])
ciclo = buscar_ciclo_real(lot)

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
        st.markdown(f"**Focus:** {nivel}")
        st.markdown(f"**{focus}%**")

with tabs[1]:
    st.subheader("📊 Meus Jogos");
    if st.session_state.historico:
        for h in reversed(st.session_state.historico[-20:]):
            st.write(f"{h['data']} - {h['lot']}: {'-'.join(f'{n:02d}' for n in h['j'])} (Focus {h['f']}%)")
    else: st.info("Nenhum jogo gerado ainda")

with tabs[2]:
    st.subheader("🔄 Análise de Ciclo"); st.markdown(f'<div class="real-box"><b>FASE: {ciclo["fase"]}</b> | {ciclo["h"]} | Atualizado {ciclo["atualizado"]}</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in ciclo["q"]))
    with c2: st.markdown("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in ciclo["f"]))
    with c3: st.markdown("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in ciclo["n"][:10])+"...")
    st.markdown("---")
    hist = st.session_state.historico_ciclos.get(lot, []); valores = [h["ciclo_atual"] for h in hist]
    if len(valores) >= 2:
        ult = valores[-2:]; tendencia = "🚀 ACELERANDO" if ult[1] < ult[0] else "🐢 DESACELERANDO" if ult[1] > ult[0] else "➡️ ESTÁVEL"
        st.markdown(f"**Radar Velocidade:** {tendencia} | Histórico: {len(valores)} ciclos")
    else:
        st.markdown(f"**Radar Velocidade:** Coletando dados... ({len(valores)}/2)")
    if hist:
        media_hist = sum(valores)/len(valores); ca = ciclo.get("ciclo_atual",0); falta = int(media_hist - ca)
        if falta > 0: st.info(f"🔮 Previsão: faltam ~{falta} concurso(s) para virada (média {media_hist:.1f})")
        elif falta == 0: st.warning("🔮 Previsão: PONTO DE VIRADA AGORA")
        else: st.error(f"⚠️ Ciclo estendido! Atrasado em {abs(falta)} concurso(s)")

with tabs[3]:
    st.subheader("📈 Estatísticas");
    if ciclo["freq"]:
        df = pd.DataFrame([{"Dezena":k,"Freq":v} for k,v in ciclo["freq"].items()]).sort_values("Freq",ascending=False)
        st.dataframe(df.head(10), use_container_width=True)

with tabs[4]:
    st.subheader("🧠 IA Análise"); st.info(f"Focus {focus}% - {nivel}. Ciclo atual: {ciclo['ciclo_atual']}")

with tabs[5]:
    st.subheader("💡 Dicas"); st.write("• Use Focus 40% em início de ciclo • Focus 70% em final de ciclo")

with tabs[6]:
    st.subheader("🎯 DNA"); dna_lista = DNAS.get(lot,[]); st.write(", ".join(f"{n:02d}" for n in dna_lista))

with tabs[7]:
    st.subheader("⚙️ Config"); st.json({"Loteria":lot,"Focus":focus,"Ciclo":ciclo["ciclo_atual"]})

with tabs[8]:
    st.subheader("📚 Histórico Ciclos")
    hist = st.session_state.historico_ciclos.get(lot, [])
    if hist:
        dfh = pd.DataFrame(hist); st.dataframe(dfh, use_container_width=True)
    else: st.info("Sem histórico ainda")

with tabs[9]:
    st.subheader("🔬 Backtest")
    if st.button("Rodar Backtest (últimos 10)"):
        resultados = []
        try:
            base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{cfg['api']}"
            latest = requests.get(base, timeout=5).json(); num = latest.get("numero",0)
            for i in range(num, max(num-10,0), -1):
                r = requests.get(f"{base}/{i}", timeout=3)
                if r.status_code==200:
                    d = r.json(); dz = d.get("listaDezenas") or d.get("dezenas") or []; resultados.append({"dezenas":set(int(x) for x in dz)})
        except: pass
        if resultados:
            acertos = []
            for res in resultados:
                jogo = set(gerar(focus, ciclo)); acertos.append(len(jogo & res["dezenas"]))
            st.success(f"Média: {sum(acertos)/len(acertos):.2f} acertos | Melhor: {max(acertos)}")

with tabs[10]:
    st.subheader("💰 Preços")
    dfp=pd.DataFrame([{"Loteria":k,"Dezenas":f"{v['qtd']}/{v['max']}","Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()]); st.dataframe(dfp,use_container_width=True)

with tabs[11]:
    st.subheader("📤 Exportar")
    if st.session_state.historico:
        df=pd.DataFrame(st.session_state.historico); df["Jogo"]=df["j"].apply(lambda x:"-".join(f"{n:02d}" for n in x))
        csv=df[["data","lot","f","Jogo"]].to_csv(index=False).encode('utf-8'); st.download_button("📥 Baixar CSV",csv,"lotoelite.csv")

with tabs[12]:
    st.subheader("🔴 AO VIVO - Loterias Caixa")
    if st.button("🔄 Atualizar agora", type="primary"):
        with st.spinner("Buscando..."): st.session_state.ao_vivo = buscar_ao_vivo()
    if not st.session_state.ao_vivo: st.session_state.ao_vivo = buscar_ao_vivo()
    acumuladas = [x for x in st.session_state.ao_vivo if x["acumulado_bool"]]
    if acumuladas:
        st.markdown("### 🔥 ACUMULADAS")
        for a in acumuladas:
            st.markdown(f'<div class="acumulada"><b>{a["Loteria"]}</b> - Concurso {a["Concurso"]}<br>💰 {a["Prêmio_fmt"]}<br><b>{a["Acumulou"]}</b></div>', unsafe_allow_html=True)
    df_vivo = pd.DataFrame([{"Loteria":x["Loteria"],"Concurso":x["Concurso"],"Acumulou":x["Acumulou"],"Prêmio":x["Prêmio_fmt"]} for x in st.session_state.ao_vivo])
    st.dataframe(df_vivo, use_container_width=True, hide_index=True)

with tabs[13]:
    st.subheader("🎯 Hub Especiais")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🌽 Quina São João")
        if st.button("🎯 Gerar 3 jogos São João"):
            for i in range(3):
                jogo = sorted(random.sample(range(1,81),5)); st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
    with col2:
        st.markdown("### 🎆 Mega da Virada")
        if st.button("🎯 Gerar 3 jogos Virada"):
            for i in range(3):
                jogo = sorted(random.sample(range(1,61),6)); st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
