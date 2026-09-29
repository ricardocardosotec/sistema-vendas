import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Gestão de Vendas", layout="wide")

# 1. Ligação ao Google Sheets
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # As credenciais são lidas com segurança das configurações do Streamlit Cloud
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("vendas_db").sheet1

try:
    sheet = conectar_google_sheets()
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
except Exception as e:
    st.error("Erro ao ligar à base de dados. Verifique as credenciais.")
    df = pd.DataFrame()

st.title("📊 Painel de Gestão de Vendas e Comissões")

# 2. Barra Lateral: Formulário para Registar Venda
st.sidebar.header("📝 Nova Venda")
with st.sidebar.form("form_venda", clear_on_submit=True):
    data_venda = st.date_input("Data da Venda", datetime.today())
    fornecedor = st.text_input("Fornecedor")
    empresa = st.text_input("Empresa Cliente")
    valor = st.number_input("Valor da Venda (R$)", min_value=0.0, format="%.2f")
    comissao_pct = st.number_input("Comissão (%)", value=5.0, step=0.5)
    prazo = st.selectbox("Prazo", ["À Vista", "15 dias", "30 dias", "45 dias", "60 dias", "90 dias"])
    status = st.selectbox("Status", ["Não Pago", "Pago"])
    
    btn_salvar = st.form_submit_button("💾 Salvar Venda")

if btn_salvar:
    if fornecedor and empresa and valor > 0:
        # Calcular vencimento
        dias = 0 if "À Vista" in prazo else int(''.join(filter(str.isdigit, prazo)) or 30)
        vencimento = data_venda + timedelta(days=dias)
        comissao_val = round(valor * (comissao_pct / 100.0), 2)
        
        nova_linha = [
            data_venda.strftime("%Y-%m-%d"),
            vencimento.strftime("%Y-%m-%d"),
            fornecedor,
            empresa,
            valor,
            comissao_pct,
            comissao_val,
            prazo,
            status
        ]
        
        sheet.append_row(nova_linha)
        st.sidebar.success("Venda registada com sucesso!")
        st.rerun()
    else:
        st.sidebar.warning("Preencha todos os campos obrigatórios!")

# 3. Painel Principal: KPIs e Tabela
if not df.empty:
    # Conversão de colunas
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["Comissao_Val"] = pd.to_numeric(df["Comissao_Val"], errors="coerce").fillna(0)
    
    # Cards de Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Vendido", f"R$ {df['Valor'].sum():,.2f}")
    col2.metric("Recebido", f"R$ {df[df['Status'] == 'Pago']['Valor'].sum():,.2f}")
    col3.metric("A Receber", f"R$ {df[df['Status'] == 'Não Pago']['Valor'].sum():,.2f}")
    col4.metric("Total Comissões", f"R$ {df['Comissao_Val'].sum():,.2f}")

    st.markdown("---")
    st.subheader("📋 Registos de Vendas")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nenhuma venda registada até ao momento.")
