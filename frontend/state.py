"""
Shared state management for the entire app.
"""

import reflex as rx
import httpx
import os
from typing import List, Dict, Optional


class AppState(rx.State):
    """Global application state"""

    # Authentication
    token: str = ""
    is_authenticated: bool = False

    # API base URL
    api_url: str = "http://localhost:8000"

    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
        self.is_authenticated = bool(token)

    def logout(self):
        """Clear authentication"""
        self.token = ""
        self.is_authenticated = False
        return rx.redirect("/login")

    async def check_auth(self):
        """Check if user is authenticated"""
        if not self.is_authenticated:
            return rx.redirect("/login")

    def get_headers(self) -> Dict[str, str]:
        """Get API request headers with auth token"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
