import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

st.set_page_config(page_title="LOTOELITE v86.2", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:3.5rem; font-weight:900; text-align:center; letter-spacing:2px;}
.status-box {padding:6px 10px; border-radius:6px; font-size:0.85em; margin-bottom:10px;}
.online {background:#e8f5e9; border-left:4px solid #2e7d32;}
.offline {background:#fff3e0; border-left:4px solid #f57c00;}
.acumulada {background:#ffebee; padding:12px; border-radius:8px; border-left:5px solid #d32f2f; margin:8px 0;}
</style>
""", unsafe_allow_html=True)

if 'historico' not in st.session_state: st.session_state.historico = []
if 'historico_ciclos' not in st.session_state: st.session_state.historico_ciclos = {}
if 'qtd_fechamento' not in st.session_state: st.session_state.qtd_fechamento = 21

configs = {
    "Lotofácil":{"max":25,"qtd":15,"preco":3.50},
    "Mega-Sena":{"max":60,"qtd":6,"preco":6.00},
    "Quina":{"max":80,"qtd":5,"preco":3.00},
    "Dupla Sena":{"max":50,"qtd":6,"preco":3.00},
    "Timemania":{"max":80,"qtd":10,"preco":3.50},
    "Lotomania":{"max":100,"qtd":50,"preco":3.00},
    "Dia de Sorte":{"max":31,"qtd":7,"preco":2.50},
    "Super Sete":{"max":9,"qtd":7,"preco":3.00},
    "+Milionária":{"max":50,"qtd":6,"preco":6.00}
}
DNAS = {"Lotofácil":[4,6,10,14,17,19,20,24,25],"Mega-Sena":[14,32,37,39,42],"Quina":[4,10,14,19,20,25,32,37],"Dupla Sena":[14,19,25,32,37,42]}

API_MAP = {"Lotofácil":"lotofacil","Mega-Sena":"megasena","Quina":"quina","Dupla Sena":"duplasena","Timemania":"timemania","Lotomania":"lotomania","Dia de Sorte":"diadesorte","Super Sete":"supersete","+Milionária":"maismilionaria"}

def buscar_dados_reais(loteria):
    try:
        api = API_MAP[loteria]
        base = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}"
        latest = requests.get(base, timeout=7).json()
        max_n = configs[loteria]["max"]
        freq = {i:0 for i in range(1,max_n+1)}
        atrasos = {i:0 for i in range(1,max_n+1)}
        draws = []
        num_atual = latest.get("numero",0)
        for i in range(num_atual, max(num_atual-60,0), -1):
            try:
                r = requests.get(f"{base}/{i}", timeout=4)
                if r.status_code!=200: continue
                d = r.json()
                dezenas = [int(x) for x in (d.get("listaDezenas") or []) if str(x).isdigit() and 1<=int(x)<=max_n]
                draws.append({"concurso":i,"dezenas":dezenas,"data":d.get("dataApuracao")})
                for n in dezenas: freq[n]+=1
            except: pass
        
        for n in range(1,max_n+1):
            atraso=0
            for draw in draws:
                if n in draw["dezenas"]: break
                atraso+=1
            atrasos[n]=atraso
        
        seen=set(); ciclo=0
        for d in draws:
            seen.update(d["dezenas"]); ciclo+=1
            if len(seen)>=max_n: break
        
        ordenados = sorted(freq.items(), key=lambda x:x[1], reverse=True)
        quentes = [n for n,_ in ordenados[:int(max_n*0.35)]]
        frios = [n for n,_ in ordenados[-int(max_n*0.3):]]
        neutros = [n for n in range(1,max_n+1) if n not in quentes and n not in frios]
        
        return {"status":"online","latest":latest,"draws":draws,"freq":freq,"atrasos":atrasos,"q":quentes,"f":frios,"n":neutros,"ciclo":ciclo}
    except:
        return {"status":"offline"}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE v86.2")
    lot = st.selectbox("Loteria", list(configs.keys()))
    focus = st.slider("Focus %", 0, 100, 40, 5)
    dados = buscar_dados_reais(lot)
    if dados["status"]=="online":
        st.markdown('<div class="status-box online">🟢 ONLINE - Caixa conectada</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box offline">🟡 OFFLINE - usando backup</div>', unsafe_allow_html=True)

cfg = configs[lot]

def gerar_jogo():
    qtd=cfg["qtd"]; jogo=[]; dna=DNAS.get(lot,[])
    nq = int(qtd * focus / 100)
    for d in dna[:nq]:
        if d<=cfg["max"] and d not in jogo: jogo.append(d)
    pool = dados.get("q", list(range(1,cfg["max"]+1))) if focus>50 else list(range(1,cfg["max"]+1))
    random.shuffle(pool)
    for n in pool:
        if len(jogo)>=qtd: break
        if n not in jogo: jogo.append(n)
    while len(jogo)<qtd:
        n=random.randint(1,cfg["max"])
        if n not in jogo: jogo.append(n)
    return sorted(jogo[:qtd])

st.markdown('<h1 class="main-title">🎯 LOTOELITE</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🎲 GERADOR","📊 MEUS JOGOS","🔄 CICLO","📈 ESTATÍSTICAS","🧠 IA","💡 DICAS","🎯 DNA","⚙️ CONFIG","📚 HISTÓRICO","🔬 BACKTEST","💰 PREÇOS","📤 EXPORTAR","🔴 AO VIVO","🎯 ESPECIAIS","🔢 FECHAMENTO"])

with tabs[0]:
    col1,col2 = st.columns([2,1])
    with col1:
        if st.button("🎲 GERAR 3 JOGOS", type="primary", use_container_width=True):
            for i in range(3):
                jogo = gerar_jogo()
                st.session_state.historico.append({"data":datetime.now().strftime("%d/%m %H:%M"),"lot":lot,"j":jogo,"f":focus})
                st.success(f"**JOGO {i+1}:** {' - '.join(f'{n:02d}' for n in jogo)}")
    with col2:
        if dados["status"]=="online":
            st.metric("Último concurso", dados["latest"].get("numero","-"))
            st.metric("Ciclo atual", f"{dados['ciclo']} conc.")

with tabs[1]:
    st.subheader("Meus Jogos")
    if st.session_state.historico:
        for h in reversed(st.session_state.historico[-20:]):
            st.write(f"{h['data']} - {h['lot']}: {'-'.join(f'{n:02d}' for n in h['j'])}")

with tabs[2]:
    st.subheader("Análise de Ciclo - RESTAURADO")
    if dados["status"]=="online":
        df_ciclo = pd.DataFrame([{"Concurso":d["concurso"],"Qtd Dezenas":len(d["dezenas"])} for d in dados["draws"][:12]])
        st.bar_chart(df_ciclo.set_index("Concurso"))
        fase = "Início" if dados["ciclo"]<=4 else "Meio" if dados["ciclo"]<=8 else "Fim"
        st.info(f"**Fase do ciclo: {fase}** ({dados['ciclo']} concursos sem fechar)")
        c1,c2,c3 = st.columns(3)
        with c1: st.write("**🔥 QUENTES**"); st.write(", ".join(f"{n:02d}" for n in sorted(dados["q"])[:15]))
        with c2: st.write("**❄️ FRIOS**"); st.write(", ".join(f"{n:02d}" for n in sorted(dados["f"])[:15]))
        with c3: st.write("**➖ NEUTROS**"); st.write(", ".join(f"{n:02d}" for n in sorted(dados["n"])[:15]))
    else:
        st.warning("Sem conexão - usando dados simulados")

with tabs[3]:
    st.subheader("Estatísticas Completas - RESTAURADO")
    if dados["status"]=="online":
        freq = dados["freq"]; atrasos = dados["atrasos"]
        df_stats = pd.DataFrame([{"Dezena":n,"Frequência":freq[n],"Atraso":atrasos[n],"Par":"Sim" if n%2==0 else "Não"} for n in range(1,cfg["max"]+1)])
        df_stats = df_stats.sort_values("Frequência", ascending=False)
        st.dataframe(df_stats.head(20), use_container_width=True, hide_index=True)
        col1,col2 = st.columns(2)
        with col1: st.metric("Mais frequente", f"{df_stats.iloc[0]['Dezena']:02d}", f"{df_stats.iloc[0]['Frequência']}x")
        with col2: st.metric("Mais atrasada", f"{df_stats.sort_values('Atraso',ascending=False).iloc[0]['Dezena']:02d}", f"{df_stats['Atraso'].max()} conc.")
    else:
        st.info("Conecte para ver estatísticas reais")

with tabs[4]:
    st.subheader("IA")
    if st.button("Gerar 3 estratégias"):
        for nome,pct in [("Conservador",30),("Equilibrado",50),("Agressivo",75)]:
            jogo=gerar_jogo(); st.success(f"{nome}: {' - '.join(f'{n:02d}' for n in jogo)}")

with tabs[5]:
    st.subheader("Dicas por Fase - RESTAURADO")
    fase = dados.get("ciclo",5)
    if fase<=4: st.success("**INÍCIO DE CICLO**: Use Focus 25-35%, priorize frios")
    elif fase<=8: st.info("**MEIO DE CICLO**: Use Focus 40-55%, equilibrado")
    else: st.warning("**FIM DE CICLO**: Use Focus 70-85%, priorize quentes")

with tabs[6]:
    st.subheader("DNA"); st.write(", ".join(f"{n:02d}" for n in DNAS.get(lot,[])))

with tabs[7]:
    st.subheader("Config"); st.json({"Loteria":lot,"Focus":focus})

with tabs[8]:
    st.subheader("Histórico de Ciclos - RESTAURADO")
    st.session_state.historico_ciclos[lot] = dados.get("ciclo",0)
    st.write(st.session_state.historico_ciclos)

with tabs[9]:
    st.subheader("Backtest Real - RESTAURADO")
    if dados["status"]=="online" and st.session_state.historico:
        ultimo_jogo = st.session_state.historico[-1]["j"]
        resultados=[]
        for d in dados["draws"][:10]:
            acertos = len(set(ultimo_jogo) & set(d["dezenas"]))
            resultados.append({"Concurso":d["concurso"],"Acertos":acertos})
        st.dataframe(pd.DataFrame(resultados), hide_index=True)
    else:
        st.info("Gere um jogo e conecte para backtest")

with tabs[10]:
    st.subheader("Preços Múltiplos - RESTAURADO")
    if lot=="Lotofácil":
        tabela=[{"Dezenas":15,"Preço":"R$ 3,50"},{"Dezenas":16,"Preço":"R$ 56,00"},{"Dezenas":17,"Preço":"R$ 408,00"},{"Dezenas":18,"Preço":"R$ 2.448,00"},{"Dezenas":19,"Preço":"R$ 11.628,00"},{"Dezenas":20,"Preço":"R$ 46.512,00"}]
        st.dataframe(pd.DataFrame(tabela), hide_index=True)
    else:
        st.dataframe(pd.DataFrame([{"Loteria":k,"Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()]), hide_index=True)

with tabs[11]:
    st.subheader("Exportar"); st.download_button("CSV", pd.DataFrame(st.session_state.historico).to_csv(index=False).encode(),"jogos.csv")

with tabs[12]:
    st.subheader("AO VIVO Automático - RESTAURADO")
    # Tenta buscar real, senão usa backup do usuário
    backup = {
        "Mega-Sena":{"numero":2998,"valor":60000000},
        "Quina":{"numero":7004,"valor":20000000},
        "+Milionária":{"numero":347,"valor":36000000}
    }
    loterias_vivo = ["Mega-Sena","Quina","Lotofácil","+Milionária"]
    dados_vivo=[]
    for l in loterias_vivo:
        try:
            api = API_MAP[l]; r=requests.get(f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}", timeout=5).json()
            acumulado = r.get("acumulado",True); premio = r.get("valorEstimadoProximoConcurso",0)
            dados_vivo.append({"Loteria":l,"Concurso":r.get("numero"),"Acumulou":"SIM" if acumulado else "NÃO","Prêmio":f"R$ {premio:,.2f}".replace(",","X").replace(".",",").replace("X",".")})
        except:
            b=backup.get(l,{"numero":0,"valor":0}); dados_vivo.append({"Loteria":l,"Concurso":b["numero"],"Acumulou":"SIM","Prêmio":f"R$ {b['valor']:,.2f}".replace(",","X").replace(".",",").replace("X",".")})
    
    for item in dados_vivo:
        if item["Acumulou"]=="SIM":
            st.markdown(f'<div class="acumulada"><b>🔥 {item["Loteria"]}</b> - Concurso {item["Concurso"]}<br>💰 {item["Prêmio"]}</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(dados_vivo), hide_index=True, use_container_width=True)

with tabs[13]:
    st.subheader("Especiais"); 
    if st.button("Mega da Virada"): st.success(' - '.join(f'{n:02d}' for n in sorted(random.sample(range(1,61),6))))

with tabs[14]:
    st.subheader("Fechamento")
    if st.button("➕"): st.session_state.qtd_fechamento+=1
    if st.button("➖"): st.session_state.qtd_fechamento=max(1,st.session_state.qtd_fechamento-1)
    st.write(f"{st.session_state.qtd_fechamento} jogos")
    if st.button("GERAR"):
        for i in range(st.session_state.qtd_fechamento):
            st.text(f"{i+1:02d}: {' - '.join(f'{n:02d}' for n in gerar_jogo())}")
