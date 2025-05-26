import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
import pandas as pd
import matplotlib.pyplot as plt
from math import pi
import json
import re
import io
import tempfile
from tqdm import tqdm

# Configurações da página Streamlit
st.set_page_config(
    page_title="Assistente de Análise InternReady",
    page_icon="🚀",
    layout="wide"
)

# Título principal
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

# Configurações visuais do Matplotlib
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 12

# Sidebar para entrada da API
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("🔑 Cole sua *Chave InternReady*:", type="password")
    
    st.markdown("---")
    st.markdown("### Como usar:")
    st.markdown("""
    1. Insira sua chave de API
    2. Faça upload do seu currículo em PDF
    3. Clique em 'Analisar Currículo'
    4. Veja os resultados da análise
    """)

# Área principal para upload do PDF
st.header("📄 Upload do Currículo")
uploaded_file = st.file_uploader("Envie seu currículo em PDF", type="pdf")

# Função para processar o PDF e fazer a análise
def analisar_curriculo(pdf_file, api_key):
    # Criar um arquivo temporário para o PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(pdf_file.getvalue())
        pdf_path = temp_file.name
    
    # Extrair texto do PDF
    doc = fitz.open(pdf_path)
    texto_curriculo = ""
    for page in doc:
        texto_curriculo += page.get_text()
    doc.close()
    
    # Criar o prompt para a API
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
    
    # Configurar cliente OpenAI e fazer a chamada
    client = OpenAI(api_key=api_key)
    
    with st.spinner("⏳ Analisando com agente de IA..."):
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
    
    resposta_completa = response.choices[0].message.content
    
    # Processar JSON da resposta
    match = re.search(r"\[(.*?)\]", resposta_completa, re.DOTALL)
    dados_json = json.loads("[" + match.group(1) + "]")
    df = pd.DataFrame(dados_json)
    df = df.sort_values(by="Pontuação", ascending=True)
    
    # Definir mínimos para o setor financeiro
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
    
    # Calcular afinidade com área financeira
    afinidade_df = df[df["Área"].isin(minimos_financas.keys())]
    afinidade_financas = round(afinidade_df["Pontuação"].mean(), 1)
    
    # Extrair texto da análise qualitativa
    texto_analise = resposta_completa.split("]")[-1].strip()
    
    return df, afinidade_financas, texto_analise

# Botão para iniciar análise
if uploaded_file is not None and api_key:
    if st.button("🔍 Analisar Currículo"):
        try:
            df, afinidade_financas, texto_analise = analisar_curriculo(uploaded_file, api_key)
            
            # Exibir resultados
            st.success("✅ Análise concluída com sucesso!")
            
            # Exibir tabela de competências
            st.header("📌 Tabela de Competências:")
            st.dataframe(df)
            
            # Criar visualizações em colunas
            col1, col2 = st.columns(2)
            
            # Gráfico de afinidade com área financeira
            with col1:
                fig, ax = plt.subplots()
                ax.bar(["Afinidade com Área Financeira"], [afinidade_financas], color='purple')
                ax.set_ylim(0, 100)
                ax.axhline(75, linestyle='--', color='gray', label='Referência ideal')
                ax.set_title("🎯 Afinidade com o Setor Financeiro")
                ax.set_ylabel("Pontuação Média (%)")
                ax.legend()
                plt.tight_layout()
                st.pyplot(fig)
            
            # Gráfico de competências vs mínimos
            with col2:
                fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))
                ax.barh(df["Área"], df["Pontuação"], color=df["Status"].map({"✔️ OK": "green", "❌ Abaixo do ideal": "red"}))
                ax.set_xlabel("Pontuação (0 a 100)")
                ax.set_title("📊 Competências vs Mínimos Recomendados (Finanças)")
                ax.grid(True, axis='x')
                plt.tight_layout()
                st.pyplot(fig)
            
            # Segunda linha de gráficos
            col3, col4 = st.columns(2)
            
            # Gráfico de dispersão
            with col3:
                fig, ax = plt.subplots()
                ax.scatter(df["Área"], df["Pontuação"], s=100)
                for i, row in df.iterrows():
                    ax.plot([row["Área"]], [row["Mínimo Ideal"]], marker="x", color="orange")
                ax.axhline(50, color='gray', linestyle='--', label='Mínimo Geral')
                plt.xticks(rotation=45)
                ax.set_title("📍 Dispersão de Pontuações por Área")
                ax.set_ylabel("Pontuação")
                ax.legend()
                plt.tight_layout()
                st.pyplot(fig)
            
            # Gráfico de distribuição por nível
            with col4:
                df['Nível'] = pd.cut(df['Pontuação'], bins=[-1, 49, 74, 100], labels=["Baixa", "Média", "Alta"])
                nivel_counts = df['Nível'].value_counts().sort_index()
                fig, ax = plt.subplots()
                nivel_counts.plot(kind='bar', color=['red', 'orange', 'green'], ax=ax)
                ax.set_title("📘 Distribuição de Competências por Nível")
                ax.set_ylabel("Número de Áreas")
                plt.xticks(rotation=0)
                ax.grid(axis='y')
                plt.tight_layout()
                st.pyplot(fig)
            
            # Gráfico radar
            st.subheader("🕸️ Radar de Competências")
            labels = df["Área"].tolist()
            values = df["Pontuação"].tolist()
            labels += [labels[0]]
            values += [values[0]]
            angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            ax.plot(angles, values, linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels[:-1], rotation=45)
            ax.set_title("🕸️ Radar de Competências")
            st.pyplot(fig)
            
            # Análise textual
            st.header("📝 Análise Qualitativa:")
            st.markdown(texto_analise)
            
        except Exception as e:
            st.error(f"Ocorreu um erro durante a análise: {str(e)}")
            st.info("Verifique se a chave da API está correta e tente novamente.")
elif not api_key and uploaded_file:
    st.warning("⚠️ Por favor, insira sua chave de API para continuar.")
elif api_key and not uploaded_file:
    st.info("📤 Faça o upload do seu currículo em PDF para iniciar a análise.")

# Rodapé
st.markdown("---")
st.markdown("### Desenvolvido com ❤️ pelo InternReady")
st.markdown("Assistente de Análise de Currículo para o Setor Financeiro")
