import os
import copy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit_authenticator as stauth
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential
from io import BytesIO
from urllib.parse import quote
from dotenv import load_dotenv

# =========================
# Carregar variáveis de ambiente locais
# =========================
load_dotenv()

# =========================
# Configuração de autenticação
# =========================
def get_credentials():
    """
    Retorna o dicionário de credenciais e cookie config
    Funciona tanto no Streamlit Cloud quanto local.
    """
    try:
        # Tenta usar st.secrets
        creds = {
            "usernames": {
                username: {
                    "name": f"{info['first_name']} {info['last_name']}",
                    "email": info['email'],
                    "password": info['password'],
                    "role": info['role']
                }
                for username, info in st.secrets["credentials"]["usernames"].items()
            }
        }
        cookie_conf = st.secrets['cookie']
        return creds, cookie_conf
    except (AttributeError, KeyError, RuntimeError, st.errors.StreamlitSecretNotFoundError):
        # Fallback local
        creds = {
            "usernames": {
                os.getenv("USERNAME_LOCAL", "admin"): {
                    "name": os.getenv("NAME_LOCAL", "Admin User"),
                    "email": os.getenv("EMAIL_LOCAL", "admin@email.com"),
                    "password": os.getenv("PASSWORD_LOCAL", "1234"),
                    "role": os.getenv("ROLE_LOCAL", "PAIVA")
                },
                os.getenv("USERNAME_LOCAL2", "cpfl"): {
                    "name": os.getenv("NAME_LOCAL2", "Cliente 1"),
                    "email": os.getenv("EMAIL_LOCAL2", "cliente1@email.com"),
                    "password": os.getenv("PASSWORD_LOCAL2", "1234"),
                    "role": os.getenv("ROLE_LOCAL2", "CPFL")
                }
            }
        }
        cookie_conf = {
            "name": os.getenv("COOKIE_NAME", "streamlit_dashboard"),
            "key": os.getenv("COOKIE_KEY", "123456"),
            "expiry_days": int(os.getenv("COOKIE_EXPIRY_DAYS", 30))
        }
        return creds, cookie_conf

credentials_dict, cookie_config = get_credentials()

authenticator = stauth.Authenticate(
    credentials_dict,
    cookie_config['name'],
    cookie_config['key'],
    cookie_config['expiry_days']
)

# =========================
# Login seguro
# =========================
try:
    authenticator.login()
except Exception as e:
    st.error(e)

# =========================
# Verifica status de autenticação
# =========================
if st.session_state.get('authentication_status'):
    st.sidebar.success(f"Bem-vindo, {st.session_state.get('name')} 👋")
    authenticator.logout("Sair", location='sidebar', key="logout_button")

    usuario_logado = st.session_state.get('username')
    cliente_atual = credentials_dict["usernames"][usuario_logado].get("role")

    # =========================
    # Configuração da Página
    # =========================
    st.set_page_config(
        page_title="Dashboard Reparos",
        page_icon="🛠️",
        layout="wide"
    )

    # =========================
    # Login SharePoint
    # =========================
    def get_sharepoint_secrets():
        try:
            sp = st.secrets["sharepoint"]
            return sp["TENANT_ID"], sp["CLIENT_ID"], sp["CLIENT_SECRET"], sp["SITE_URL"], sp["FILE_URL"]
        except (AttributeError, KeyError, RuntimeError, st.errors.StreamlitSecretNotFoundError):
            return (
                os.getenv("TENANT_ID"),
                os.getenv("CLIENT_ID"),
                os.getenv("CLIENT_SECRET"),
                os.getenv("SITE_URL"),
                os.getenv("FILE_URL")
            )

    tenant_id, client_id, client_secret, SITE_URL, FILE_URL = get_sharepoint_secrets()

    credentials = ClientCredential(client_id, client_secret)
    ctx = ClientContext(SITE_URL).with_credentials(credentials)

    # =========================
    # Baixar arquivo do SharePoint
    # =========================
    file = ctx.web.get_file_by_server_relative_url(FILE_URL)
    file_content = BytesIO()
    file.download(file_content).execute_query()
    file_content.seek(0)

    # Ler Excel diretamente da memória
    df = pd.read_excel(file_content, sheet_name="Reparos Paiva")
    # Remover espaços da coluna SERIAL
    df["SERIAL"] = df["SERIAL"].astype(str).str.replace(r"\s+", "", regex=True) 

    # =========================
    # Preparar DataFrame
    # =========================
    df = df[[
        "SEQ", "PLACA", "VERSÃO", "SERIAL", "Prioridade",
        "DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO",
        "CLIENTE", "LOCAL", "Status", "FOLLOW-UP","GARANTIA", 
        "Entrega", "BM", "VALOR", "LINK RELATORIO"
    ]].copy()
    
    #------ Tratar link relatório

    #------ Abaixo é realizado o tratamento das datas --------
    for col in ["DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO", "GARANTIA"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["GARANTIA"] = df["GARANTIA"].dt.strftime("%d/%m/%Y")

    role_usuario = cliente_atual

    # =========================
    # Dashboard e filtros
    # =========================
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #2E86C1, #5DADE2);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
        font-weight: bold;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    .font_negrit{ font-weight: bold }
    </style>
    """, unsafe_allow_html=True)

    # Data de atualização do arquivo
    file_info = file.listItemAllFields.get().execute_query()
    last_modified = file_info.properties.get("Modified")
    last_modified_str = pd.to_datetime(last_modified).strftime("%d/%m/%Y %H:%M")

    # =========================
    # Sidebar - Filtros
    # =========================
    st.sidebar.image("assets/logo-colorida.png", use_container_width=True)
    st.sidebar.title("🔎 Filtros")

    # 🔹 Filtro de cliente para role PAIVA
    if role_usuario == "PAIVA":
        todos_clientes = df["CLIENTE"].dropna().unique()
        todos_clientes.sort()
        cliente_sel = st.sidebar.multiselect(
            "Cliente",
            options=todos_clientes,
            default=todos_clientes
        )
        df_cliente = df[df["CLIENTE"].isin(cliente_sel)]
    else:
        df_cliente = df[df["CLIENTE"].str.strip().eq(role_usuario)]

    # Filtros adicionais
    placas = df_cliente["PLACA"].dropna().unique()
    placa_sel = st.sidebar.multiselect("Placa", options=placas)
    df_placa = df_cliente[df_cliente["PLACA"].isin(placa_sel)] if placa_sel else df_cliente

    seriais = df_placa["SERIAL"].dropna().unique()
    serial_sel = st.sidebar.multiselect("Serial", options=seriais)
    df_serial = df_placa[df_placa["SERIAL"].isin(serial_sel)] if serial_sel else df_placa

    prioridades = df_serial["Prioridade"].dropna().unique()
    prioridade_sel = st.sidebar.multiselect("Prioridade", options=prioridades)
    df_prioridade = df_serial[df_serial["Prioridade"].isin(prioridade_sel)] if prioridade_sel else df_serial

    status_opts = df_prioridade["Status"].dropna().astype(str).str.strip().unique().tolist()
    status_opts.sort()
    status_sel = st.sidebar.multiselect("Status", options=status_opts)
    df_status = df_prioridade[df_prioridade["Status"].isin(status_sel)] if status_sel else df_prioridade

    entrega_opts = df_status["Entrega"].dropna().astype(str).str.strip().unique().tolist()
    entrega_opts.sort()
    entrega_sel = st.sidebar.multiselect("Entrega", options=entrega_opts)
    df_entrega = df_status[df_status["Entrega"].isin(entrega_sel)] if entrega_sel else df_status

    bm_opts = df_entrega["BM"].dropna().astype(str).str.strip().unique().tolist()
    bm_opts.sort()
    bm_sel = st.sidebar.multiselect("BM", options=bm_opts)
    df_bm = df_entrega[df_entrega["BM"].isin(bm_sel)] if bm_sel else df_entrega

    # --- Filtro Data ---
    date_range = st.sidebar.date_input(
        "Período de chegada",
        value=[df["DATA DE CHEGADA"].min().date(), pd.Timestamp.today().date()],
        help="Selecione o intervalo de datas"
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        data_inicio, data_fim = date_range
        df_filtered = df_bm[
            (df_bm["DATA DE CHEGADA"].dt.date >= data_inicio) &
            (df_bm["DATA DE CHEGADA"].dt.date <= data_fim)
        ]
    else:
        df_filtered = df_bm
        st.info("🗓️ Selecione a data inicial e final para aplicar o filtro.")

    # --- Filtro Data de Entrega ---
    date_range_entrega = st.sidebar.date_input(
        "Período de entrega",
        value=[],
        help="Selecione o intervalo de datas de entrega"
    )
    if isinstance(date_range_entrega, (list, tuple)) and len(date_range_entrega) == 2:
        data_inicio_entrega, data_fim_entrega = date_range_entrega
        df_filtered = df_filtered[
            (df_filtered["ENTREGA/PREVISÃO"].dt.date >= data_inicio_entrega) &
            (df_filtered["ENTREGA/PREVISÃO"].dt.date <= data_fim_entrega)
        ]
    elif date_range_entrega:
        start_date, end_date = date_range_entrega
        df_filtered = df_filtered[
            (df_filtered["ENTREGA/PREVISÃO"].dt.date >= start_date) &
            (df_filtered["ENTREGA/PREVISÃO"].dt.date <= end_date)
        ]
    else:
        st.info("🗓️ Selecione a data inicial e final para aplicar o filtro de entrega.")

    # =========================
    # KPIs e Dashboard
    # =========================
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(f"<div class='metric-card'>📦<br>Total recebidos<br>{len(df_filtered)}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'>📱<br>Seriais<br>{df_filtered['SERIAL'].nunique()}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'>✅<br>Reparados<br>{(df_filtered['Status']=='Reparada').sum()}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'>↩️<br>Retorno<br>{(df_filtered['Status']=='Retorno').sum()}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='metric-card'>🔄<br>Em andamento<br>{(df_filtered['Status']=='Analisando').sum()}</div>", unsafe_allow_html=True)
    with col6:
        st.markdown(f"<div class='metric-card'>❌<br>Sem reparo<br>{(df_filtered['Status']=='Sem Reparo').sum()}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='font_negrit'><br>🕒 Última atualização: {last_modified_str}</div>", unsafe_allow_html=True)
    st.markdown("---")

    # =========================
    # Abas
    # =========================
    aba = st.tabs(["📊 Visão Geral", "📈 Linha do Tempo", "🛠️ Detalhamento", "💰 Financeiro"])

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

        # Linha do tempo por Serial (Gantt)
        df_gantt = df_timeline[["SERIAL", "PLACA", "DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO"]].copy()
        df_gantt = df_gantt.rename(columns={"DATA DE CHEGADA": "Inicio", "DATA DE REPARO": "Fim"})
        df_gantt["Fim"] = df_gantt["Fim"].fillna(df_gantt["ENTREGA/PREVISÃO"])
        df_gantt = df_gantt.dropna(subset=["Inicio", "Fim"])
        fig_gantt = px.timeline(df_gantt, x_start="Inicio", x_end="Fim", y="SERIAL", color="PLACA", hover_data=["PLACA"], title="Linha do Tempo por Serial")
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(xaxis_title="Data", yaxis_title="Serial", showlegend=True)
        st.plotly_chart(fig_gantt, use_container_width=True)


    # =========================
    # Usar a coluna LINK RELATORIO para gerar links
    # =========================
    df_filtered["Relatório de Reparo"] = df_filtered["LINK RELATORIO"]

    with aba[2]:
        # Criar uma cópia para exibição
        df_display = df_filtered.copy()
        for col in ["DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO"]:
            df_display[col] = df_display[col].dt.strftime("%d/%m/%Y")

        # Remover colunas desnecessárias
        if "CLIENTE" in df_display.columns:
            df_display = df_display.drop(columns=["CLIENTE", "BM", "VALOR","LINK RELATORIO"])

        # Reorganizar colunas
        cols = [c for c in df_display.columns if c not in ["DATA DE REPARO", "ENTREGA/PREVISÃO"]]
        cols += ["DATA DE REPARO", "ENTREGA/PREVISÃO"]
        df_display = df_display[cols]

        df_display["Relatório de Reparo"] = df_filtered["LINK RELATORIO"].apply(
            lambda x: (
                f'<a href="{x}" target="_blank" style="text-decoration:none;">'
                f'<button style="background-color:#2E86C1;color:white;border:none;'
                f'padding:6px 12px;border-radius:8px;cursor:pointer;'
                f'font-weight:600;font-size:13px;box-shadow:1px 1px 6px rgba(0,0,0,0.2);">'
                f'📄 Abrir PDF</button></a>'
            ) if pd.notna(x) and x.strip() != "" else "❌ Sem relatório"
        )


        # Converter o DataFrame em HTML com escape=False para interpretar HTML
        html_table = df_display.to_html(escape=False, index=False)

        st.markdown("### 📄 Relatórios de Reparo")
        
        st.markdown(html_table, unsafe_allow_html=True)

        # Botão de download do CSV
        st.download_button(
            label="📥 Exportar dados filtrados",
            data=df_filtered.drop(columns=["CLIENTE"]).to_csv(index=False).encode("utf-8"),
            file_name="reparos_filtrados.csv",
            mime="text/csv"
        )



    # ------------------ Financeiro ------------------
    with aba[3]:
        st.subheader("💰 Controle Financeiro")
        df_fin = df_filtered[["BM", "VALOR", "SERIAL", "PLACA", "DATA DE CHEGADA"]].dropna(subset=["VALOR"]).copy()
        df_fin["VALOR"] = pd.to_numeric(df_fin["VALOR"], errors="coerce")

        # ==== Indicador de Valor Total ====
        valor_total = df_fin["VALOR"].sum()
        st.markdown(
            f"<div class='metric-card'>💵<br>Valor Total<br>R$ {valor_total:,.2f}</div>",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)  # espaçamento

        # --- Formatar datas no padrão dd/mm/aaaa ---
        df_fin["DATA DE CHEGADA"] = df_fin["DATA DE CHEGADA"].dt.strftime("%d/%m/%Y")

        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            # Criar uma cópia formatada só para exibição
            df_fin_display = df_fin.copy()
            df_fin_display["VALOR"] = df_fin_display["VALOR"].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

            st.dataframe(df_fin_display, use_container_width=True, hide_index=True)

        with col2:
            fig_valor_bm = px.bar(
                df_fin.groupby("BM")["VALOR"].sum().reset_index(),
                x="BM", y="VALOR", title="💵 Valor Total por BM",
                color="VALOR", color_continuous_scale="Teal"
            )
            st.plotly_chart(fig_valor_bm, use_container_width=True)

            fig_valor_placa = px.pie(
                df_fin, names="PLACA", values="VALOR",
                title="Distribuição de Valor por Placa",
                hole=0.4, color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            st.plotly_chart(fig_valor_placa, use_container_width=True)

        st.markdown("### 📈 Evolução dos Gastos Mensais")

        # Criar coluna Mês/Ano
        df_fin["Mes_Ano"] = pd.to_datetime(df_fin["DATA DE CHEGADA"], format="%d/%m/%Y").dt.to_period("M").astype(str)

        # Agrupar por mês
        df_mensal = df_fin.groupby("Mes_Ano")["VALOR"].sum().reset_index()

        # Criar coluna formatada em reais (para labels, se quiser mostrar)
        df_mensal["VALOR_FORMATADO"] = df_mensal["VALOR"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        # Gráfico usando valores numéricos
        fig_mensal = px.line(
            df_mensal, x="Mes_Ano", y="VALOR", markers=True,
            title="Evolução Mensal dos Valores",
            text="VALOR_FORMATADO"  # Mostra os rótulos formatados
        )

        fig_mensal.update_traces(line_color="#005bea", textposition="top center")
        st.plotly_chart(fig_mensal, use_container_width=True)


    st.write("🚀 Dashboard carregado com sucesso!")

elif st.session_state.get('authentication_status') is False:
    st.error("Usuário ou senha incorretos")
elif st.session_state.get('authentication_status') is None:
    st.warning("Por favor, insira suas credenciais")