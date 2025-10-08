import streamlit as st

def aplicar_estilos():
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
