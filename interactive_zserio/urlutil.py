import streamlit as st
from streamlit.web.server.websocket_headers import _get_websocket_headers

from interactive_zserio.widget import Widget

class URLUtil(Widget):
    def __init__(self):
        super().__init__("URLUtil")

    def get_current_url(self):
        headers = _get_websocket_headers()
        self._log(headers)
        return headers["Host"]

    def get_url_params(self):
        params = st.experimental_get_query_params()
        self._log(params)
        return params

    def set_url_params(self, params):
        st.experimental_set_query_params(**params)
