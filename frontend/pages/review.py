"""
Article review page - view and approve/reject articles.
"""

import reflex as rx
import httpx
from typing import Dict, Optional
from frontend.state import AppState


class ReviewState(AppState):
    """Review page state"""

    article: Optional[Dict] = None
    loading: bool = False
    error: str = ""
    comments: str = ""
    action_loading: bool = False

    async def load_article(self, article_id: int):
        """Load full article details"""
        await self.check_auth()

        self.loading = True
        self.error = ""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/articles/{article_id}",
                    headers=self.get_headers(),
                )

                if response.status_code == 200:
                    self.article = response.json()
                else:
                    self.error = f"Error loading article: {response.status_code}"
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.loading = False

    async def approve_article(self, article_id: int):
        """Approve the article"""
        self.action_loading = True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/articles/{article_id}/approve",
                    headers=self.get_headers(),
                )

                if response.status_code == 200:
                    return rx.redirect("/")
                else:
                    self.error = f"Error approving: {response.text}"
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.action_loading = False

    async def reject_article(self, article_id: int):
        """Reject the article"""
        if not self.comments:
            self.error = "Comments are required for rejection"
            return

        self.action_loading = True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/articles/{article_id}/reject",
                    headers=self.get_headers(),
                    json={"comments": self.comments},
                )

                if response.status_code == 200:
                    return rx.redirect("/")
                else:
                    self.error = f"Error rejecting: {response.text}"
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.action_loading = False


def review_page() -> rx.Component:
    """Review page component"""
    return rx.container(
        rx.vstack(
            # Header
            rx.hbox(
                rx.button("← Back", on_click=lambda: rx.redirect("/")),
                rx.spacer(),
                rx.button("Logout", on_click=ReviewState.logout, variant="soft"),
                width="100%",
            ),
            # Error message
            rx.cond(
                ReviewState.error != "",
                rx.callout(ReviewState.error, color_scheme="red"),
            ),
            # Loading or content
            rx.cond(
                ReviewState.loading,
                rx.spinner(),
                rx.cond(
                    ReviewState.article.is_none(),
                    rx.text("Article not found"),
                    rx.hbox(
                        # Left panel - metadata and actions
                        rx.card(
                            rx.vstack(
                                rx.heading("Article Review", size="6"),
                                rx.text(
                                    f"Title: {ReviewState.article['article']['title']}",
                                    weight="bold",
                                ),
                                rx.text(
                                    f"Category: {ReviewState.article['article']['category']}"
                                ),
                                rx.text(
                                    f"Submitted: {ReviewState.article['article']['submitted_at']}"
                                ),
                                rx.divider(),
                                rx.heading("Products", size="4"),
                                rx.text(
                                    f"Top Pick: {ReviewState.article['products'][ReviewState.article['article']['top_pick_staging_id']]['name']}"
                                ),
                                rx.divider(),
                                rx.heading("Comments", size="4"),
                                rx.text_area(
                                    placeholder="Enter comments for rejection...",
                                    value=ReviewState.comments,
                                    on_change=ReviewState.set_comments,
                                    width="100%",
                                ),
                                rx.divider(),
                                rx.hbox(
                                    rx.button(
                                        "✓ Approve",
                                        on_click=lambda: ReviewState.approve_article(
                                            ReviewState.article["article"][
                                                "staging_article_id"
                                            ]
                                        ),
                                        color_scheme="green",
                                        loading=ReviewState.action_loading,
                                    ),
                                    rx.button(
                                        "✗ Reject",
                                        on_click=lambda: ReviewState.reject_article(
                                            ReviewState.article["article"][
                                                "staging_article_id"
                                            ]
                                        ),
                                        color_scheme="red",
                                        loading=ReviewState.action_loading,
                                    ),
                                    spacing="4",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            width="400px",
                        ),
                        # Right panel - preview
                        rx.card(
                            rx.vstack(
                                rx.heading("Preview", size="6"),
                                rx.text("Article preview would appear here"),
                                rx.text(
                                    "(Reuse article rendering component from main ProvenPick)"
                                ),
                                spacing="4",
                            ),
                            flex="1",
                        ),
                        spacing="6",
                        width="100%",
                    ),
                ),
            ),
            spacing="6",
            width="100%",
            padding="4",
        ),
        on_mount=lambda: ReviewState.load_article(
            ReviewState.router.page.params.get("article_id")
        ),
    )
