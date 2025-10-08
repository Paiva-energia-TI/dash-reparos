import streamlit as st
import streamlit_authenticator as stauth

def autenticar_usuario():
    config = st.secrets
    credentials = {
        "usernames": {
            username: {
                "name": f"{info['first_name']} {info['last_name']}",
                "email": info['email'],
                "password": info['password'],
                "role": info['role']
            }
            for username, info in config["credentials"]["usernames"].items()
        }
    }

    authenticator = stauth.Authenticate(
        credentials,
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    return authenticator
