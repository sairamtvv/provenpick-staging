"""
Reflex configuration file.
"""

import reflex as rx

config = rx.Config(
    app_name="staging_frontend",
    backend_port=8001,  # Different from provenpick (8000)
    frontend_port=3001,  # Different from provenpick (3000)
)
