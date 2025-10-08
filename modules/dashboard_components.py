import streamlit as st

def mostrar_kpis(df):
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(f"<div class='metric-card'>📦<br>Total recebidos<br>{len(df)}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'>📱<br>Seriais<br>{df['SERIAL'].nunique()}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'>✅<br>Reparados<br>{(df['Status']=='Reparada').sum()}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'>↩️<br>Retorno<br>{(df['Status']=='Retorno').sum()}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='metric-card'>🔄<br>Em andamento<br>{(df['Status']=='Analisando').sum()}</div>", unsafe_allow_html=True)
    with col6:
        st.markdown(f"<div class='metric-card'>❌<br>Sem reparo<br>{(df['Status']=='Sem Reparo').sum()}</div>", unsafe_allow_html=True)
