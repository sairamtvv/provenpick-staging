"""
Login page for staging system.
"""

import reflex as rx
from frontend.state import AppState


class LoginState(AppState):
    """Login page state"""

    token_input: str = ""
    error_message: str = ""

    def set_token_input(self, value: str):
        """Set token input value"""
        self.token_input = value

    async def login(self):
        """Attempt login with token"""
        if not self.token_input:
            self.error_message = "Please enter a token"
            return

        # Set token and redirect
        self.set_token(self.token_input)
        self.error_message = ""
        return rx.redirect("/")


def login_page() -> rx.Component:
    """Login page component"""
    return rx.container(
        rx.vstack(
            rx.heading("ProvenPick Staging", size="9"),
            rx.text("Content Moderation System", size="5", color_scheme="gray"),
            rx.spacer(),
            rx.card(
                rx.vstack(
                    rx.heading("Login", size="6"),
                    rx.input(
                        placeholder="Enter your token",
                        type="password",
                        value=LoginState.token_input,
                        on_change=LoginState.set_token_input,
                        width="100%",
                    ),
                    rx.cond(
                        LoginState.error_message != "",
                        rx.text(LoginState.error_message, color="red"),
                    ),
                    rx.button(
                        "Login",
                        on_click=LoginState.login,
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                width="400px",
            ),
            spacing="6",
            align="center",
            justify="center",
            min_height="100vh",
        ),
        center_content=True,
    )
