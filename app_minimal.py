import streamlit as st
import requests

st.set_page_config(page_title="Support Triage Co-pilot", layout="wide")

API_BASE_URL = "http://localhost:8000"

st.title("🎯 Support Triage Co-pilot")
st.markdown("*Testing minimal app*")

# Just show a simple button
if st.button("Test Button"):
    st.write("Button clicked!")

st.write("App is running!")
