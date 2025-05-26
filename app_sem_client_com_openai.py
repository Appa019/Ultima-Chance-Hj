import streamlit as st
import openai
import plotly.express as px
import plotly.graph_objects as go
import json
import re
import base64
import math

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

def analisar_curriculo(pdf_file, api_key):
    openai.api_key = api_key
    pdf_bytes = pdf_file.getvalue()
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    prompt = """Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. 
    O usuário enviou um currículo em PDF. Sua tarefa é analisar este currículo com base em competências valorizadas no mercado financeiro.

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
    - Sugestões práticas para aprimorar o currículo para o mercado financeiro"""

    with st.spinner("⏳ Analisando com IA..."):
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:application/pdf;base64,{pdf_base64}"}}
                ]
            }],
            max_tokens=4000
        )

    resposta_completa = response.choices[0].message.content
    match = re.search(r"\[(.*?)\]", resposta_completa, re.DOTALL)
    dados_json = json.loads("[" + match.group(1) + "]")

    minimos_financas = {
        "Finanças": 80, "Economia": 85, "Mercado Financeiro": 82, "Contabilidade": 78,
        "Excel Avançado": 90, "SQL": 75, "Python": 78, "Power BI": 80,
        "Análise de Dados": 82, "Comunicação Oral": 78, "Comunicação Escrita": 80,
        "Modelagem Financeira": 84, "Valuation": 83, "Gestão Orçamentária": 80, "Planejamento Financeiro": 82
    }

    dados_json.sort(key=lambda x: x["Pontuação"])
    areas, pontuacoes, minimos, status = [], [], [], []

    for item in dados_json:
        area = item["Área"]
        p = item["Pontuação"]
        minimo = minimos_financas.get(area.strip(), 55)
        areas.append(area)
        pontuacoes.append(p)
        minimos.append(minimo)
        status.append("✔️ OK" if p >= minimo else "❌ Abaixo do ideal")

    afinidade_financas = round(sum([p for a, p in zip(areas, pontuacoes) if a in minimos_financas]) / max(1, len([a for a in areas if a in minimos_financas])), 1)
    texto_analise = resposta_completa.split("]")[-1].strip()

    tabela_dados = [{"Área": a, "Pontuação": p, "Mínimo Ideal": m, "Status": s} for a, p, m, s in zip(areas, pontuacoes, minimos, status)]
    return tabela_dados, areas, pontuacoes, minimos, status, afinidade_financas, texto_analise

if uploaded_file and api_key:
    if st.button("🔍 Analisar Currículo"):
        try:
            tabela_dados, areas, pontuacoes, minimos, status, afinidade, texto = analisar_curriculo(uploaded_file, api_key)
            st.success("✅ Análise concluída com sucesso!")
            st.header("📌 Tabela de Competências:")
            st.table(tabela_dados)
        except Exception as e:
            st.error(f"Erro: {e}")
elif uploaded_file and not api_key:
    st.warning("⚠️ Insira a chave de API.")
elif api_key and not uploaded_file:
    st.info("📤 Envie o PDF para iniciar.")

st.markdown("---")
st.markdown("### Desenvolvido com ❤️ pelo InternReady")