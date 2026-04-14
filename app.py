import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import io

st.set_page_config(page_title="LOTOELITE", layout="wide", page_icon="🎯")

st.markdown('''
<style>
.main-title {color:#d32f2f; font-size:2.6rem; font-weight:800; text-align:center;}
.focus-box {background:#e8f5e9; padding:12px; border-radius:8px; border-left:5px solid #2e7d32;}
.perfil-card {background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:20px; border-radius:12px;}
.historico-item {background:#f5f5f5; padding:10px; margin:5px 0; border-radius:8px; border-left:4px solid #1976d2;}
.acerto-11 {border-left-color:#4caf50; background:#e8f5e9;}
.acerto-12 {border-left-color:#ff9800; background:#fff3e0;}
.acerto-13 {border-left-color:#f44336; background:#ffebee;}
.acerto-14 {border-left-color:#9c27b0; background:#f3e5f5;}
.acerto-15 {border-left-color:#ffd700; background:#fffde7;}
</style>
''', unsafe_allow_html=True)

if 'historico_jogos' not in st.session_state:
    st.session_state.historico_jogos = []
if 'perfil_aprendido' not in st.session_state:
    st.session_state.perfil_aprendido = {"focus_medio": 40, "acertos_medio": 0, "total_jogos": 0, "melhor_focus": 40}
if 'ciclos' not in st.session_state:
    st.session_state.ciclos = {}
if 'sugestoes_atuais' not in st.session_state:
    st.session_state.sugestoes_atuais = []

configs = {
    "Mega-Sena": {"max":60,"qtd":6,"preco":6.00},
    "Lotofácil": {"max":25,"qtd":15,"preco":3.50},
    "Quina": {"max":80,"qtd":5,"preco":3.00},
    "Lotomania": {"max":100,"qtd":50,"preco":3.00},
    "Dupla Sena": {"max":50,"qtd":6,"preco":3.00},
    "Timemania": {"max":80,"qtd":10,"preco":3.50},
    "Dia de Sorte": {"max":31,"qtd":7,"preco":2.50},
    "Super Sete": {"max":9,"qtd":7,"preco":3.00},
    "+Milionária": {"max":50,"qtd":6,"preco":6.00},
    "Loteca": {"max":14,"qtd":14,"preco":4.00},
}

with st.sidebar:
    st.markdown("### 🎯 LOTOELITE")
    loteria = st.selectbox("Loteria", list(configs.keys()), index=1)
    focus = st.slider("Focus", 0, 100, st.session_state.perfil_aprendido["focus_medio"], 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel} ({focus}%)</b></div>', unsafe_allow_html=True)

cfg = configs[loteria]

def gerar_jogo():
    return sorted(random.sample(range(1, cfg["max"]+1), cfg["qtd"]))

st.markdown('<div class="main-title">🎯 LOTOELITE</div>', unsafe_allow_html=True)
st.caption(f"{loteria} • R$ {cfg['preco']:.2f} • {len(st.session_state.historico_jogos)} jogos salvos")

tabs = st.tabs(["🧠 Perfil","📊 Gráfico","💰 Preços","📊 Ciclo","📍 Posição","🤖 IA 3","🔒 Fechamento","🔒 Fech 21","🎲 Bolões","🏆 Resultados","💾 Meus Jogos","🔍 Conferidor","📥 Exportar"])

with tabs[0]:
    c1,c2 = st.columns(2)
    with c1:
        html = '<div class="perfil-card"><h3>IA Aprendeu</h3>'
        html += f"<p>Jogos: {st.session_state.perfil_aprendido['total_jogos']}</p>"
        html += f"<p>Média: {st.session_state.perfil_aprendido['acertos_medio']:.1f}</p>"
        html += f"<p>Melhor Focus: {st.session_state.perfil_aprendido['melhor_focus']}%</p></div>"
        st.markdown(html, unsafe_allow_html=True)
    with c2:
        df_l = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
        if len(df_l)>=3:
            df = pd.DataFrame(df_l)
            st.bar_chart(df.groupby('focus')['acertos'].mean())

with tabs[1]:
    df_l = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
    if len(df_l)>=2:
        df = pd.DataFrame(df_l)
        st.line_chart(df['acertos'])
    else:
        st.info("Salve jogos com acertos")

with tabs[2]:
    dfp = pd.DataFrame([{"Loteria":k, "Preço":f"R$ {v['preco']:.2f}"} for k,v in configs.items()])
    st.dataframe(dfp, hide_index=True, use_container_width=True)

with tabs[3]:
    if st.button("ANALISAR CICLO"):
        st.session_state.ciclos[loteria] = random.sample(range(1,cfg["max"]+1), min(18,cfg["max"]))
    if loteria in st.session_state.ciclos:
        st.code(" - ".join(f"{n:02d}" for n in sorted(st.session_state.ciclos[loteria])))

with tabs[4]:
    dados = [{"Loteria":n, "Fase":random.choice(["Início","Meio","Fim","Virada"])} for n in configs]
    st.dataframe(pd.DataFrame(dados), hide_index=True)

with tabs[5]:
    if st.button("Gerar 3 Sugestões", type="primary"):
        st.session_state.sugestoes_atuais = [{"focus":f,"jogo":gerar_jogo()} for f in [max(10,focus-20),focus,min(95,focus+20)]]
    for i,s in enumerate(st.session_state.sugestoes_atuais,1):
        c1,c2 = st.columns([5,1])
        with c1: st.code(f"S{i} F{s['focus']}%: {' - '.join(f'{n:02d}' for n in s['jogo'])}")
        with c2:
            if st.button("💾", key=f"s{i}"):
                st.session_state.historico_jogos.append({"data":datetime.now().strftime("%d/%m %H:%M"),"jogo":s["jogo"],"focus":s["focus"],"loteria":loteria,"acertos":None,"preco":cfg["preco"]})
                st.success("Salvo")

with tabs[6]:
    if st.button("Gerar 5 Fechamentos"):
        for i in range(5):
            st.code(f"F{i+1}: {' - '.join(f'{n:02d}' for n in gerar_jogo())}")

with tabs[7]:
    if loteria=="Lotofácil":
        base = st.multiselect("21 números", list(range(1,26)), list(range(1,22)), format_func=lambda x:f"{x:02d}")
        qtd = st.slider("Jogos",5,30,10)
        if st.button("Gerar Fech 21") and len(base)==21:
            for i in range(qtd):
                j = sorted(random.sample(base,15))
                st.code(f"J{i+1}: {' - '.join(f'{n:02d}' for n in j)}")
            st.success(f"Total R$ {qtd*3.5:.2f}")
    else:
        st.info("Use Lotofácil")

with tabs[8]:
    jogos = st.number_input("Jogos",5,50,15)
    cotas = st.number_input("Cotas",2,20,10)
    if st.button("Criar Bolão"):
        total = jogos*cfg["preco"]
        st.info(f"{jogos} jogos = R$ {total:.2f} | {cotas} cotas de R$ {total/cotas:.2f}")
        for i in range(3):
            st.code(f"{i+1}: {' - '.join(f'{n:02d}' for n in gerar_jogo())}")

with tabs[9]:
    res = {"Lotofácil":[3,5,8,10,11,13,14,17,18,19,21,22,23,24,25],"Mega":[7,18,23,34,45,56],"Quina":[2,3,24,29,77]}
    for k,v in res.items():
        st.code(f"{k}: {' - '.join(f'{n:02d}' for n in v)}")

with tabs[10]:
    total = sum(j.get('preco',0) for j in st.session_state.historico_jogos)
    st.metric("Investido", f"R$ {total:.2f}")
    for idx in range(len(st.session_state.historico_jogos)-1, -1, -1):
        jg = st.session_state.historico_jogos[idx]
        ac = jg.get('acertos')
        c1,c2 = st.columns([4,1])
        with c1:
            cls = f"acerto-{ac}" if ac and ac>=11 else ""
            st.markdown(f'<div class="historico-item {cls}">J{idx+1} {jg["loteria"]}: {" - ".join(f"{n:02d}" for n in jg["jogo"])} F{jg["focus"]}%</div>', unsafe_allow_html=True)
        with c2:
            if ac is None:
                v = st.number_input("ac",0,25,key=f"a{idx}",label_visibility="collapsed")
                if st.button("ok",key=f"o{idx}"):
                    st.session_state.historico_jogos[idx]['acertos']=v
                    com=[j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
                    if com:
                        df=pd.DataFrame(com)
                        melhor=int(df.groupby('focus')['acertos'].mean().idxmax())
                        st.session_state.perfil_aprendido={"acertos_medio":float(df['acertos'].mean()),"focus_medio":int(df['focus'].mean()),"total_jogos":len(com),"melhor_focus":melhor}
                    st.rerun()
            else:
                st.write(f"{ac} ac")

with tabs[11]:
    j = st.text_input("Seu jogo")
    r = st.text_input("Resultado")
    if st.button("Conferir"):
        nj=[int(x) for x in j.split() if x.isdigit()]
        nr=[int(x) for x in r.split() if x.isdigit()]
        ac=len(set(nj)&set(nr))
        st.metric("Acertos",ac)
        st.session_state.historico_jogos.append({"data":datetime.now().strftime("%d/%m %H:%M"),"jogo":nj,"focus":focus,"loteria":loteria,"acertos":ac,"preco":cfg["preco"]})

with tabs[12]:
    if st.session_state.historico_jogos:
        df=pd.DataFrame(st.session_state.historico_jogos)
        df['Jogo']=df['jogo'].apply(lambda x:' - '.join(f"{n:02d}" for n in x))
        out=io.BytesIO()
        with pd.ExcelWriter(out,engine='openpyxl') as w:
            df[['data','loteria','preco','focus','acertos','Jogo']].to_excel(w,index=False)
        st.download_button("Baixar Excel",out.getvalue(),"lotoelite.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Sem jogos")
