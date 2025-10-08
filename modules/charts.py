import plotly.express as px
import plotly.graph_objects as go

def grafico_status(df):
    return px.pie(df, names="Status", title="Distribuição de Status", hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Blues)

def grafico_reparos_por_placa(df):
    return px.bar(
        df.groupby("PLACA").size().reset_index(name="Quantidade"),
        x="PLACA", y="Quantidade", title="Reparos por Placa",
        color="Quantidade", color_continuous_scale="Blues"
    )

def grafico_timeline(chegadas, reparos):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chegadas["Mes_Ano_Chegada"], y=chegadas["Chegadas"],
                             mode="lines+markers", name="Chegadas"))
    fig.add_trace(go.Scatter(x=reparos["Mes_Ano_Reparo"], y=reparos["Reparos"],
                             mode="lines+markers", name="Reparos"))
    fig.update_layout(title="Linha do Tempo - Chegadas vs Reparos",
                      xaxis_title="Mês/Ano", yaxis_title="Quantidade")
    return fig
