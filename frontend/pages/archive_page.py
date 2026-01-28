"""
Archive page - view archived articles.
"""

import reflex as rx
import httpx
from typing import List, Dict
from frontend.state import AppState


class ArchiveState(AppState):
    """Archive page state"""

    archives: List[Dict] = []
    loading: bool = False
    error: str = ""
    filter_action: str = ""  # '', 'approved', or 'rejected'

    async def load_archives(self):
        """Load archived articles"""
        await self.check_auth()

        self.loading = True
        self.error = ""

        try:
            url = f"{self.api_url}/api/archive/"
            if self.filter_action:
                url += f"?action={self.filter_action}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.get_headers())

                if response.status_code == 200:
                    self.archives = response.json()
                else:
                    self.error = f"Error loading archives: {response.status_code}"
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.loading = False

    def set_filter(self, action: str):
        """Set filter and reload"""
        self.filter_action = action
        return self.load_archives()


def archive_row(archive: Dict) -> rx.Component:
    """Single archive row"""
    return rx.table.row(
        rx.table.cell(str(archive["staging_article_id"])),
        rx.table.cell(
            rx.badge(
                archive["action"],
                color_scheme="green" if archive["action"] == "approved" else "red",
            )
        ),
        rx.table.cell(archive["archived_at"][:10]),
        rx.table.cell(archive.get("reviewer_comments", "")[:50] + "..."),
    )


def archive_list_page() -> rx.Component:
    """Archive page component"""
    return rx.container(
        rx.vstack(
            # Header
            rx.hbox(
                rx.heading("Archive", size="8"),
                rx.spacer(),
                rx.button("← Back to Dashboard", on_click=lambda: rx.redirect("/")),
                rx.button("Logout", on_click=ArchiveState.logout, variant="soft"),
                width="100%",
                align="center",
            ),
            # Filters
            rx.hbox(
                rx.button("All", on_click=lambda: ArchiveState.set_filter("")),
                rx.button(
                    "Approved",
                    on_click=lambda: ArchiveState.set_filter("approved"),
                    color_scheme="green",
                ),
                rx.button(
                    "Rejected",
                    on_click=lambda: ArchiveState.set_filter("rejected"),
                    color_scheme="red",
                ),
                spacing="4",
            ),
            # Error message
            rx.cond(
                ArchiveState.error != "",
                rx.callout(ArchiveState.error, color_scheme="red"),
            ),
            # Archives table
            rx.cond(
                ArchiveState.loading,
                rx.spinner(),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Article ID"),
                            rx.table.column_header_cell("Action"),
                            rx.table.column_header_cell("Archived Date"),
                            rx.table.column_header_cell("Comments"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(ArchiveState.archives, archive_row),
                    ),
                    variant="surface",
                    width="100%",
                ),
            ),
            spacing="6",
            width="100%",
            padding="4",
        ),
        on_mount=ArchiveState.load_archives,
    )
