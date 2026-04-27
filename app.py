import streamlit as st
import pandas as pd
import re
import io

# Configuração da página
st.set_page_config(page_title="Listagem de OFX", page_icon="✏️", layout="centered")

# Estilo CSS para o design Dark Mode (inspirado na imagem enviada)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .title-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 5px;
    }
    .title-text {
        color: #ffffff;
        font-size: 42px;
        font-weight: 800;
        font-family: 'Source Sans Pro', sans-serif;
    }
    .subtitle-text {
        color: #a3a8b4;
        font-size: 18px;
        margin-bottom: 30px;
    }
    .ofx-green { color: #00c853; font-weight: bold; }
    
    /* Estilização da área de Upload */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #161b22;
        border: 1px dashed #30363d;
        border-radius: 8px;
    }
    
    /* Estilo do botão de download */
    .stDownloadButton>button {
        background-color: #1f2937;
        color: white;
        border: 1px solid #374151;
        width: 100%;
        transition: 0.3s;
    }
    .stDownloadButton>button:hover {
        border-color: #00c853;
        color: #00c853;
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho da página
st.markdown("""
    <div class="title-container">
        <span style="font-size: 40px;">✏️</span>
        <span class="title-text">Listagem de OFX</span>
    </div>
    <p class="subtitle-text">
        Faça o upload do seu arquivo <span class="ofx-green">.ofx</span> limpo para iniciar o processo de listagem.
    </p>
    """, unsafe_allow_html=True)

# Componente de Upload
uploaded_file = st.file_uploader("", type=["ofx"])

if uploaded_file is not None:
    try:
        # Lê o conteúdo ignorando erros de caracteres especiais (importante para arquivos OFX brasileiros)
        raw_content = uploaded_file.read().decode("utf-8", errors="ignore")
        
        # Expressão Regular para extrair os campos principais de cada transação <STMTTRN>
        # Pega: Valor (TRNAMT), Data (DTPOSTED) e Descrição (MEMO)
        transactions = re.findall(r"<STMTTRN>.*?<TRNAMT>(.*?)<.*?<DTPOSTED>(.*?)<.*?<MEMO>(.*?)<", raw_content, re.DOTALL)
        
        extracted_data = []
        
        for amt, dt, memo in transactions:
            # Tratamento do Valor: Remove espaços e troca vírgula por ponto para conversão float
            clean_amt = amt.strip().replace(',', '.')
            
            try:
                amount = float(clean_amt)
            except ValueError:
                continue # Pula se o valor não for um número válido
                
            memo_text = memo.strip()
            
            # Regra de negócio: Apenas CRÉDITOS (positivo) que contenham o identificador '#'
            if '#' in memo_text and amount > 0:
                # Extrai o código que vem após o símbolo '#'
                codigo = memo_text.split('#')[-1].strip()
                
                # Formata a data de YYYYMMDD para DD/MM/YYYY
                data_limpa = dt.strip()[:8]
                data_formatada = f"{data_limpa[6:8]}/{data_limpa[4:6]}/{data_limpa[0:4]}"
                
                extracted_data.append({
                    "Código da Fatura": codigo,
                    "Valor (R$)": amount,
                    "Data de Pagamento": data_formatada
                })
        
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            
            st.divider()
            st.write("### Itens Encontrados")
            
            # Exibe a tabela formatada
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Preparação do arquivo Excel para Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Faturas_Listadas')
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Baixar Lista em Excel",
                data=output.getvalue(),
                file_name="Listagem_Faturas_Processada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhuma fatura com o padrão '#' foi identificada neste arquivo.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
