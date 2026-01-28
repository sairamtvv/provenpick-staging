"""
Reflex configuration file.
"""

import reflex as rx

config = rx.Config(
    app_name="staging_frontend",
    api_url="http://localhost:8000",
    frontend_port=3000,
)
