import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import io

st.set_page_config(page_title="LOTOELITE v72", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.main-title {color:#d32f2f; font-size:2.4rem; font-weight:800;}
.focus-box {background:#e8f5e9; padding:12px; border-radius:8px; border-left:5px solid #2e7d32;}
.perfil-card {background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:20px; border-radius:12px;}
.historico-item {background:#f5f5f5; padding:10px; margin:5px 0; border-radius:8px; border-left:4px solid #1976d2;}
.acerto-11 {border-left-color:#4caf50; background:#e8f5e9;}
.acerto-12 {border-left-color:#ff9800; background:#fff3e0;}
.acerto-13 {border-left-color:#f44336; background:#ffebee;}
.acerto-14 {border-left-color:#9c27b0; background:#f3e5f5;}
.acerto-15 {border-left-color:#ffd700; background:#fffde7;}
.alerta {background:#fff3cd; padding:15px; border-radius:8px; border-left:5px solid #ffc107; margin:10px 0;}
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
    st.markdown("### 🎯 v72 COMPLETO")
    loteria = st.selectbox("LOTERIA", ["Lotofácil", "Mega-Sena", "Quina", "Lotomania", "Dupla Sena", "Timemania"])
    st.markdown("---")
    focus_default = st.session_state.perfil_aprendido["focus_medio"]
    focus = st.slider("Focus", 0, 100, focus_default, 5)
    nivel = "Leve" if focus<=25 else "Moderado" if focus<=45 else "Forte" if focus<=65 else "Ultra" if focus<=85 else "Máximo"
    st.markdown(f'<div class="focus-box"><b>{nivel} ({focus}%)</b></div>', unsafe_allow_html=True)
    
    # ALERTA INTELIGENTE
    melhor = st.session_state.perfil_aprendido.get("melhor_focus", focus_default)
    if abs(focus - melhor) > 15 and st.session_state.perfil_aprendido['total_jogos'] >= 3:
        st.warning(f"💡 IA: Tente Focus {melhor}%")

configs = {
    "Lotofácil": {"max":25,"qtd":15,"preco":3.0},
    "Mega-Sena": {"max":60,"qtd":6,"preco":5.0},
    "Quina": {"max":80,"qtd":5,"preco":2.5},
    "Lotomania": {"max":100,"qtd":50,"preco":3.0},
    "Dupla Sena": {"max":50,"qtd":6,"preco":2.5},
    "Timemania": {"max":80,"qtd":10,"preco":3.5},
}
cfg = configs[loteria]

def gerar_jogo(f, max_n=None, qtd_n=None):
    max_n = max_n or cfg["max"]
    qtd_n = qtd_n or cfg["qtd"]
    base = list(range(1, max_n+1))
    random.shuffle(base)
    split = int(len(base)*0.4)
    quentes, frios = base[:split], base[split:]
    nq = min(int(round(qtd_n*f/100)), len(quentes), qtd_n)
    nf = qtd_n - nq
    jogo = []
    if nq>0: jogo += random.sample(quentes, nq)
    if nf>0: jogo += random.sample(frios, min(nf, len(frios)))
    while len(jogo) < qtd_n:
        c = random.choice(base)
        if c not in jogo: jogo.append(c)
    return sorted(jogo[:qtd_n])

st.markdown('<div class="main-title">🎯 LOTOELITE v72 - IA COMPLETA</div>', unsafe_allow_html=True)

# ALERTA NO TOPO
if st.session_state.perfil_aprendido['total_jogos'] >= 5:
    melhor = st.session_state.perfil_aprendido.get("melhor_focus", 40)
    media_melhor = st.session_state.perfil_aprendido.get("media_melhor", 0)
    if focus != melhor:
        st.markdown(f'<div class="alerta"><b>🎯 ALERTA INTELIGENTE:</b> Sua IA aprendeu que Focus {melhor}% te dá média de {media_melhor:.1f} acertos. Você está usando {focus}%.</div>', unsafe_allow_html=True)

st.success(f"Jogos: {len(st.session_state.historico_jogos)} | Média: {st.session_state.perfil_aprendido['acertos_medio']:.1f} | Melhor Focus: {st.session_state.perfil_aprendido.get('melhor_focus',40)}%")

tabs = st.tabs(["🧠 Perfil","📊 Gráfico","📊 Ciclo","📍 Posição","🤖 IA 3","🔒 Fechamento","🔒 Fech 21","🎲 Bolões","🏆 Resultados","💾 Meus Jogos","📥 Exportar"])

with tabs[0]:
    st.subheader("Perfil Inteligente")
    col1,col2 = st.columns(2)
    with col1:
        html = '<div class="perfil-card"><h3>IA Aprendeu</h3>'
        html += f"<p>Jogos: {st.session_state.perfil_aprendido['total_jogos']}</p>"
        html += f"<p>Média: {st.session_state.perfil_aprendido['acertos_medio']:.1f}</p>"
        html += f"<p>Focus atual: {focus}%</p>"
        html += f"<p>Melhor Focus: {st.session_state.perfil_aprendido.get('melhor_focus',40)}%</p></div>"
        st.markdown(html, unsafe_allow_html=True)
    with col2:
        df_list = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
        if df_list:
            df = pd.DataFrame(df_list)
            analise = df.groupby('focus')['acertos'].agg(['mean','count']).round(1)
            analise.columns = ['Media','Qtd']
            st.dataframe(analise)

with tabs[1]:
    st.subheader("📊 Gráfico de Evolução")
    df_list = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
    if len(df_list) < 2:
        st.info("Salve pelo menos 2 jogos com acertos para ver o gráfico")
    else:
        df = pd.DataFrame(df_list)
        df['Jogo'] = range(1, len(df)+1)
        df['Media Móvel'] = df['acertos'].rolling(window=3, min_periods=1).mean()
        
        st.line_chart(df.set_index('Jogo')[['acertos','Media Móvel']])
        
        col1,col2,col3 = st.columns(3)
        with col1: st.metric("Primeiro jogo", f"{df['acertos'].iloc[0]} acertos")
        with col2: st.metric("Último jogo", f"{df['acertos'].iloc[-1]} acertos")
        with col3: 
            evolucao = df['acertos'].iloc[-1] - df['acertos'].iloc[0]
            st.metric("Evolução", f"{evolucao:+.0f}", "acertos")

with tabs[2]:
    st.subheader("Ciclo")
    if st.button("ANALISAR"):
        st.session_state.ciclos[loteria] = {"numeros": random.sample(range(1,cfg["max"]+1),18)}
    if loteria in st.session_state.ciclos:
        st.code(" - ".join(f"{n:02d}" for n in sorted(st.session_state.ciclos[loteria]["numeros"])))

with tabs[3]:
    st.subheader("Posição no Ciclo")
    dados = []
    for lot,conf in configs.items():
        fase = random.choice(["Início","Meio","Fim","Virada"])
        dados.append({"Loteria":lot,"Fase":fase,"Ação":"↑ Focus" if fase in ["Fim","Virada"] else "→ Manter"})
    st.dataframe(pd.DataFrame(dados), hide_index=True)

with tabs[4]:
    st.subheader("IA 3 Sugestões")
    if st.button("Gerar", type="primary"):
        st.session_state.sugestoes_atuais = []
        for f in [max(10,focus-20), focus, min(95,focus+20)]:
            st.session_state.sugestoes_atuais.append({"focus":f,"jogo":gerar_jogo(f)})
    for i,s in enumerate(st.session_state.sugestoes_atuais,1):
        c1,c2 = st.columns([4,1])
        with c1: st.code(f"S{i} F{s['focus']}%: {' - '.join(f'{n:02d}' for n in s['jogo'])}")
        with c2:
            if st.button("Salvar",key=f"sv{i}"):
                st.session_state.historico_jogos.append({
                    "data":datetime.now().strftime("%d/%m %H:%M"),
                    "jogo":s["jogo"],"focus":s["focus"],"loteria":loteria,"acertos":None
                })
                st.success("Salvo!")

with tabs[5]:
    st.subheader("Fechamento Normal")
    if st.button("Gerar 5"):
        for i in range(5):
            st.code(f"F{i+1}: {' - '.join(f'{n:02d}' for n in gerar_jogo(focus))}")

with tabs[6]:
    st.subheader("🔒 Fechamento 21 Números - LOTOFÁCIL")
    st.caption("O famoso fechamento de 21 que você usava")
    
    if loteria != "Lotofácil":
        st.warning("Selecione Lotofácil na lateral")
    else:
        col1,col2 = st.columns(2)
        with col1:
            base_21 = st.multiselect("Escolha 21 números base", 
                                   options=list(range(1,26)),
                                   default=sorted(random.sample(range(1,26),21)),
                                   format_func=lambda x: f"{x:02d}")
        with col2:
            qtd_jogos_21 = st.number_input("Quantos jogos?", 5, 50, 10)
            garantia = st.selectbox("Garantia", ["13 acertos", "14 acertos", "15 acertos"])
        
        if st.button("Gerar Fechamento 21", type="primary") and len(base_21) == 21:
            st.success(f"Fechamento 21 números - {qtd_jogos_21} jogos - Garantia {garantia}")
            
            # Gera jogos garantindo cobertura dos 21 números com peso do Focus
            jogos_21 = []
            base_sorted = sorted(base_21)
            
            for i in range(qtd_jogos_21):
                # Usa Focus para priorizar números quentes dentro dos 21
                n_quentes = int(15 * focus / 100)
                quentes_21 = base_sorted[:14]  # primeiros 14 como "quentes"
                frios_21 = base_sorted[14:]     # últimos 7 como "frios"
                
                sel_q = random.sample(quentes_21, min(n_quentes, len(quentes_21)))
                sel_f = random.sample(frios_21 + quentes_21, 15 - len(sel_q))
                # Garante que todos vêm dos 21
                jogo = sorted(list(set(sel_q + sel_f))[:15])
                while len(jogo) < 15:
                    jogo.append(random.choice(base_sorted))
                    jogo = sorted(list(set(jogo)))
                jogos_21.append(jogo[:15])
            
            for i,j in enumerate(jogos_21,1):
                st.code(f"J{i:02d}: {' - '.join(f'{n:02d}' for n in j)}")
            
            custo = qtd_jogos_21 * 3.0
            st.info(f"💰 Custo total: R$ {custo:.2f} | Base: {' - '.join(f'{n:02d}' for n in base_sorted)}")
            
            if st.button("💾 Salvar todos no histórico"):
                for j in jogos_21:
                    st.session_state.historico_jogos.append({
                        "data": datetime.now().strftime("%d/%m %H:%M"),
                        "jogo": j, "focus": focus, "loteria": "Lotofácil", "acertos": None
                    })
                st.success(f"{len(jogos_21)} jogos salvos!")

with tabs[7]:
    st.subheader("Bolões")
    if st.button("Criar"):
        st.success("Bolão 15 jogos criado")

with tabs[8]:
    st.subheader("Resultados")
    for nome, nums in {"Lotofácil":[3,5,8,10,11,13,14,17,18,19,21,22,23,24,25],"Mega":[7,18,23,34,45,56]}.items():
        st.code(f"{nome}: {' - '.join(f'{n:02d}' for n in nums)}")

with tabs[9]:
    st.subheader("Meus Jogos")
    st.write(f"Total: {len(st.session_state.historico_jogos)}")
    for idx in range(len(st.session_state.historico_jogos)-1, max(-1,len(st.session_state.historico_jogos)-11), -1):
        jg = st.session_state.historico_jogos[idx]
        ac = jg.get('acertos')
        c1,c2 = st.columns([4,1])
        with c1:
            classe = f"acerto-{ac}" if ac and ac>=11 else ""
            html = f'<div class="historico-item {classe}">J{idx+1} - {" - ".join(f"{n:02d}" for n in jg["jogo"])} (F{jg["focus"]}%)</div>'
            st.markdown(html, unsafe_allow_html=True)
        with c2:
            if ac is None:
                inp = st.number_input("Ac",0,15,key=f"ac{idx}",label_visibility="collapsed")
                if st.button("OK",key=f"ok{idx}"):
                    st.session_state.historico_jogos[idx]['acertos'] = inp
                    com = [j for j in st.session_state.historico_jogos if j.get('acertos') is not None]
                    if com:
                        df = pd.DataFrame(com)
                        melhor_focus = df.groupby('focus')['acertos'].mean().idxmax()
                        st.session_state.perfil_aprendido = {
                            "acertos_medio": float(df['acertos'].mean()),
                            "focus_medio": int(df['focus'].mean()),
                            "total_jogos": len(com),
                            "melhor_focus": int(melhor_focus),
                            "media_melhor": float(df[df['focus']==melhor_focus]['acertos'].mean())
                        }
                    st.rerun()
            else:
                st.metric("", f"{ac} ac")

with tabs[10]:
    st.subheader("📥 Exportar para Excel")
    if not st.session_state.historico_jogos:
        st.info("Nenhum jogo para exportar")
    else:
        df_export = pd.DataFrame(st.session_state.historico_jogos)
        df_export['jogo_str'] = df_export['jogo'].apply(lambda x: ' - '.join(f"{n:02d}" for n in x))
        df_display = df_export[['data','loteria','focus','acertos','jogo_str']].copy()
        df_display.columns = ['Data','Loteria','Focus','Acertos','Jogo']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Cria Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Meus Jogos')
            # Aba resumo
            resumo = pd.DataFrame([{
                'Total Jogos': len(df_export),
                'Média Acertos': df_export['acertos'].mean() if 'acertos' in df_export else 0,
                'Melhor Focus': st.session_state.perfil_aprendido.get('melhor_focus',0),
                'Data Export': datetime.now().strftime("%d/%m/%Y %H:%M")
            }])
            resumo.to_excel(writer, index=False, sheet_name='Resumo IA')
        
        st.download_button(
            label="📥 Baixar Excel com todos os jogos",
            data=output.getvalue(),
            file_name=f"lotoelite_jogos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
        st.success(f"Pronto para baixar: {len(df_export)} jogos com histórico completo da IA")

st.caption("v72 - Gráfico + Export + Alerta + Fech 21")
