# -*- coding: utf-8 -*-
"""Assistente de Analise InternReady - Streamlit App - Versão Otimizada"""

import streamlit as st
import pandas as pd
import json
import re
import tempfile
import os
from math import pi
import sys

# Configuração da página (deve estar no topo)
st.set_page_config(
    page_title="Assistente de Análise InternReady", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para verificar dependências
@st.cache_data
def verificar_dependencias():
    """Verifica e reporta status das dependências"""
    deps_status = {}
    
    try:
        from openai import OpenAI
        deps_status['openai'] = True
    except ImportError:
        deps_status['openai'] = False
    
    try:
        import fitz  # PyMuPDF
        deps_status['pymupdf'] = True
    except ImportError:
        deps_status['pymupdf'] = False
    
    try:
        import matplotlib.pyplot as plt
        deps_status['matplotlib'] = True
        # Configurações visuais do Matplotlib
        plt.rcParams['figure.figsize'] = [10, 6]
        plt.rcParams['font.size'] = 12
    except ImportError:
        deps_status['matplotlib'] = False
    
    return deps_status

# Interface principal
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

# Verificar dependências
deps_status = verificar_dependencias()
missing_deps = [dep for dep, status in deps_status.items() if not status]

if missing_deps:
    st.error(f"❌ Bibliotecas não encontradas: {', '.join(missing_deps)}")
    st.info("💡 Verifique se o requirements.txt está correto no repositório")
    
    with st.expander("📋 Requirements.txt recomendado"):
        st.code("""# Requirements.txt otimizado para Streamlit Cloud
streamlit>=1.28.0,<2.0.0
openai>=1.3.0,<2.0.0
pymupdf>=1.23.0,<1.24.0
pandas>=1.5.0,<3.0.0
matplotlib>=3.5.0,<4.0.0
numpy>=1.21.0,<2.0.0
pillow>=8.0.0,<11.0.0""")
    st.stop()

# Imports condicionais (só após verificação)
from openai import OpenAI
import fitz  # PyMuPDF
import matplotlib.pyplot as plt

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input(
        "🔑 Cole sua *Chave InternReady*:", 
        type="password",
        help="Sua chave da API OpenAI"
    )
    
    if api_key:
        st.success("✅ Chave inserida")
    
    st.markdown("---")
    st.markdown("### 📖 Como usar:")
    st.markdown("""
    1. **Insira sua chave de API** acima
    2. **Faça upload do currículo** em PDF
    3. **Clique em 'Analisar Currículo'**
    4. **Aguarde a análise** completa
    """)

def extrair_json_robusto(texto):
    """Extrai JSON de forma mais robusta do texto da resposta"""
    try:
        # Tenta encontrar JSON entre colchetes
        match = re.search(r"\[(.*?)\]", texto, re.DOTALL)
        if match:
            json_str = "[" + match.group(1) + "]"
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    try:
        # Tenta encontrar objetos JSON individuais
        objetos = re.findall(r'\{[^{}]*\}', texto)
        dados = []
        for obj in objetos:
            try:
                dados.append(json.loads(obj))
            except json.JSONDecodeError:
                continue
        if dados:
            return dados
    except Exception:
        pass
    
    return None

def criar_grafico_radar_seguro(df):
    """Cria gráfico radar com verificações de segurança"""
    if len(df) < 3:
        st.warning("⚠️ Necessário pelo menos 3 competências para gráfico radar")
        return None
    
    try:
        labels = df["Área"].tolist()
        values = df["Pontuação"].tolist()
        
        # Adiciona o primeiro ponto no final para fechar o polígono
        labels += [labels[0]]
        values += [values[0]]
        
        angles = [n / float(len(labels)-1) * 2 * pi for n in range(len(labels))]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.plot(angles, values, linewidth=2, color='#1f77b4')
        ax.fill(angles, values, alpha=0.25, color='#1f77b4')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels[:-1], fontsize=10)
        ax.set_ylim(0, 100)
        ax.set_title("🕸️ Radar de Competências", fontsize=14, pad=20)
        ax.grid(True)
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico radar: {str(e)}")
        return None

# Upload de arquivo
st.header("📄 Upload do Currículo")
uploaded_file = st.file_uploader(
    "📎 Envie seu currículo em PDF", 
    type="pdf",
    help="Apenas arquivos PDF são aceitos"
)

# Validação de entrada
if not api_key and not uploaded_file:
    st.info("👋 **Bem-vindo!** Insira sua chave de API e faça upload de um currículo para começar.")
elif uploaded_file and not api_key:
    st.warning("⚠️ **Insira sua chave de API** para continuar com a análise.")
elif api_key and not uploaded_file:
    st.info("📤 **Faça upload de um currículo** em PDF para iniciar a análise.")

# Processamento principal
if uploaded_file and api_key:
    # Botão de análise
    if st.button("🔍 Analisar Currículo", type="primary", use_container_width=True):
        # Container para progresso
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Etapa 1: Configurar cliente
                status_text.text("🔧 Configurando cliente OpenAI...")
                progress_bar.progress(10)
                
                try:
                    client = OpenAI(api_key=api_key)
                except Exception as e:
                    st.error(f"❌ Erro ao configurar cliente OpenAI: {str(e)}")
                    st.info("Verifique se sua chave de API está correta.")
                    st.stop()
                
                # Etapa 2: Processar PDF
                status_text.text("📄 Processando arquivo PDF...")
                progress_bar.progress(25)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    pdf_path = temp_file.name

                # Etapa 3: Extrair texto
                status_text.text("📝 Extraindo texto do currículo...")
                progress_bar.progress(40)
                
                texto_curriculo = ""
                try:
                    doc = fitz.open(pdf_path)
                    for page_num, page in enumerate(doc):
                        texto_curriculo += page.get_text()
                        # Atualizar progresso para páginas
                        progress_bar.progress(40 + (page_num + 1) * 10 // len(doc))
                    doc.close()
                except Exception as e:
                    st.error(f"❌ Erro ao processar PDF: {str(e)}")
                    st.info("Verifique se o arquivo não está corrompido ou protegido por senha.")
                    st.stop()
                finally:
                    # Limpar arquivo temporário
                    try:
                        if os.path.exists(pdf_path):
                            os.unlink(pdf_path)
                    except:
                        pass

                if not texto_curriculo.strip():
                    st.error("❌ Não foi possível extrair texto do PDF. Verifique se o arquivo não está protegido.")
                    st.stop()

                # Etapa 4: Análise com IA
                status_text.text("🤖 Analisando com inteligência artificial...")
                progress_bar.progress(60)

                # Prompt otimizado
                prompt = f"""
Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. Analise o currículo abaixo.

**IMPORTANTE: Responda EXATAMENTE no formato especificado.**

**Parte 1 – Análise Quantitativa (JSON)**
Identifique as principais áreas de competência e atribua notas de 0 a 100:

[
  {{"Área": "Nome da Competência", "Pontuação": número}},
  {{"Área": "Outra Competência", "Pontuação": número}}
]

**Parte 2 – Análise Qualitativa**
- **Pontos Fortes:** principais qualidades identificadas
- **Pontos de Melhoria:** áreas que podem ser desenvolvidas
- **Sugestões:** recomendações práticas para o mercado financeiro

Currículo:
\"\"\"
{texto_curriculo[:4000]}  # Limitar texto para evitar tokens excessivos
\"\"\"
"""

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",  # Modelo mais estável e econômico
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=2500
                    )
                    resposta_completa = response.choices[0].message.content
                except Exception as api_error:
                    st.error(f"❌ Erro na API OpenAI: {str(api_error)}")
                    st.info("Possíveis soluções:\n- Verifique sua chave de API\n- Confirme se você tem créditos disponíveis\n- Tente novamente em alguns minutos")
                    st.stop()

                # Etapa 5: Processar resultados
                status_text.text("📊 Processando resultados...")
                progress_bar.progress(80)

                # Processar JSON
                dados_json = extrair_json_robusto(resposta_completa)
                
                if not dados_json:
                    st.error("❌ Erro: Não foi possível extrair os dados de competências.")
                    with st.expander("🔍 Ver resposta completa da IA"):
                        st.text(resposta_completa)
                    st.stop()
                
                # Validar e limpar dados
                dados_validos = []
                for item in dados_json:
                    if isinstance(item, dict) and "Área" in item and "Pontuação" in item:
                        try:
                            pontuacao = float(item["Pontuação"])
                            if 0 <= pontuacao <= 100:
                                dados_validos.append({
                                    "Área": str(item["Área"]).strip(),
                                    "Pontuação": pontuacao
                                })
                        except (ValueError, TypeError):
                            continue
                
                if not dados_validos:
                    st.error("❌ Nenhum dado válido encontrado na análise.")
                    st.stop()

                # Finalizar progresso
                status_text.text("✅ Análise concluída!")
                progress_bar.progress(100)
                
                # Limpar containers de progresso
                progress_container.empty()
                
                # Criar DataFrame
                df = pd.DataFrame(dados_validos)
                df = df.sort_values(by="Pontuação", ascending=False)  # Ordenar por pontuação
                
                st.success(f"✅ **Currículo analisado com sucesso:** `{uploaded_file.name}`")
                
                # === RESULTADOS ===
                
                # Tabela de competências
                st.markdown("### 📊 **Competências Identificadas**")
                
                # Colorir tabela baseado na pontuação
                def color_pontuacao(val):
                    if val >= 80:
                        return 'background-color: lightgreen'
                    elif val >= 60:
                        return 'background-color: lightyellow'
                    else:
                        return 'background-color: lightcoral'
                
                styled_df = df.style.applymap(color_pontuacao, subset=['Pontuação'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    pontuacao_media = round(df["Pontuação"].mean(), 1)
                    st.metric("📈 Pontuação Média", f"{pontuacao_media}%")
                
                with col2:
                    competencias_altas = len(df[df["Pontuação"] >= 80])
                    st.metric("🏆 Competências Altas (≥80%)", competencias_altas)
                
                with col3:
                    total_competencias = len(df)
                    st.metric("📝 Total de Competências", total_competencias)
                
                with col4:
                    pontuacao_maxima = df["Pontuação"].max()
                    st.metric("⭐ Maior Pontuação", f"{pontuacao_maxima}%")

                # Gráficos
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("### 📊 **Distribuição de Competências**")
                    
                    fig1, ax1 = plt.subplots(figsize=(10, 6))
                    colors = ['#2E8B57' if x >= 80 else '#DAA520' if x >= 60 else '#DC143C' for x in df["Pontuação"]]
                    
                    bars = ax1.barh(df["Área"], df["Pontuação"], color=colors)
                    ax1.set_xlabel("Pontuação (%)")
                    ax1.set_title("Competências por Área")
                    ax1.grid(axis='x', alpha=0.3)
                    
                    # Adicionar valores nas barras
                    for bar, valor in zip(bars, df["Pontuação"]):
                        ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                                f'{valor:.0f}%', va='center', fontsize=9)
                    
                    plt.tight_layout()
                    st.pyplot(fig1)
                
                with col_right:
                    st.markdown("### 🕸️ **Radar de Competências**")
                    fig_radar = criar_grafico_radar_seguro(df.head(8))  # Limitar a 8 competências
                    if fig_radar:
                        st.pyplot(fig_radar)
                    else:
                        st.info("Gráfico radar não disponível para este perfil.")

                # Distribuição por níveis
                st.markdown("### 📈 **Análise por Níveis**")
                
                df['Nível'] = pd.cut(
                    df['Pontuação'], 
                    bins=[-1, 59.9, 79.9, 100], 
                    labels=["🔴 Baixo (0-59%)", "🟡 Médio (60-79%)", "🟢 Alto (80-100%)"]
                )
                nivel_counts = df['Nível'].value_counts()
                
                col_a, col_b = st.columns([1, 1])
                
                with col_a:
                    st.dataframe(nivel_counts.reset_index(), use_container_width=True)
                
                with col_b:
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    colors_pie = ['#DC143C', '#DAA520', '#2E8B57']
                    wedges, texts, autotexts = ax2.pie(
                        nivel_counts.values, 
                        labels=nivel_counts.index,
                        colors=colors_pie,
                        autopct='%1.1f%%',
                        startangle=90
                    )
                    ax2.set_title("Distribuição por Níveis de Competência")
                    plt.tight_layout()
                    st.pyplot(fig2)

                # Análise textual
                st.markdown("### 📝 **Análise Qualitativa Detalhada**")
                
                # Extrair texto após JSON
                partes = resposta_completa.split("]")
                if len(partes) > 1:
                    texto_analise = partes[-1].strip()
                    if texto_analise:
                        st.markdown(texto_analise)
                    else:
                        st.info("Análise qualitativa não disponível nesta resposta.")
                else:
                    st.markdown(resposta_completa)

                # Download dos resultados
                st.markdown("### 💾 **Download dos Resultados**")
                
                csv_data = df.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Baixar dados em CSV",
                    data=csv_data,
                    file_name=f"analise_curriculo_{uploaded_file.name.replace('.pdf', '')}.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"❌ **Erro durante a análise:** {str(e)}")
                st.info("Tente novamente ou verifique se o arquivo está correto.")
                
                # Debug info
                with st.expander("🔧 Informações de debug"):
                    st.text(f"Erro: {type(e).__name__}")
                    st.text(f"Detalhes: {str(e)}")
                    st.text(f"Python: {sys.version}")

# Footer
st.markdown("---")
st.markdown("🚀 **InternReady** - Análise inteligente de currículos para o mercado financeiro")