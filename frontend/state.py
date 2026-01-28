"""
Shared state management for the entire app.
"""

import reflex as rx
import httpx
import os
from typing import List, Dict, Optional


class AppState(rx.State):
    """Global application state"""

    # API base URL
    api_url: str = "http://localhost:8080"

    def get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            "Content-Type": "application/json",
        }
