import streamlit as st
from app_frontend import login
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode


# Decorator function for login requirement

def login_required(func):
    def wrapper(*args, **kwargs):
        if "token" in st.session_state:
            # Check if the token is expired
            if "expiration_time" in st.session_state and st.session_state["expiration_time"] > datetime.now():
                # User is already logged in
                return func(*args, **kwargs)
            else:
                st.warning("Session expired. Please login again.")
                st.experimental_set_query_params(page="login")
                login()
        else:
            st.warning("You need to login first.")
            st.experimental_set_query_params(page="login")
            login()
    return wrapper

