"""
ProvenPick Staging Frontend
Main Reflex application entry point.
"""

import reflex as rx
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.pages import login, dashboard, review, archive_page

# Create the app
app = rx.App()

# Add pages
app.add_page(login.login_page, route="/login")
app.add_page(dashboard.dashboard_page, route="/")
app.add_page(review.review_page, route="/review/[article_id]")
app.add_page(archive_page.archive_list_page, route="/archive")
