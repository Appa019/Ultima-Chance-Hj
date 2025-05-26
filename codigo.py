# -*- coding: utf-8 -*-
"""Assistente de Analise InternReady - Streamlit App"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from math import pi
import json
import re
import tempfile
import os

# Imports com tratamento de erro específico
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    OPENAI_AVAILABLE = False
    st.error(f"❌ Erro ao importar OpenAI: {str(e)}")
    st.info("💡 Verifique se o arquivo requirements.txt está na raiz do repositório")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError as e:
    PYMUPDF_AVAILABLE = False
    st.error(f"❌ Erro ao importar PyMuPDF: {str(e)}")
    st.info("💡 Certifique-se de que 'pymupdf==1.23.8' está no requirements.txt")

# Configurações visuais do Matplotlib
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 12

# Configuração da página
st.set_page_config(page_title="Assistente de Análise InternReady", page_icon="🚀", layout="wide")
st.title("🚀 Assistente de Análise InternReady")
st.markdown("### Análise de currículo especializada para o setor financeiro")

# Status das dependências (debug)
if not OPENAI_AVAILABLE or not PYMUPDF_AVAILABLE:
    st.warning("⚠️ Algumas dependências não estão disponíveis. Verifique o requirements.txt")
    with st.expander("🔍 Status das Dependências"):
        st.write(f"OpenAI: {'✅ OK' if OPENAI_AVAILABLE else '❌ Erro'}")
        st.write(f"PyMuPDF: {'✅ OK' if PYMUPDF_AVAILABLE else '❌ Erro'}")
        st.code("""
# Conteúdo esperado do requirements.txt:
streamlit==1.32.0
openai==1.12.0
pymupdf==1.23.8
pandas>=1.5.0
matplotlib>=3.5.0
        """)
    if not OPENAI_AVAILABLE or not PYMUPDF_AVAILABLE:
        st.stop()

# Sidebar com configurações
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("🔑 Cole sua *Chave InternReady*:", type="password")
    st.markdown("---")
    st.markdown("### Como usar:")
    st.markdown("1. Insira sua chave de API\n2. Faça upload do currículo em PDF\n3. Clique em 'Analisar Currículo'")

def extrair_json_robusto(texto):
    """Extrai JSON de forma mais robusta do texto da resposta"""
    try:
        # Tenta encontrar JSON entre colchetes
        match = re.search(r"\[(.*?)\]", texto, re.DOTALL)
        if match:
            json_str = "[" + match.group(1) + "]"
            return json.loads(json_str)
    except json.JSONDecodeError:
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
    except:
        pass
    
    return None

def criar_grafico_radar_seguro(df):
    """Cria gráfico radar com verificações de segurança"""
    if len(df) < 3:
        st.warning("⚠️ Necessário pelo menos 3 competências para gráfico radar")
        return None
    
    labels = df["Área"].tolist()
    values = df["Pontuação"].tolist()
    
    # Adiciona o primeiro ponto no final para fechar o polígono
    labels += [labels[0]]
    values += [values[0]]
    
    angles = [n / float(len(labels)-1) * 2 * pi for n in range(len(labels))]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels[:-1])
    ax.set_ylim(0, 100)
    ax.set_title("🕸️ Radar de Competências")
    ax.grid(True)
    
    return fig

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
            texto_curriculo = ""
            try:
                doc = fitz.open(pdf_path)
                for page in doc:
                    texto_curriculo += page.get_text()
                doc.close()
            except Exception as e:
                st.error(f"❌ Erro ao processar PDF: {str(e)}")
                continue
            finally:
                # Limpar arquivo temporário de forma segura
                try:
                    if os.path.exists(pdf_path):
                        os.unlink(pdf_path)
                except:
                    pass  # Ignora erros de limpeza

            if not texto_curriculo.strip():
                st.error("❌ Não foi possível extrair texto do PDF. Verifique se o arquivo não está protegido.")
                continue

            st.success(f"✅ Currículo carregado com sucesso: `{uploaded_file.name}`")

            # Prompt melhorado com instruções mais claras
            prompt = f"""
Você é um consultor de carreira especializado em perfis voltados para o setor financeiro. Sua tarefa é analisar o currículo abaixo com base em competências valorizadas nesse mercado.

**IMPORTANTE: Retorne EXATAMENTE no formato especificado abaixo.**

**Parte 1 – Análise Quantitativa**
- Identifique as principais **áreas de competência profissional** (ex: Finanças, Economia, Risco, Análise de Dados, Excel, Programação, Comunicação, etc.).
- Para cada área, atribua uma nota de **0 a 100**, com base nas evidências fornecidas no texto como um especialista em recursos humanos com muitos anos de prática. **Não infira habilidades não mencionadas.**
- A resposta deve estar EXATAMENTE no formato JSON:

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

            # Chamar API OpenAI com tratamento de erro
            with st.spinner("⏳ Analisando com agente de IA..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=3000
                    )
                    resposta_completa = response.choices[0].message.content
                except Exception as api_error:
                    st.error(f"❌ Erro na API OpenAI: {str(api_error)}")
                    st.info("Verifique se sua chave de API está correta e se você tem créditos disponíveis.")
                    continue

            st.success("✅ Análise concluída.")

            # Processar JSON de forma robusta
            dados_json = extrair_json_robusto(resposta_completa)
            
            if not dados_json:
                st.error("❌ Erro: Não foi possível extrair os dados de competências.")
                st.text("Resposta da IA:")
                st.text(resposta_completa)
                continue
            
            # Validar estrutura dos dados
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
                st.error("❌ Nenhum dado válido encontrado na resposta.")
                continue
                
            df = pd.DataFrame(dados_validos)
            df = df.sort_values(by="Pontuação", ascending=True)
            
            # Tabela de competências
            st.markdown("### 📌 Tabela de Competências:")
            st.dataframe(df, use_container_width=True)

            # Mínimos para área financeira
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
            afinidade_financas = round(afinidade_df["Pontuação"].mean(), 1) if not afinidade_df.empty else 0

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
            cores = df["Status"].map({"✔️ OK": "green", "❌ Abaixo do ideal": "red"})
            ax2.barh(df["Área"], df["Pontuação"], color=cores)
            ax2.set_xlabel("Pontuação (0 a 100)")
            ax2.set_title("📊 Competências vs Mínimos Recomendados (Finanças)")
            ax2.grid(True, axis='x')
            plt.tight_layout()
            st.pyplot(fig2)

            # Gráfico 3: Dispersão de Pontuações
            st.markdown("### 📍 Dispersão de Pontuações por Área")
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            x_pos = range(len(df))
            ax3.scatter(x_pos, df["Pontuação"], s=100, label='Pontuação Atual')
            ax3.scatter(x_pos, df["Mínimo Ideal"], marker="x", color="orange", s=100, label='Mínimo Ideal')
            ax3.axhline(50, color='gray', linestyle='--', label='Mínimo Geral')
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels(df["Área"], rotation=45, ha='right')
            ax3.set_title("📍 Dispersão de Pontuações por Área")
            ax3.set_ylabel("Pontuação")
            ax3.legend()
            plt.tight_layout()
            st.pyplot(fig3)

            # Gráfico 4: Distribuição por Nível
            st.markdown("### 📘 Distribuição de Competências por Nível")
            df['Nível'] = pd.cut(df['Pontuação'], bins=[-1, 49, 74, 100], labels=["Baixa", "Média", "Alta"])
            nivel_counts = df['Nível'].value_counts().sort_index()
            
            if not nivel_counts.empty:
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
            fig_radar = criar_grafico_radar_seguro(df)
            if fig_radar:
                st.pyplot(fig_radar)

            # Análise textual
            st.markdown("### 📝 Análise Textual:")
            # Procura pela análise qualitativa após o JSON
            partes = resposta_completa.split("]")
            if len(partes) > 1:
                texto_analise = partes[-1].strip()
                if texto_analise:
                    st.markdown(texto_analise)
                else:
                    st.info("Análise qualitativa não disponível.")
            else:
                # Se não houver JSON, mostra a resposta completa
                st.markdown(resposta_completa)

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")
            st.info("Verifique se sua chave de API está correta e se você tem créditos disponíveis.")
            import traceback
            st.code(traceback.format_exc())

elif uploaded_file and not api_key:
    st.warning("⚠️ Insira sua chave de API para continuar.")
elif api_key and not uploaded_file:
    st.info("📤 Faça upload de um currículo em PDF para iniciar.")
else:
    st.info("👋 Bem-vindo! Insira sua chave de API e faça upload de um currículo para começar.")
