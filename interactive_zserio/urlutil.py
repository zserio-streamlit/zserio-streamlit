import streamlit as st

from interactive_zserio.widget import Widget

class URLUtil(Widget):
    def __init__(self):
        super().__init__("URLUtil")

    def get_current_url(self):
        headers = st.context.headers
        return headers["Host"]

    def get_url_params(self):
        params = st.query_params
        return params

    def set_url_params(self, params):
        self._log(f"setting url params: {params}")
        st.query_params.update(params)
