import streamlit as st
from modules.auth import autenticar_usuario
from modules.sharepoint_utils import baixar_excel_sharepoint
from modules.data_preprocessing import preparar_dataframe
from modules.dashboard_components import mostrar_kpis
from modules.charts import grafico_status, grafico_reparos_por_placa
from modules.styles import aplicar_estilos

st.set_page_config(page_title="Dashboard Reparos", page_icon="🛠️", layout="wide")

authenticator = autenticar_usuario()

if st.session_state.get('authentication_status'):
    authenticator.logout("Sair", location='sidebar', key="logout_button")

    df, file = baixar_excel_sharepoint(st.secrets)
    df = preparar_dataframe(df)
    aplicar_estilos()

    st.sidebar.image("assets/logo-colorida.png", use_container_width=True)
    st.title("🛠️ Dashboard de Reparos")
    mostrar_kpis(df)

    st.plotly_chart(grafico_status(df), use_container_width=True)
    st.plotly_chart(grafico_reparos_por_placa(df), use_container_width=True)

    st.success("🚀 Dashboard carregado com sucesso!")

elif st.session_state.get('authentication_status') is False:
    st.error("Usuário ou senha incorretos")
else:
    st.warning("Por favor, insira suas credenciais")
