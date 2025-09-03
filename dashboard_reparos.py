import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.runtime.auth.user_credential import UserCredential
import os
from io import BytesIO
from dotenv import load_dotenv

# =========================
# Configuração da Página
# =========================
st.set_page_config(
    page_title="Dashboard Reparos",
    page_icon="🛠️",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Título principal */
    .css-10trblm {
        font-size: 36px !important;
        font-weight: bold;
        color: #2E86C1;
    }
    /* Cards de KPI */
    .metric-card {
        background: linear-gradient(135deg, #2E86C1, #5DADE2);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
        font-weight: bold;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Login Sharepoint
# =========================
# Carregar .env
load_dotenv()

USERNAME = os.getenv("SP_USERNAME")
PASSWORD = os.getenv("SP_PASSWORD")
SITE_URL = "https://paivaenergiapaivaenergia150.sharepoint.com/sites/paivaenergiaadministrativo"
FILE_URL = "/sites/paivaenergiaadministrativo/Engenharia/Reparos/Reparos Paiva.xlsx"

# Conectar ao SharePoint
ctx = ClientContext(SITE_URL).with_credentials(UserCredential(USERNAME, PASSWORD))

# Baixar arquivo do SharePoint
file = ctx.web.get_file_by_server_relative_url(FILE_URL)
ctx.load(file)
ctx.execute_query()

# Ler conteúdo em memória
content = file.read()
df = pd.read_excel(BytesIO(content), sheet_name="Reparos Paiva")

print(df.head())

# =========================
# Carregar os dados
# =========================
# df = pd.read_excel("Reparos Paiva.xlsx", sheet_name="Reparos Paiva")

# Selecionar colunas principais
df = df[[
    "SEQ", "PLACA", "VERSÃO", "SERIAL", "Prioridade",
    "DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO", "CLIENTE", "Status"
]].copy()

# Converter datas
for col in ["DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Criar status
# df["STATUS"] = df["DATA DE REPARO"].apply(
#     lambda x: "Concluído" if pd.notnull(x) else "Em andamento"
# )

# Calcular dias de reparo
df["DIAS_REPARO"] = (df["DATA DE REPARO"] - df["DATA DE CHEGADA"]).dt.days

# =========================
# Sidebar - Filtros
# =========================
# =========================
# Sidebar - Filtros
# =========================
st.sidebar.image(
    "assets/logo-colorida.png",
    use_container_width=True
)

st.sidebar.title("🔎 Filtros")

# --- Filtro Cliente ---
clientes = df["CLIENTE"].dropna().unique()
cliente_sel = st.sidebar.multiselect("Cliente", options=clientes)

df_cliente = df[df["CLIENTE"].isin(cliente_sel)] if cliente_sel else df

# --- Filtro Placa (dependente de Cliente) ---
placas = df_cliente["PLACA"].dropna().unique()
placa_sel = st.sidebar.multiselect("Placa", options=placas)

df_placa = df_cliente[df_cliente["PLACA"].isin(placa_sel)] if placa_sel else df_cliente

# --- Filtro Serial (dependente de Cliente + Placa) ---
seriais = df_placa["SERIAL"].dropna().unique()
serial_sel = st.sidebar.multiselect("Serial", options=seriais)

df_serial = df_placa[df_placa["SERIAL"].isin(serial_sel)] if serial_sel else df_placa

# --- Filtro Prioridade (dependente dos anteriores) ---
prioridades = df_serial["Prioridade"].dropna().unique()
prioridade_sel = st.sidebar.multiselect("Prioridade", options=prioridades)

df_prioridade = df_serial[df_serial["Prioridade"].isin(prioridade_sel)] if prioridade_sel else df_serial

# --- Filtro Status (dependente dos anteriores) ---
status_opts = df_prioridade["Status"].dropna().unique()
status_sel = st.sidebar.multiselect("Status", options=status_opts)

df_filtered = df_prioridade[df_prioridade["Status"].isin(status_sel)] if status_sel else df_prioridade

# --- Filtro Data ---
date_range = st.sidebar.date_input(
    "Período de chegada",
    value=[df["DATA DE CHEGADA"].min().date(), pd.Timestamp.today().date()],
    help="Selecione o intervalo de datas"
)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    data_inicio, data_fim = date_range
    df_filtered = df_filtered[
        (df_filtered["DATA DE CHEGADA"].dt.date >= data_inicio) &
        (df_filtered["DATA DE CHEGADA"].dt.date <= data_fim)
    ]
else:
    st.info("🗓️ Selecione a data inicial e final para aplicar o filtro.")


# =========================
# KPIs
# =========================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"<div class='metric-card'>📦<br>Total de placas<br>{len(df_filtered)}</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'>✅<br>Concluídos<br>{(df_filtered['Status']=='Reparada').sum()}</div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'>↩️<br>Retorno<br>{(df_filtered['Status']=='Retorno').sum()}</div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card'>🔄<br>Em andamento<br>{(df_filtered['Status']=='Analisando').sum()}</div>", unsafe_allow_html=True)
with col5:
    st.markdown(f"<div class='metric-card'>⏱️<br>Tempo Médio<br>{round(df_filtered['DIAS_REPARO'].mean(skipna=True),1)} dias</div>", unsafe_allow_html=True)

st.markdown("---")

# =========================
# Gráficos
# =========================
aba = st.tabs(["📊 Visão Geral", "📈 Linha do Tempo", "🛠️ Detalhamento"])

with aba[0]:
    col1, col2 = st.columns(2)

    with col1:
        fig_status = px.pie(df_filtered, names="Status", title="Distribuição de Status", hole=0.4,
                            color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig_status, use_container_width=True)

    with col2:
        fig_placa = px.bar(
            df_filtered.groupby("PLACA").size().reset_index(name="Quantidade"),
            x="PLACA", y="Quantidade", title="Reparos por Placa",
            color="Quantidade", color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_placa, use_container_width=True)

with aba[1]:
    df_timeline = df_filtered.copy()
    df_timeline["Mes_Ano_Chegada"] = df_timeline["DATA DE CHEGADA"].dt.to_period("M").astype(str)
    df_timeline["Mes_Ano_Reparo"] = df_timeline["DATA DE REPARO"].dt.to_period("M").astype(str)

    chegadas = df_timeline.groupby("Mes_Ano_Chegada").size().reset_index(name="Chegadas")
    reparos = df_timeline.groupby("Mes_Ano_Reparo").size().reset_index(name="Reparos")

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(x=chegadas["Mes_Ano_Chegada"], y=chegadas["Chegadas"], mode="lines+markers", name="Chegadas"))
    fig_timeline.add_trace(go.Scatter(x=reparos["Mes_Ano_Reparo"], y=reparos["Reparos"], mode="lines+markers", name="Reparos"))
    fig_timeline.update_layout(title="Linha do Tempo - Chegadas vs Reparos", xaxis_title="Mês/Ano", yaxis_title="Quantidade")

    st.plotly_chart(fig_timeline, use_container_width=True)
    st.subheader("📈 Linha do Tempo - Fluxo por Serial")

    df_timeline = df_filtered.copy()

    # Criar dataset no formato Gantt: cada SERIAL vira uma "tarefa"
    df_gantt = df_timeline[["SERIAL", "PLACA", "DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO"]].copy()

    # Criar colunas para início e fim do período de reparo
    df_gantt = df_gantt.rename(columns={
        "DATA DE CHEGADA": "Inicio",
        "DATA DE REPARO": "Fim"
    })

    # Caso não tenha reparo, usa previsão de entrega como "Fim" (se existir)
    df_gantt["Fim"] = df_gantt["Fim"].fillna(df_gantt["ENTREGA/PREVISÃO"])

    # Tirar registros sem data válida
    df_gantt = df_gantt.dropna(subset=["Inicio", "Fim"])

    # Construir gráfico de linha do tempo (Gantt)
    fig_timeline = px.timeline(
        df_gantt,
        x_start="Inicio",
        x_end="Fim",
        y="SERIAL",          # <<< agora é por SERIAL
        color="PLACA",       # cor pode ser por placa (ou trocar por cliente/status, se preferir)
        hover_data=["PLACA"], # mostra a placa no hover
        title="Linha do Tempo por Serial"
    )

    # Ajustar layout
    fig_timeline.update_yaxes(autorange="reversed")  # Serials de cima para baixo
    fig_timeline.update_layout(
        xaxis_title="Data",
        yaxis_title="Serial",
        showlegend=True
    )

    st.plotly_chart(fig_timeline, use_container_width=True)


with aba[2]:
    st.subheader("📋 Tabela Detalhada")

    # Criar cópia apenas para exibição, com datas formatadas
    df_display = df_filtered.copy()
    for col in ["DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO"]:
        df_display[col] = df_display[col].dt.strftime("%d/%m/%Y")

    st.dataframe(df_display, use_container_width=True)

    st.download_button(
        label="📥 Exportar dados filtrados",
        data=df_filtered.to_csv(index=False).encode("utf-8"),
        file_name="reparos_filtrados.csv",
        mime="text/csv"
    )
