# -*- coding: utf-8 -*-
"""Assistente de Analise InternReady - Streamlit App"""

import streamlit as st
import openai
import fitz  # PyMuPDF
import pandas as pd
import matplotlib.pyplot as plt
from math import pi
import json
import re
import tempfile
import os

# Configurações visuais do Matplotlib
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 12

# Configuração da página
st.set_page_config(page_title="Assistente de Análise InternReady", page_icon="🚀", layout="wide")
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

# Sidebar com configurações
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("🔑 Cole sua *Chave InternReady*:", type="password")
    st.markdown("---")
    st.markdown("### Como usar:")
    st.markdown("1. Insira sua chave de API\n2. Faça upload do currículo em PDF\n3. Clique em 'Analisar Currículo'")

# Upload de arquivo
st.header("📄 Upload do Currículo")
uploaded_file = st.file_uploader("📎 Envie seu currículo em PDF", type="pdf")

if uploaded_file and api_key:
    if st.button("🔍 Analisar Currículo", type="primary"):
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

            st.success(f"✅ Currículo carregado com sucesso: `{uploaded_file.name}`")

            # Prompt original mantido
            prompt = f"""
Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. Sua tarefa é analisar o currículo abaixo com base em competências valorizadas nesse mercado.

**Parte 1 – Análise Quantitativa**
- Identifique as principais **áreas de competência profissional** (ex: Finanças, Economia, Risco, Análise de Dados, Excel, Programação, Comunicação, etc.).
- Para cada área, atribua uma nota de **0 a 100**, com base nas evidências fornecidas no texto como um especialista em recursos humanos com muitos anos de pratica. **Não infira habilidades não mencionadas.**
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
\"\"\"
{texto_curriculo}
\"\"\"
"""

            # Chamar API OpenAI com progress bar
            with st.spinner("⏳ Analisando com agente de IA..."):
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )

            resposta_completa = response.choices[0].message.content
            st.success("✅ Análise concluída.")

            # Processar JSON (código original mantido)
            match = re.search(r"\[(.*?)\]", resposta_completa, re.DOTALL)
            if not match:
                st.error("❌ Erro: Não foi possível extrair os dados de competências.")
                st.text(resposta_completa)
            else:
                dados_json = json.loads("[" + match.group(1) + "]")
                df = pd.DataFrame(dados_json)
                df = df.sort_values(by="Pontuação", ascending=True)
                
                # Tabela de competências
                st.markdown("### 📌 Tabela de Competências:")
                st.dataframe(df, use_container_width=True)

                # Mínimos originais mantidos
                minimos_financas = {
                    "Finanças": 80, "Economia": 85, "Mercado Financeiro": 82,
                    "Contabilidade": 78, "Contabilidade Gerencial": 75,
                    "Análise de Demonstrativos Financeiros": 83, "Controladoria": 75,
                    "Tesouraria": 76, "Gestão Orçamentária": 80, "Planejamento Financeiro": 82,
                    "Análise de Investimentos": 82, "Valuation": 83, "Modelagem Financeira": 84,
                    "Riscos Financeiros": 80, "Compliance": 75, "Auditoria": 78,
                    "Governança Corporativa": 76, "Gestão de Ativos": 80, "Gestão de Riscos": 80,
                    "Excel": 92, "Excel Avançado": 90, "Power BI": 80, "SQL": 75,
                    "Python": 78, "R": 75, "VBA": 70, "Access": 65, "ETL": 70,
                    "Análise de Dados": 82, "Business Intelligence": 80, "Data Analytics": 82,
                    "Big Data": 70, "Dashboards": 78, "CVM": 75, "Bacen": 75,
                    "IFRS": 80, "Normas Contábeis": 77, "Regulação Bancária": 78,
                    "Inglês": 85, "Espanhol": 70, "Comunicação Escrita": 80,
                    "Comunicação Oral": 78, "Apresentações Executivas": 80,
                    "Gestão de Projetos": 75, "Liderança": 78, "Tomada de Decisão": 80,
                    "Pensamento Crítico": 82, "Resolução de Problemas": 80,
                    "Trabalho em Equipe": 78, "Autonomia": 76, "Proatividade": 78,
                    "Ética Profissional": 85, "Organização": 75,
                }

                df["Mínimo Ideal"] = df["Área"].apply(lambda x: minimos_financas.get(x.strip(), 55))
                df["Status"] = df.apply(lambda row: "✔️ OK" if row["Pontuação"] >= row["Mínimo Ideal"] else "❌ Abaixo do ideal", axis=1)

                afinidade_df = df[df["Área"].isin(minimos_financas.keys())]
                if not afinidade_df.empty:
                    afinidade_financas = round(afinidade_df["Pontuação"].mean(), 1)
                else:
                    afinidade_financas = 0

                # Gráfico 1: Afinidade com Área Financeira
                st.markdown("### 🎯 Afinidade com o Setor Financeiro")
                fig1, ax1 = plt.subplots()
                ax1.bar(["Afinidade com Área Financeira"], [afinidade_financas], color='purple')
                ax1.set_ylim(0, 100)
                ax1.axhline(75, linestyle='--', color='gray', label='Referência ideal')
                ax1.set_title("🎯 Afinidade com o Setor Financeiro")
                ax1.set_ylabel("Pontuação Média (%)")
                ax1.legend()
                plt.tight_layout()
                st.pyplot(fig1)

                # Gráfico 2: Competências vs Mínimos
                st.markdown("### 📊 Competências vs Mínimos Recomendados")
                fig2, ax2 = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))
                ax2.barh(df["Área"], df["Pontuação"], color=df["Status"].map({"✔️ OK": "green", "❌ Abaixo do ideal": "red"}))
                ax2.set_xlabel("Pontuação (0 a 100)")
                ax2.set_title("📊 Competências vs Mínimos Recomendados (Finanças)")
                ax2.grid(True, axis='x')
                plt.tight_layout()
                st.pyplot(fig2)

                # Gráfico 3: Dispersão de Pontuações
                st.markdown("### 📍 Dispersão de Pontuações por Área")
                fig3, ax3 = plt.subplots()
                ax3.scatter(df["Área"], df["Pontuação"], s=100)
                for i, row in df.iterrows():
                    ax3.plot([row["Área"]], [row["Mínimo Ideal"]], marker="x", color="orange")
                ax3.axhline(50, color='gray', linestyle='--', label='Mínimo Geral')
                ax3.set_xticklabels(df["Área"], rotation=45)
                ax3.set_title("📍 Dispersão de Pontuações por Área")
                ax3.set_ylabel("Pontuação")
                ax3.legend()
                plt.tight_layout()
                st.pyplot(fig3)

                # Gráfico 4: Distribuição por Nível
                st.markdown("### 📘 Distribuição de Competências por Nível")
                df['Nível'] = pd.cut(df['Pontuação'], bins=[-1, 49, 74, 100], labels=["Baixa", "Média", "Alta"])
                nivel_counts = df['Nível'].value_counts().sort_index()
                fig4, ax4 = plt.subplots()
                nivel_counts.plot(kind='bar', color=['red', 'orange', 'green'], ax=ax4)
                ax4.set_title("📘 Distribuição de Competências por Nível")
                ax4.set_ylabel("Número de Áreas")
                ax4.set_xticklabels(ax4.get_xticklabels(), rotation=0)
                ax4.grid(axis='y')
                plt.tight_layout()
                st.pyplot(fig4)

                # Gráfico 5: Radar de Competências
                st.markdown("### 🕸️ Radar de Competências")
                labels = df["Área"].tolist()
                values = df["Pontuação"].tolist()
                labels += [labels[0]]
                values += [values[0]]
                angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
                fig5, ax5 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
                ax5.plot(angles, values, linewidth=2)
                ax5.fill(angles, values, alpha=0.25)
                ax5.set_xticks(angles[:-1])
                ax5.set_xticklabels(labels[:-1])
                ax5.set_title("🕸️ Radar de Competências")
                st.pyplot(fig5)

                # Análise textual
                st.markdown("### 📝 Análise Textual:")
                texto_analise = resposta_completa.split("]")[-1].strip()
                if texto_analise:
                    st.markdown(texto_analise)
                else:
                    st.info("Análise qualitativa não disponível.")

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")
            st.info("Verifique se sua chave de API está correta e se você tem créditos disponíveis.")

elif uploaded_file and not api_key:
    st.warning("⚠️ Insira sua chave de API para continuar.")
elif api_key and not uploaded_file:
    st.info("📤 Faça upload de um currículo em PDF para iniciar.")
else:
    st.info("👋 Bem-vindo! Insira sua chave de API e faça upload de um currículo para começar.")
