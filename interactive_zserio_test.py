from streamlit.testing.v1 import AppTest

app_test = AppTest.from_file("interactive_zserio.py")
app_test.run()

assert not app_test.exception
