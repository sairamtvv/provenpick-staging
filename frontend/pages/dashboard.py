"""
Dashboard page - list of pending articles.
"""

import reflex as rx
import httpx
from typing import List
from frontend.state import AppState


class ArticleItem(rx.Base):
    """Article list item model"""

    id: int
    title: str
    category: str
    top_pick_name: str
    products_count: int
    submitted_at: str
    status: str = "pending"


class DashboardState(AppState):
    """Dashboard state"""

    articles: List[ArticleItem] = []
    loading: bool = False
    error: str = ""

    async def load_articles(self):
        """Load pending articles from API"""
        self.loading = True
        self.error = ""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/articles/",
                    headers=self.get_headers(),
                )

                if response.status_code == 200:
                    self.articles = [
                        ArticleItem(**article) for article in response.json()
                    ]
                else:
                    self.error = f"Error loading articles: {response.status_code}"
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.loading = False

    def view_article(self, article_id: int):
        """Navigate to article review page"""
        return rx.redirect(f"/review/{article_id}")


def article_row(article: ArticleItem) -> rx.Component:
    """Single article row component"""
    return rx.table.row(
        rx.table.cell(article.title),
        rx.table.cell(article.category),
        rx.table.cell(article.top_pick_name),
        rx.table.cell(article.products_count),
        rx.table.cell(article.submitted_at[:10]),  # Date only
        rx.table.cell(
            rx.button(
                "Review",
                on_click=lambda: DashboardState.view_article(article.id),
                size="2",
            )
        ),
    )


def dashboard_page() -> rx.Component:
    """Dashboard page component"""
    return rx.container(
        rx.vstack(
            # Header
            rx.flex(
                rx.heading("Staging Dashboard", size="8"),
                rx.spacer(),
                rx.button(
                    "Archive", on_click=lambda: rx.redirect("/archive"), variant="soft"
                ),
                width="100%",
                align="center",
            ),
            # Refresh button
            rx.button(
                "Refresh Articles",
                on_click=DashboardState.load_articles,
                loading=DashboardState.loading,
            ),
            # Error message
            rx.cond(
                DashboardState.error != "",
                rx.callout(DashboardState.error, color_scheme="red"),
            ),
            # Articles table
            rx.cond(
                DashboardState.loading,
                rx.spinner(),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Title"),
                            rx.table.column_header_cell("Category"),
                            rx.table.column_header_cell("Top Pick"),
                            rx.table.column_header_cell("Products"),
                            rx.table.column_header_cell("Submitted"),
                            rx.table.column_header_cell("Action"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(DashboardState.articles, article_row),
                    ),
                    variant="surface",
                    width="100%",
                ),
            ),
            spacing="6",
            width="100%",
            padding="4",
        ),
        on_mount=DashboardState.load_articles,
    )
