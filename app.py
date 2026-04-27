import streamlit as st
import pandas as pd
import re
import io

# Configuração da página e Design
st.set_page_config(page_title="Listagem de OFX", page_icon="✏️", layout="centered")

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
    section[data-testid="stFileUploadDropzone"] {
        background-color: #161b22;
        border: 1px dashed #30363d;
        border-radius: 8px;
    }
    .stDownloadButton>button {
        background-color: #1f2937;
        color: white;
        border: 1px solid #374151;
        width: 100%;
    }
    .stDownloadButton>button:hover {
        border-color: #00c853;
        color: #00c853;
    }
    </style>
    """, unsafe_allow_html=True)

# Título conforme o design solicitado
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
        # 1. Leitura resiliente (resolve erro de caracteres especiais)
        raw_content = uploaded_file.read().decode("utf-8", errors="ignore")
        
        # 2. Extração via Regex (mais seguro que parsers XML para OFX customizado)
        # Busca Valor (TRNAMT), Data (DTPOSTED) e Descrição (MEMO)
        transactions = re.findall(r"<STMTTRN>.*?<TRNAMT>(.*?)<.*?<DTPOSTED>(.*?)<.*?<MEMO>(.*?)<", raw_content, re.DOTALL)
        
        extracted_data = []
        
        for amt, dt, memo in transactions:
            # 3. Tratamento de Valor (resolve erro: could not convert string to float: '179,38')
            clean_amt = amt.strip().replace(',', '.')
            try:
                val = float(clean_amt)
            except:
                continue

            memo_text = memo.strip()
            
            # 4. Filtro: Apenas Créditos que possuem '#'
            if '#' in memo_text and val > 0:
                # Extrai o código após o #
                id_fatura = memo_text.split('#')[-1].strip()
                
                # Formata a data YYYYMMDD -> DD/MM/YYYY
                d = dt.strip()[:8]
                dt_fmt = f"{d[6:8]}/{d[4:6]}/{d[0:4]}"
                
                extracted_data.append({
                    "Código da Fatura": id_fatura,
                    "Valor (R$)": val,
                    "Data de Pagamento": dt_fmt
                })
        
        # 5. Exibição e Exportação
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            st.divider()
            st.write("### Itens Encontrados")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Gerar Excel em memória
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Listagem')
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Baixar Lista em Excel",
                data=output.getvalue(),
                file_name="Listagem_Faturas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            # Mensagem de alerta se não encontrar o padrão (conforme imagem enviada) 
            st.warning("Nenhuma fatura com o padrão '#' foi identificada neste arquivo.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar: {e}")
