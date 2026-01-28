"""
Reflex configuration file.
"""

import reflex as rx

config = rx.Config(
    app_name="staging_frontend",
    backend_port=8000,  # Reflex websocket backend
    frontend_port=3000,
)
