import streamlit as st
import pandas as pd
from ofxparse import OfxParser
import io

# Configuração da página e Estilo Dark
st.set_page_config(page_title="Padronização de OFX", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #ffffff; font-family: 'sans-serif'; font-weight: 700; }
    p { color: #a3a8b4; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #262730;
        color: white;
        border: 1px solid #4f535e;
    }
    .stButton>button:hover { border-color: #00ff00; color: #00ff00; }
    /* Estilizando a área de upload */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #161b22;
        border: 1px dashed #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# Header inspirado na imagem
st.markdown("# 📝 Tratamento e Padronização de OFX")
st.markdown("Faça o upload do seu arquivo <span style='color: #4CAF50; font-weight: bold;'>.ofx</span> para iniciar o processo de limpeza.", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["ofx"])

if uploaded_file is not None:
    try:
        # Parsing do OFX
        ofx = OfxParser.parse(uploaded_file)
        data = []

        for account in ofx.accounts:
            for tx in account.statement.transactions:
                # Filtro: Se tem '#' no memo e é um crédito (valor > 0)
                if '#' in tx.memo and tx.amount > 0:
                    # Extrai o código após o #
                    codigo_fatura = tx.memo.split('#')[-1].strip()
                    
                    data.append({
                        "Código da Fatura": codigo_fatura,
                        "Valor (R$)": float(tx.amount),
                        "Data de Pagamento": tx.date.strftime("%d/%m/%Y"),
                        "Descrição Original": tx.memo
                    })

        if data:
            df = pd.DataFrame(data)
            
            st.divider()
            st.subheader("Visualização dos Dados")
            st.dataframe(df, use_container_width=True)

            # Preparação do Excel em memória
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Faturas')
            
            st.markdown("---")
            st.download_button(
                label="📥 Clique aqui para baixar o Excel formatado",
                data=output.getvalue(),
                file_name=f"OFX_Tratado_{df['Data de Pagamento'].iloc[0].replace('/','-')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhuma fatura com o padrão '#' foi encontrada neste arquivo.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
