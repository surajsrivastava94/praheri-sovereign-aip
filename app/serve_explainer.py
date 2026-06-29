"""Tiny static server for the standalone explainer page (the 'why/what' narrative).

The explainer (app/explainer.html) is a self-contained page; serving it over http
(rather than file://) keeps its 'Launch console →' links and fonts behaving
consistently. Sovereignty-safe: binds to localhost only, no external calls.

Run alongside the Streamlit console for the demo:

    python -m app.serve_explainer        # serves http://localhost:8000/explainer.html
    streamlit run app/streamlit_app.py   # the console at http://localhost:8501

Then open http://localhost:8000/explainer.html to start the walkthrough.
"""
from __future__ import annotations

import functools
import http.server
import socketserver
from pathlib import Path

PORT = 8000
ROOT = Path(__file__).resolve().parent  # serve app/ so /explainer.html resolves


def main() -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(ROOT))
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"Explainer → http://localhost:{PORT}/explainer.html  (Ctrl+C to stop)")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
