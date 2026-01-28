"""
Main Reflex app and routing.
"""

import reflex as rx
from frontend.pages import login, dashboard, review, archive_page

# Create the app
app = rx.App()

# Add pages
app.add_page(login.login_page, route="/login")
app.add_page(dashboard.dashboard_page, route="/")
app.add_page(review.review_page, route="/review/[article_id]")
app.add_page(archive_page.archive_list_page, route="/archive")
