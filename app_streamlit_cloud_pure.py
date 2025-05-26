import streamlit as st
import OpenAI
import plotly.express as px
import plotly.graph_objects as go
import json
import re
import base64
import math

# Configurações da página Streamlit
st.set_page_config(
    page_title="Assistente de Análise InternReady",
    page_icon="🚀",
    layout="wide"
)

# Título principal
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

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
    # Ler o conteúdo do arquivo PDF
    pdf_bytes = pdf_file.getvalue()
    
    # Converter para base64
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Criar o prompt para a API
    prompt = f"""
    Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. 
    O usuário enviou um currículo em PDF. Sua tarefa é analisar este currículo com base em competências valorizadas no mercado financeiro.

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
    """
    
    # Configurar cliente OpenAI e fazer a chamada
    client = OpenAI(api_key=api_key)
    
    with st.spinner("⏳ Analisando com agente de IA..."):
        # Usar a API Vision para analisar o PDF
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000
        )
    
    resposta_completa = response.choices[0].message.content
    
    # Processar JSON da resposta
    match = re.search(r"\[(.*?)\]", resposta_completa, re.DOTALL)
    dados_json = json.loads("[" + match.group(1) + "]")
    
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
    
    # Processar dados sem pandas
    areas = []
    pontuacoes = []
    minimos = []
    status = []
    
    # Ordenar por pontuação (ascendente)
    dados_json.sort(key=lambda x: x["Pontuação"])
    
    for item in dados_json:
        area = item["Área"]
        pontuacao = item["Pontuação"]
        areas.append(area)
        pontuacoes.append(pontuacao)
        
        # Obter mínimo ideal
        minimo = minimos_financas.get(area.strip(), 55)
        minimos.append(minimo)
        
        # Definir status
        if pontuacao >= minimo:
            status.append("✔️ OK")
        else:
            status.append("❌ Abaixo do ideal")
    
    # Calcular afinidade com área financeira
    areas_financas = []
    pontuacoes_financas = []
    
    for i, area in enumerate(areas):
        if area in minimos_financas:
            areas_financas.append(area)
            pontuacoes_financas.append(pontuacoes[i])
    
    if pontuacoes_financas:
        afinidade_financas = round(sum(pontuacoes_financas) / len(pontuacoes_financas), 1)
    else:
        afinidade_financas = 0
    
    # Extrair texto da análise qualitativa
    texto_analise = resposta_completa.split("]")[-1].strip()
    
    # Criar estrutura de dados para tabela
    tabela_dados = []
    for i in range(len(areas)):
        tabela_dados.append({
            "Área": areas[i],
            "Pontuação": pontuacoes[i],
            "Mínimo Ideal": minimos[i],
            "Status": status[i]
        })
    
    return tabela_dados, areas, pontuacoes, minimos, status, afinidade_financas, texto_analise

# Botão para iniciar análise
if uploaded_file is not None and api_key:
    if st.button("🔍 Analisar Currículo"):
        try:
            tabela_dados, areas, pontuacoes, minimos, status, afinidade_financas, texto_analise = analisar_curriculo(uploaded_file, api_key)
            
            # Exibir resultados
            st.success("✅ Análise concluída com sucesso!")
            
            # Exibir tabela de competências
            st.header("📌 Tabela de Competências:")
            st.table(tabela_dados)
            
            # Criar visualizações em colunas
            col1, col2 = st.columns(2)
            
            # Gráfico de afinidade com área financeira
            with col1:
                fig = go.Figure(go.Bar(
                    x=["Afinidade com Área Financeira"],
                    y=[afinidade_financas],
                    marker_color='purple'
                ))
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    x1=0.5,
                    y0=75,
                    y1=75,
                    line=dict(color="gray", width=2, dash="dash"),
                )
                fig.update_layout(
                    title="🎯 Afinidade com o Setor Financeiro",
                    yaxis=dict(title="Pontuação Média (%)", range=[0, 100]),
                    showlegend=False
                )
                st.plotly_chart(fig)
            
            # Gráfico de competências vs mínimos
            with col2:
                cores = ['green' if s == "✔️ OK" else 'red' for s in status]
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=areas,
                    x=pontuacoes,
                    orientation='h',
                    marker_color=cores
                ))
                fig.update_layout(
                    title="📊 Competências vs Mínimos Recomendados (Finanças)",
                    xaxis=dict(title="Pontuação (0 a 100)"),
                    height=max(400, len(areas) * 25)
                )
                st.plotly_chart(fig)
            
            # Segunda linha de gráficos
            col3, col4 = st.columns(2)
            
            # Gráfico de dispersão
            with col3:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=areas,
                    y=pontuacoes,
                    mode='markers',
                    marker=dict(size=12),
                    name='Pontuação'
                ))
                fig.add_trace(go.Scatter(
                    x=areas,
                    y=minimos,
                    mode='markers',
                    marker=dict(symbol='x', size=8, color='orange'),
                    name='Mínimo Ideal'
                ))
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    x1=len(areas) - 0.5,
                    y0=50,
                    y1=50,
                    line=dict(color="gray", width=2, dash="dash"),
                )
                fig.update_layout(
                    title="📍 Dispersão de Pontuações por Área",
                    yaxis=dict(title="Pontuação"),
                    xaxis=dict(tickangle=45),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig)
            
            # Gráfico de distribuição por nível
            with col4:
                # Classificar pontuações por nível
                baixa = sum(1 for p in pontuacoes if p < 50)
                media = sum(1 for p in pontuacoes if 50 <= p < 75)
                alta = sum(1 for p in pontuacoes if p >= 75)
                
                fig = go.Figure(go.Bar(
                    x=["Baixa", "Média", "Alta"],
                    y=[baixa, media, alta],
                    marker_color=['red', 'orange', 'green']
                ))
                fig.update_layout(
                    title="📘 Distribuição de Competências por Nível",
                    yaxis=dict(title="Número de Áreas"),
                    xaxis=dict(title="Nível")
                )
                st.plotly_chart(fig)
            
            # Gráfico radar
            st.subheader("🕸️ Radar de Competências")
            
            # Preparar dados para o radar
            areas_radar = areas.copy()
            pontuacoes_radar = pontuacoes.copy()
            areas_radar.append(areas_radar[0])
            pontuacoes_radar.append(pontuacoes_radar[0])
            
            # Calcular ângulos para o radar
            theta = []
            for i in range(len(areas_radar)):
                theta.append(i * 2 * math.pi / (len(areas_radar) - 1))
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=pontuacoes_radar,
                theta=areas_radar,
                fill='toself',
                name='Competências'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=False,
                title="🕸️ Radar de Competências"
            )
            st.plotly_chart(fig)
            
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
