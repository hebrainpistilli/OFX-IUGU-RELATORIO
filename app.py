import streamlit as st
import pandas as pd
import re
import io

# Configuração da página
st.set_page_config(page_title="Listagem de OFX", page_icon="✏️", layout="centered")

# Estilo CSS para o novo design (Dark Mode com acentos específicos)
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
    
    /* Estilização do Upload */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #161b22;
        border: 1px dashed #30363d;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# Header conforme a nova imagem
st.markdown("""
    <div class="title-container">
        <span style="font-size: 40px;">✏️</span>
        <span class="title-text">Listagem de OFX</span>
    </div>
    <p class="subtitle-text">
        Faça o upload do seu arquivo <span class="ofx-green">.ofx</span> limpo para iniciar o processo de listagem.
    </p>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["ofx"])

if uploaded_file is not None:
    try:
        # Lê o conteúdo ignorando erros de caracteres especiais
        raw_content = uploaded_file.read().decode("utf-8", errors="ignore")
        
        # Expressão Regular para extrair blocos de transação de forma robusta
        # Pega o valor (TRNAMT), a data (DTPOSTED) e a descrição (MEMO)
        transactions = re.findall(r"<STMTTRN>.*?<TRNAMT>(.*?)<.*?<DTPOSTED>(.*?)<.*?<MEMO>(.*?)<", raw_content, re.DOTALL)
        
        extracted_data = []
        
        for amt, dt, memo in transactions:
            amount = float(amt.strip())
            memo_text = memo.strip()
            
            # Filtro solicitado: apenas CRÉDITOS que contenham '#'
            if '#' in memo_text and amount > 0:
                # Extrai o código após o #
                codigo = memo_text.split('#')[-1].strip()
                
                # Formata a data (YYYYMMDD -> DD/MM/YYYY)
                data_limpa = dt.strip()[:8]
                data_formatada = f"{data_limpa[6:8]}/{data_limpa[4:6]}/{data_limpa[0:4]}"
                
                extracted_data.append({
                    "Código da Fatura": codigo,
                    "Valor (R$)": amount,
                    "Data de Pagamento": data_formatada
                })
        
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            
            st.write("### Itens Encontrados")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Gerar Excel em memória
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Faturas')
            
            st.download_button(
                label="📥 Baixar Lista em Excel",
                data=output.getvalue(),
                file_name="Listagem_Faturas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Nenhuma fatura com '#' foi encontrada. Verifique se o arquivo OFX possui créditos com esse padrão.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar: {e}")
