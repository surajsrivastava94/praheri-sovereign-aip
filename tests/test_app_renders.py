"""Regression guard — the Streamlit app must render top-to-bottom with no exception.

Catches the class of bug a server health-check misses: import errors and script
exceptions that only surface when Streamlit actually runs the script (e.g. the
praheri package not being importable under streamlit's sys.path).
"""
from streamlit.testing.v1 import AppTest


def test_app_renders_without_exception():
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=30).run()
    assert not at.exception, [str(e.value) for e in at.exception]
    # Platform + Alert Queue, Investigation, Approvals, Audit + 5 verticals
    # (Procurement, Insurance SIU, Lending EWS, Wealth, Corporate)
    assert len(at.tabs) == 10
