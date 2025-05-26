import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from math import pi
import json
import re
import tempfile
import os

# Configuração da página
st.set_page_config(page_title="Assistente de Análise InternReady", page_icon="🚀", layout="wide")
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("🔑 Cole sua *Chave InternReady*:", type="password")
    st.markdown("---")
    st.markdown("### Como usar:")
    st.markdown("1. Insira sua chave de API\n2. Faça upload do currículo em PDF\n3. Clique em 'Analisar Currículo'")

# Upload de arquivo
st.header("📄 Upload do Currículo")
uploaded_file = st.file_uploader("Envie seu currículo em PDF", type="pdf")

if uploaded_file and api_key:
    if st.button("🔍 Analisar Currículo"):
        try:
            # Configurar cliente OpenAI
            client = OpenAI(api_key=api_key)
            
            # Processar PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(uploaded_file.getvalue())
                pdf_path = temp_file.name

            # Extrair texto do PDF
            doc = fitz.open(pdf_path)
            texto_curriculo = ""
            for page in doc:
                texto_curriculo += page.get_text()
            doc.close()
            
            # Limpar arquivo temporário
            os.unlink(pdf_path)

            # Prompt para análise
            prompt = f"""
Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. Sua tarefa é analisar o currículo abaixo com base em competências valorizadas nesse mercado.

**Parte 1 – Análise Quantitativa**
- Identifique as principais **áreas de competência profissional** (ex: Finanças, Economia, Risco, Análise de Dados, Excel, Programação, Comunicação, etc.).
- Para cada área, atribua uma nota de **0 a 100**, com base nas evidências fornecidas no texto como um especialista em recursos humanos com muitos anos de prática. **Não infira habilidades não mencionadas.**
- A resposta deve estar no formato JSON conforme exemplo:

[
  {{"Área": "Gestão Financeira", "Pontuação": 82}},
  {{"Área": "Excel Avançado", "Pontuação": 78}}
]

**Parte 2 – Análise Qualitativa (em português)**
- Pontos fortes mais evidentes
- Pontos que podem ser melhor desenvolvidos ou explicitados
- Sugestões práticas para aprimorar o currículo para o mercado financeiro

Texto do currículo:
{texto_curriculo}
"""

            # Chamar API OpenAI
            with st.spinner("⏳ Analisando com IA..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )

            resposta_completa = response.choices[0].message.content
            
            # Extrair JSON da resposta
            match = re.search(r'\[(.*?)\]', resposta_completa, re.DOTALL)
            if not match:
                st.error("❌ Erro: Não foi possível extrair os dados de competências da resposta da IA.")
                st.text("Resposta da IA:")
                st.text(resposta_completa)
            else:
                try:
                    dados_json = json.loads("[" + match.group(1) + "]")
                    df = pd.DataFrame(dados_json)
                    
                    # Verificar se o DataFrame não está vazio
                    if df.empty:
                        st.error("❌ Nenhuma competência foi identificada no currículo.")
                    else:
                        df = df.sort_values(by="Pontuação", ascending=True)

                        # Tabela de competências
                        st.header("📌 Tabela de Competências")
                        st.dataframe(df, use_container_width=True)

                        # Definir mínimos ideais para finanças
                        minimos_financas = {
                            "Finanças": 80, "Economia": 85, "Mercado Financeiro": 82,
                            "Contabilidade": 78, "Excel Avançado": 90, "SQL": 75,
                            "Python": 78, "Power BI": 80, "Análise de Dados": 82,
                            "Comunicação Oral": 78, "Comunicação Escrita": 80,
                            "Modelagem Financeira": 84, "Valuation": 83,
                            "Gestão Orçamentária": 80, "Planejamento Financeiro": 82
                        }

                        # Adicionar colunas de análise
                        df["Mínimo Ideal"] = df["Área"].apply(lambda x: minimos_financas.get(x.strip(), 55))
                        df["Status"] = df.apply(lambda row: "✔️ OK" if row["Pontuação"] >= row["Mínimo Ideal"] else "❌ Abaixo do ideal", axis=1)

                        # Calcular afinidade com área financeira
                        afinidade_df = df[df["Área"].isin(minimos_financas.keys())]
                        if not afinidade_df.empty:
                            afinidade_financas = round(afinidade_df["Pontuação"].mean(), 1)
                        else:
                            afinidade_financas = 0

                        # Gráfico de afinidade
                        st.subheader("🎯 Afinidade com Área Financeira")
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.metric("Pontuação Geral", f"{afinidade_financas}%")
                            if afinidade_financas >= 75:
                                st.success("Excelente afinidade!")
                            elif afinidade_financas >= 60:
                                st.warning("Boa afinidade, mas há espaço para melhoria")
                            else:
                                st.error("Afinidade baixa - recomenda-se desenvolvimento")
                        
                        with col2:
                            fig_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = afinidade_financas,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "Afinidade Financeira (%)"},
                                gauge = {
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "purple"},
                                    'steps': [
                                        {'range': [0, 50], 'color': "lightgray"},
                                        {'range': [50, 75], 'color': "yellow"},
                                        {'range': [75, 100], 'color': "lightgreen"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': 75
                                    }
                                }
                            ))
                            fig_gauge.update_layout(height=300)
                            st.plotly_chart(fig_gauge, use_container_width=True)

                        # Gráfico de barras horizontais
                        st.subheader("📊 Competências vs Mínimos")
                        fig_bar = px.bar(
                            df.sort_values(by="Pontuação", ascending=True),
                            x="Pontuação",
                            y="Área",
                            orientation='h',
                            color="Status",
                            color_discrete_map={"✔️ OK": "green", "❌ Abaixo do ideal": "red"},
                            title="Pontuação das Competências"
                        )
                        fig_bar.update_layout(height=max(400, len(df) * 30))
                        st.plotly_chart(fig_bar, use_container_width=True)

                        # Gráfico radar
                        st.subheader("🕸️ Radar de Competências")
                        if len(df) > 0:
                            fig_radar = go.Figure()
                            
                            fig_radar.add_trace(go.Scatterpolar(
                                r=df["Pontuação"].tolist(),
                                theta=df["Área"].tolist(),
                                fill='toself',
                                name='Competências Atuais',
                                line_color='blue'
                            ))
                            
                            # Adicionar linha de referência ideal quando aplicável
                            if not afinidade_df.empty:
                                fig_radar.add_trace(go.Scatterpolar(
                                    r=afinidade_df["Mínimo Ideal"].tolist(),
                                    theta=afinidade_df["Área"].tolist(),
                                    fill='toself',
                                    name='Mínimo Ideal',
                                    line_color='red',
                                    opacity=0.6
                                ))
                            
                            fig_radar.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100]
                                    )),
                                showlegend=True,
                                height=500
                            )
                            
                            st.plotly_chart(fig_radar, use_container_width=True)

                        # Análise qualitativa
                        st.header("📝 Análise Qualitativa")
                        # Procurar por texto após o JSON
                        partes = resposta_completa.split("]")
                        if len(partes) > 1:
                            texto_analise = partes[-1].strip()
                            if texto_analise:
                                st.markdown(texto_analise)
                            else:
                                st.info("Análise qualitativa não disponível nesta resposta.")
                        else:
                            st.info("Análise qualitativa não encontrada na resposta.")

                        # Tabela detalhada com status
                        st.header("📋 Análise Detalhada")
                        st.dataframe(
                            df[["Área", "Pontuação", "Mínimo Ideal", "Status"]].sort_values(by="Pontuação", ascending=False),
                            use_container_width=True
                        )

                except json.JSONDecodeError as je:
                    st.error(f"❌ Erro ao processar JSON: {je}")
                    st.text("Conteúdo JSON extraído:")
                    st.text("[" + match.group(1) + "]")
                except Exception as pe:
                    st.error(f"❌ Erro ao processar dados: {pe}")

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")
            st.info("Verifique se sua chave de API está correta e se você tem créditos disponíveis.")

elif uploaded_file and not api_key:
    st.warning("⚠️ Insira sua chave de API para continuar.")
elif api_key and not uploaded_file:
    st.info("📤 Faça upload de um currículo em PDF para iniciar.")
else:
    st.info("👋 Bem-vindo! Insira sua chave de API e faça upload de um currículo para começar.")
