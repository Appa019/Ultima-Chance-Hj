import streamlit as st
import openai
import fitz  # PyMuPDF
import pandas as pd
import matplotlib.pyplot as plt
from math import pi
import json
import re
import base64
import tempfile

st.set_page_config(page_title="Assistente de Análise InternReady", page_icon="🚀", layout="wide")
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("🔑 Cole sua *Chave InternReady*:", type="password")
    st.markdown("---")
    st.markdown("### Como usar:")
    st.markdown("1. Insira sua chave de API\n2. Faça upload do currículo em PDF\n3. Clique em 'Analisar Currículo'")

st.header("📄 Upload do Currículo")
uploaded_file = st.file_uploader("Envie seu currículo em PDF", type="pdf")

if uploaded_file and api_key:
    if st.button("🔍 Analisar Currículo"):
        try:
            openai.api_key = api_key
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(uploaded_file.getvalue())
                pdf_path = temp_file.name

            doc = fitz.open(pdf_path)
            texto_curriculo = ""
            for page in doc:
                texto_curriculo += page.get_text()
            doc.close()

        prompt = (
    "Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. "
    "Sua tarefa é analisar o currículo abaixo com base em competências valorizadas nesse mercado.\n\n"
    "**Parte 1 – Análise Quantitativa**\n"
    "- Identifique as principais **áreas de competência profissional** (ex: Finanças, Economia, Risco, Análise de Dados, Excel, Programação, Comunicação, etc.).\n"
    "- Para cada área, atribua uma nota de **0 a 100**, com base nas evidências fornecidas no texto como um especialista em recursos humanos com muitos anos de prática. **Não infira habilidades não mencionadas.**\n"
    "- A resposta deve estar no formato JSON conforme exemplo:\n\n"
    "[\n"
    "  {\"Área\": \"Gestão Financeira\", \"Pontuação\": 82},\n"
    "  {\"Área\": \"Excel Avançado\", \"Pontuação\": 78}\n"
    "]\n\n"
    "**Parte 2 – Análise Qualitativa (em português)**\n"
    "- Pontos fortes mais evidentes\n"
    "- Pontos que podem ser melhor desenvolvidos ou explicitados\n"
    "- Sugestões práticas para aprimorar o currículo para o mercado financeiro\n\n"
    "Texto do currículo:\n"
    f"\"\"\"\n{texto_curriculo}\n\"\"\""
)


            with st.spinner("⏳ Analisando com IA..."):
                response = openai.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )

            resposta_completa = response.choices[0].message.content
            match = re.search(r"\[(.*?)\]", resposta_completa, re.DOTALL)
            dados_json = json.loads("[" + match.group(1) + "]")
            df = pd.DataFrame(dados_json)
            df = df.sort_values(by="Pontuação", ascending=True)

            st.header("📌 Tabela de Competências")
            st.dataframe(df)

            minimos_financas = {
                "Finanças": 80, "Economia": 85, "Mercado Financeiro": 82,
                "Contabilidade": 78, "Excel Avançado": 90, "SQL": 75,
                "Python": 78, "Power BI": 80, "Análise de Dados": 82,
                "Comunicação Oral": 78, "Comunicação Escrita": 80,
                "Modelagem Financeira": 84, "Valuation": 83,
                "Gestão Orçamentária": 80, "Planejamento Financeiro": 82
            }

            df["Mínimo Ideal"] = df["Área"].apply(lambda x: minimos_financas.get(x.strip(), 55))
            df["Status"] = df.apply(lambda row: "✔️ OK" if row["Pontuação"] >= row["Mínimo Ideal"] else "❌ Abaixo do ideal", axis=1)

            afinidade_df = df[df["Área"].isin(minimos_financas.keys())]
            afinidade_financas = round(afinidade_df["Pontuação"].mean(), 1)

            st.subheader("🎯 Afinidade com Área Financeira")
            fig1, ax1 = plt.subplots()
            ax1.bar(["Afinidade"], [afinidade_financas], color='purple')
            ax1.set_ylim(0, 100)
            ax1.axhline(75, linestyle='--', color='gray', label='Referência ideal')
            ax1.set_ylabel("Pontuação (%)")
            ax1.legend()
            st.pyplot(fig1)

            st.subheader("📊 Competências vs Mínimos")
            fig2, ax2 = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))
            ax2.barh(df["Área"], df["Pontuação"], color=df["Status"].map({"✔️ OK": "green", "❌ Abaixo do ideal": "red"}))
            ax2.set_xlabel("Pontuação (0 a 100)")
            ax2.grid(True, axis='x')
            st.pyplot(fig2)

            st.subheader("🕸️ Radar de Competências")
            labels = df["Área"].tolist() + [df["Área"].tolist()[0]]
            values = df["Pontuação"].tolist() + [df["Pontuação"].tolist()[0]]
            angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
            fig3, ax3 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            ax3.plot(angles, values, linewidth=2)
            ax3.fill(angles, values, alpha=0.25)
            ax3.set_xticks(angles[:-1])
            ax3.set_xticklabels(df["Área"].tolist(), rotation=45)
            st.pyplot(fig3)

            st.header("📝 Análise Qualitativa")
            texto_analise = resposta_completa.split("]")[-1].strip()
            st.markdown(texto_analise)

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {e}")

elif uploaded_file and not api_key:
    st.warning("⚠️ Insira sua chave de API para continuar.")
elif api_key and not uploaded_file:
    st.info("📤 Faça upload de um currículo em PDF para iniciar.")
