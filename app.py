import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")

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

ciclos_ideais = {
    "Lotofácil": (4,6),
    "Mega-Sena": (9,11),
    "Quina": (14,18),
    "Dupla Sena": (8,10),
    "Timemania": (12,15),
    "Lotomania": (8,12),
    "Dia de Sorte": (4,5),
    "Super Sete": (3,4),
    "+Milionária": (9,12),
}

configs = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50, "api":"lotofacil"},
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00, "api":"megasena"},
    "Quina": {"max":80,"qtd":5,"preco":3.00, "api":"quina"},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00, "api":"duplasena"},
    "Timemania": {"max":80,"qtd":10,"preco":3.50, "api":"timemania"},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00, "api":"lotomania"},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50, "api":"diadesorte"},
    "Super Sete": {"max":9,"qtd":7,"preco":3.00, "api":"supersete"},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00, "api":"maismilionaria"},
}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE")
    st.markdown('<div class="ia-box">🧠 v79g IA CICLO</div>', unsafe_allow_html=True)
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
                if r.status_code != 200: continue
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
        return {"q":quentes,"f":frios,"n":neutros,"fase":"REAL","h":f"{buscados} concursos","freq":freq,"atualizado":datetime.now().strftime("%H:%M"),"ciclo_atual":ciclo_atual}
    except:
        max_n=configs[loteria]["max"]; quentes=sorted(random.sample(range(1,max_n+1), int(max_n*0.35)))
        resto=[x for x in range(1,max_n+1) if x not in quentes]; frios=sorted(random.sample(resto, int(max_n*0.3)))
        neutros=sorted([x for x in resto if x not in frios]); return {"q":quentes,"f":frios,"n":neutros,"fase":"OFFLINE","h":"Random","freq":{},"ciclo_atual":0}

def gerar(focus_pct, ciclo):
    qtd=cfg["qtd"]; nq=int(qtd*focus_pct/100); jogo=[]
    if nq>0: jogo+=random.sample(ciclo["q"], min(nq, len(ciclo["q"])))
    pool=ciclo["f"]+ciclo["n"]
    if len(jogo)<qtd: jogo+=random.sample(pool, min(qtd-len(jogo), len(pool)))
    while len(jogo)<qtd:
        n=random.randint(1,cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

def buscar_ao_vivo():
    dados=[]
    for nome,conf in configs.items():
        try:
            url=f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{conf['api']}"
            d=requests.get(url, timeout=5).json()
            acumulado=d.get("acumulado", False)
            valor=d.get("valorEstimadoProximoConcurso",0) or 0
            data_prox=d.get("dataProximoConcurso","")
            concurso=d.get("numero") or d.get("numeroDoConcurso","")
            dados.append({
                "Loteria":nome,
                "Concurso":concurso,
                "Acumulou": "🔥 SIM" if acumulado else "Não",
                "Próximo Prêmio": valor,
                "Prêmio_fmt": f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X","."),
                "Próximo Sorteio": data_prox,
                "acumulado_bool": acumulado
            })
        except:
            dados.append({"Loteria":nome,"Concurso":"-","Acumulou":"Erro","Próximo Prêmio":0,"Prêmio_fmt":"-","Próximo Sorteio":"-","acumulado_bool":False})
    return sorted(dados, key=lambda x: x["Próximo Prêmio"], reverse=True)

st.markdown('<div class="main-title">LOTOELITE</div>', unsafe_allow_html=True)

tabs = st.tabs(["📊 CICLO","🤖 IA 3","🔒 FECHAMENTO","🔒 FECH 21","📍 POSIÇÃO","📈 GRÁFICO","🎲 BOLÕES","🏆 RESULTADOS","💾 MEUS JOGOS","🔍 CONFERIDOR","🧠 PERFIL","💰 PREÇOS","📥 EXPORTAR","🔴 AO VIVO","🎯 HUB ESPECIAIS"])

with tabs[0]:
    st.markdown('<div class="real-box"><b>🎯 Ciclo REAL da Caixa</b></div>', unsafe_allow_html=True)
    col1,col2=st.columns([1,3])
    with col1:
        if st.button("🔄 ATUALIZAR CICLO", type="primary", use_container_width=True):
            with st.spinner("Buscando..."): st.session_state.ciclos[lot]=buscar_ciclo_real(lot); st.rerun()
    if lot in st.session_state.ciclos:
        c=st.session_state.ciclos[lot]
        with col2: st.metric("Base",c["fase"],c["h"]); st.caption(f"Atualizado {c.get('atualizado','')}")
        ideal = ciclos_ideais.get(lot,(0,0)); ca = c.get("ciclo_atual",0)
        if ca>0 and ideal[1]>0:
            if ca < ideal[0]: status="🟢 Início"; dica="Priorize FRIOS"
            elif ca <= ideal[1]: status="🟡 Meio"; dica="Equilibre quentes/neutros"
            else: status="🔴 Fim"; dica="Priorize QUENTES"
            st.info(f"**Ciclo atual: {ca} concursos** | Ideal: {ideal[0]}-{ideal[1]} | {status} → {dica}")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown("**🔥 QUENTES**"); st.code(" ".join(f"{n:02d}" for n in c["q"]))
        with c2: st.markdown("**❄️ FRIOS**"); st.code(" ".join(f"{n:02d}" for n in c["f"]))
        with c3: st.markdown("**⚖️ NEUTROS**"); st.code(" ".join(f"{n:02d}" for n in c["n"][:14])+"...")

with tabs[1]:
    st.subheader("IA - 3 Sugestões")
    if lot not in st.session_state.ciclos: st.error("Atualize ciclo"); st.stop()
    ciclo=st.session_state.ciclos[lot]
    if st.button("🎯 Gerar 3 Jogos REAIS", type="primary"):
        # ajusta automaticamente pelo ciclo
        ca = ciclo.get("ciclo_atual",0)
        ideal = ciclos_ideais.get(lot,(0,0))
        if ca>0 and ideal[1]>0:
            if ca < ideal[0]:  # início - prioriza frios
                focos = [max(10,focus-20), max(10,focus-10), focus]
                modo = "Início de ciclo → mais frios"
            elif ca > ideal[1]:  # fim - prioriza quentes
                focos = [focus, min(95,focus+10), min(95,focus+20)]
                modo = "Fim de ciclo → mais quentes"
            else:  # meio
                focos = [max(10,focus-15), focus, min(95,focus+15)]
                modo = "Meio de ciclo → equilibrado"
        else:
            focos = [max(10,focus-15), focus, min(95,focus+15)]; modo = "Ciclo padrão"
        st.caption(f"IA ajustada: {modo}")
        novas=[]
        for f in focos:
            jogo=gerar(f,ciclo); nq=len(set(jogo)&set(ciclo["q"])); novas.append({"f":f,"j":jogo,"nq":nq})
        st.session_state.sugestoes_por_loteria[lot]=novas
    for i,s in enumerate(st.session_state.sugestoes_por_loteria.get(lot,[]),1):
        c1,c2=st.columns([5,1])
        with c1: st.code(f"S{i} F{s['f']}% ({s['nq']}Q): {'-'.join(f'{n:02d}' for n in s['j'])}")
        with c2:
            if st.button("💾",key=f"sv{i}"): st.session_state.historico.append({"lot":lot,"j":s["j"],"f":s["f"],"data":datetime.now().strftime("%d/%m %H:%M"),"ac":None,"p":cfg["preco"]})

with tabs[2]:
    st.subheader("Fechamento")
    if lot not in st.session_state.ciclos: st.error("Atualize ciclo"); st.stop()
    qtd=st.number_input("Quantos jogos?",1,500,20); st.info(f"R$ {qtd*cfg['preco']:.2f}")
    if st.button(f"Gerar {qtd}"):
        ciclo=st.session_state.ciclos[lot]; jogos=[gerar(focus,ciclo) for _ in range(qtd)]
        cols=st.columns(4)
        for i,j in enumerate(jogos[:40]):
            with cols[i%4]: st.text(f"{i+1:03d}: {'-'.join(f'{n:02d}' for n in j)}")

with tabs[3]:
    st.subheader("Fechamento 21")
    if lot=="Lotofácil":
        base=st.multiselect("21 dezenas", list(range(1,26)), list(range(1,22)), format_func=lambda x:f"{x:02d}")
        if st.button("Gerar 15 jogos") and len(base)==21:
            for i in range(15): st.code(f"{i+1}: {'-'.join(f'{n:02d}' for n in sorted(random.sample(base,15)))}")

with tabs[4]:
    st.subheader("📍 Análise por Posição")
    if lot not in st.session_state.ciclos: st.info("Atualize ciclo"); st.stop()
    c=st.session_state.ciclos[lot]; max_n=cfg["max"]; faixas=5; tamanho=max_n//faixas
    for i in range(faixas):
        ini=i*tamanho+1; fim=(i+1)*tamanho if i<faixas-1 else max_n; nums=list(range(ini,fim+1))
        q=len([n for n in nums if n in c["q"]]); f=len([n for n in nums if n in c["f"]])
        st.write(f"**{ini:02d}-{fim:02d}:** {q} quentes, {f} frios")

with tabs[5]:
    st.subheader("📈 Gráfico de Frequência")
    if lot not in st.session_state.ciclos or not st.session_state.ciclos[lot].get("freq"): st.info("Atualize ciclo"); st.stop()
    freq=st.session_state.ciclos[lot]["freq"]; df=pd.DataFrame(list(freq.items()), columns=["Dezena","Vezes"]).sort_values("Vezes",ascending=False)
    st.bar_chart(df.set_index("Dezena").head(20)); st.dataframe(df.head(15), use_container_width=True)

with tabs[6]:
    st.subheader("🎲 Bolões")
    if lot not in st.session_state.ciclos: st.info("Atualize ciclo"); st.stop()
    qtd_jogos=st.number_input("Jogos no bolão",5,100,10); cotas=st.number_input("Número de cotas",2,50,10)
    total=qtd_jogos*cfg["preco"]; st.metric("Valor total",f"R$ {total:.2f}",f"R$ {total/cotas:.2f} por cota")
    if st.button("Gerar jogos do bolão"):
        ciclo=st.session_state.ciclos[lot]; jogos=[gerar(focus,ciclo) for _ in range(qtd_jogos)]
        for i,j in enumerate(jogos,1): st.text(f"Jogo {i:02d}: {'-'.join(f'{n:02d}' for n in j)}")

with tabs[7]:
    st.subheader("🏆 Últimos Resultados")
    if st.button("Buscar da Caixa"):
        try:
            api=configs[lot]["api"]; d=requests.get(f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}", timeout=10).json()
            dezenas=d.get("listaDezenas") or d.get("dezenas") or []; st.success(f"Concurso {d.get('numero') or d.get('numeroDoConcurso')} - {d.get('dataApuracao')}")
            st.code(" - ".join(dezenas)); st.session_state.dados_caixa[lot]=d
        except: st.error("Erro API")

with tabs[8]:
    st.subheader("Meus Jogos")
    if st.session_state.historico:
        total=sum(h["p"] for h in st.session_state.historico); st.metric("Investido",f"R$ {total:.2f}",f"{len(st.session_state.historico)} jogos")
        for idx in range(len(st.session_state.historico)-1, max(-1,len(st.session_state.historico)-30), -1):
            h=st.session_state.historico[idx]; c1,c2=st.columns([5,1])
            with c1: st.text(f"{h['data']} {h['lot']} F{h['f']}%: {'-'.join(f'{n:02d}' for n in h['j'])}")
            with c2:
                if h.get("ac") is None:
                    if st.button("✓",key=f"ck{idx}"): v=st.number_input("ac",0,cfg["qtd"],key=f"ac{idx}",label_visibility="collapsed"); st.session_state.historico[idx]["ac"]=v; st.rerun()
                else: st.write(f"{h['ac']} ac")

with tabs[9]:
    st.subheader("🔍 Conferidor")
    jogo_txt=st.text_input("Digite seu jogo (ex: 02-04-06-10-11...)",key="conf")
    if st.button("Conferir com último resultado"):
        try:
            if lot not in st.session_state.dados_caixa:
                api=configs[lot]["api"]; d=requests.get(f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}", timeout=10).json()
            else: d=st.session_state.dados_caixa[lot]
            dezenas=[int(x) for x in (d.get("listaDezenas") or d.get("dezenas") or [])]; jogo=[int(x) for x in jogo_txt.replace(" ","").split("-") if x.isdigit()]
            acertos=len(set(jogo)&set(dezenas)); st.success(f"Você acertou {acertos} números!"); st.write(f"Resultado: {'-'.join(f'{n:02d}' for n in dezenas)}")
        except: st.error("Formato inválido")

with tabs[10]:
    st.subheader("🧠 Meu Perfil")
    hist=[h for h in st.session_state.historico if h["lot"]==lot]
    if hist:
        total=sum(h["p"] for h in hist); com_ac=[h for h in hist if h.get("ac") is not None]; media=sum(h["ac"] for h in com_ac)/len(com_ac) if com_ac else 0
        st.metric("Jogos",len(hist)); st.metric("Investido",f"R$ {total:.2f}"); st.metric("Média acertos",f"{media:.1f}")
        df=pd.DataFrame([{"Focus":h["f"],"Acertos":h.get("ac",0)} for h in com_ac])
        if not df.empty: st.bar_chart(df.groupby("Focus").mean())
    else: st.info("Jogue e registre acertos")

with tabs[11]:
    st.subheader("💰 Preços")
    dfp=pd.DataFrame([{"Loteria":k,"Dezenas":f"{v['qtd']}/{v['max']}","Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()]); st.dataframe(dfp,use_container_width=True)

with tabs[12]:
    st.subheader("Exportar")
    if st.session_state.historico:
        df=pd.DataFrame(st.session_state.historico); df["Jogo"]=df["j"].apply(lambda x:"-".join(f"{n:02d}" for n in x))
        csv=df[["data","lot","f","p","Jogo"]].to_csv(index=False).encode('utf-8'); st.download_button("📥 Baixar CSV",csv,"lotoelite_completo.csv")

with tabs[13]:
    st.subheader("🔴 AO VIVO - Loterias Caixa")
    st.caption("Dados oficiais em tempo real direto da Caixa.")
    if st.button("🔄 Atualizar agora", type="primary"):
        with st.spinner("Buscando..."): st.session_state.ao_vivo = buscar_ao_vivo()
    if not st.session_state.ao_vivo: st.session_state.ao_vivo = buscar_ao_vivo()
    
    acumuladas = [x for x in st.session_state.ao_vivo if x["acumulado_bool"]]
    if acumuladas:
        st.markdown("### 🔥 ACUMULADAS")
        for a in acumuladas:
            st.markdown(f'<div class="acumulada"><b>{a["Loteria"]}</b> - Concurso {a["Concurso"]}<br>💰 {a["Prêmio_fmt"]} - Próximo: {a["Próximo Sorteio"]}<br><b>{a["Acumulou"]}</b></div>', unsafe_allow_html=True)
    
    st.markdown("### 📅 Todas as loterias")
    df_vivo = pd.DataFrame([{"Loteria":x["Loteria"],"Concurso":x["Concurso"],"Acumulou":x["Acumulou"],"Próximo Prêmio":x["Prêmio_fmt"],"Sorteio":x["Próximo Sorteio"]} for x in st.session_state.ao_vivo])
    st.dataframe(df_vivo, use_container_width=True, hide_index=True)
    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m %H:%M')}")

with tabs[14]:
    st.subheader("🎯 Hub Especiais - Loterias Sazonais")
    st.caption("São João, Mega da Virada, Lotofácil Independência e Dupla de Páscoa com histórico real")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌽 Quina São João")
        st.markdown('<div class="real-box"><b>15 edições (2011-2025)</b><br>Prêmio médio: R$ 120 milhões</div>', unsafe_allow_html=True)
        if st.button("📊 Ver histórico São João"):
            st.code("2025: 12-19-20-34-35\n2024: 21-38-60-64-70\n2023: 12-13-45-47-70\n2022: 07-23-30-62-76\n2021: 15-30-32-37-62")
            st.info("💡 33 números NUNCA saíram (41% de brecha)")
        
        if st.button("🎯 Gerar 3 jogos São João", type="primary"):
            # usa ciclo de 3 anos da Quina
            try:
                ciclo_sj = buscar_ciclo_real("Quina")
                for i in range(3):
                    jogo = gerar(40, ciclo_sj)[:5]  # Quina = 5 números
                    st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in sorted(jogo))}")
            except:
                for i in range(3):
                    jogo = sorted(random.sample(range(1,81),5))
                    st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
    
    with col2:
        st.markdown("### 🎆 Mega da Virada")
        st.markdown('<div class="real-box"><b>17 edições (2008-2024)</b><br>Prêmio 2024: R$ 635 milhões</div>', unsafe_allow_html=True)
        if st.button("📊 Ver histórico Mega Virada"):
            st.code("2024: 01-17-19-29-50-57\n2023: 21-24-33-41-48-56\n2022: 04-05-10-34-58-59")
            st.info("💡 Número 10 saiu 5 vezes (mais frequente)")
        
        if st.button("🎯 Gerar 3 jogos Virada", type="primary"):
            try:
                ciclo_mv = buscar_ciclo_real("Mega-Sena")
                for i in range(3):
                    jogo = gerar(60, ciclo_mv)[:6]
                    st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in sorted(jogo))}")
            except:
                for i in range(3):
                    jogo = sorted(random.sample(range(1,61),6))
                    st.success(f"Jogo {i+1}: {'-'.join(f'{n:02d}' for n in jogo)}")
    
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 🇧🇷 Lotofácil Independência")
        st.info("12 edições - Setembro")
        if st.button("Gerar Independência"):
            jogo = sorted(random.sample(range(1,26),15))
            st.success(f"{'-'.join(f'{n:02d}' for n in jogo)}")
    
    with col4:
        st.markdown("### 🐰 Dupla de Páscoa")
        st.info("Sempre em abril")
        if st.button("Gerar Páscoa"):
            jogo = sorted(random.sample(range(1,51),6))
            st.success(f"{'-'.join(f'{n:02d}' for n in jogo)}")
