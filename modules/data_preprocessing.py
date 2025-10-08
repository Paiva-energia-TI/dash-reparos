import pandas as pd

def preparar_dataframe(df):
    df = df[[
        "SEQ", "PLACA", "VERSÃO", "SERIAL", "Prioridade",
        "DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO",
        "CLIENTE", "LOCAL", "Status", "FOLLOW-UP","GARANTIA", "Entrega", "BM", "VALOR"
    ]].copy()

    for col in ["DATA DE CHEGADA", "DATA DE REPARO", "ENTREGA/PREVISÃO"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df
