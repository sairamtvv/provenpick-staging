"""
Article review page - matches main ProvenPick article display
"""

import reflex as rx
import httpx
from typing import Optional, List, Dict
from frontend.state import AppState


class ProductImage(rx.Base):
    """Product image model"""

    image_url: str
    alt_text: Optional[str] = None


class ProductText(rx.Base):
    """Product text model"""

    content: str
    heading: Optional[str] = None


class Product(rx.Base):
    """Product model"""

    name: str
    brand: str
    price: float
    description: str
    image_url: str
    affiliate_links: Dict
    images: List[ProductImage] = []
    texts: List[ProductText] = []


class ArticleImage(rx.Base):
    """Article image model"""

    image_url: str
    alt_text: Optional[str] = None
    image_type: str


class ArticleText(rx.Base):
    """Article text model"""

    content: str
    section_type: str


class Article(rx.Base):
    """Article model"""

    title: str
    category: str
    submitted_at: str
    hook_image: Optional[ArticleImage] = None
    introduction: Optional[ArticleText] = None  # Introduction section (above mindmap)
    mindmap_image: Optional[ArticleImage] = None
    mindmap_summary: Optional[ArticleText] = None
    full_article_html: Optional[str] = None  # Full article content
    bullet_points: Optional[str] = None  # Bullet points summary
    methodology_texts: List[ArticleText] = []
    top_pick: Optional[Product] = None
    runner_up: Optional[Product] = None
    budget_pick: Optional[Product] = None


class ReviewState(AppState):
    """Review page state"""

    article: Optional[Article] = None
    loading: bool = False
    error: str = ""
    comments: str = ""
    action_loading: bool = False
    current_article_id: int = 0
    hook_image_uploading: bool = False
    uploaded_hook_image_url: str = ""

    def set_comments(self, value: str):
        """Set comments value"""
        self.comments = value

    @rx.var
    def get_full_article_html_dataurl(self) -> str:
        """Return full article HTML as data URL for iframe"""
        if self.article and self.article.full_article_html:
            import base64

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            font-size: 1.05em;
            padding: 1em;
            margin: 0;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 600;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: 600;
        }}
        p {{
            margin: 0.8em 0;
        }}
    </style>
</head>
<body>
{self.article.full_article_html}
</body>
</html>
            """
            # Encode as base64 data URL
            encoded = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
            return f"data:text/html;base64,{encoded}"
        return ""

    async def handle_hook_image_upload(self, files: list[rx.UploadFile]):
        """Handle hook image upload"""
        if not files:
            return

        self.hook_image_uploading = True

        try:
            file = files[0]
            upload_data = await file.read()

            # Save file to a temporary location or upload to storage
            import base64
            import os
            from datetime import datetime

            # Create uploads directory if it doesn't exist
            upload_dir = "uploaded_files"
            os.makedirs(upload_dir, exist_ok=True)

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hook_{self.current_article_id}_{timestamp}_{file.filename}"
            filepath = os.path.join(upload_dir, filename)

            # Save file
            with open(filepath, "wb") as f:
                f.write(upload_data)

            # Update the article's hook image via API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/articles/{self.current_article_id}/hook-image",
                    headers=self.get_headers(),
                    json={"image_url": f"/{filepath}", "alt_text": "Hook Image"},
                )

                if response.status_code == 200:
                    self.uploaded_hook_image_url = f"/{filepath}"
                    # Reload article to show new image
                    await self.load_article(self.current_article_id)
                else:
                    self.error = f"Failed to upload image: {response.text}"
        except Exception as e:
            self.error = f"Upload error: {str(e)}"
        finally:
            self.hook_image_uploading = False

    async def on_load(self):
        """Load article when page mounts"""
        # Get article_id from URL params
        article_id_str = self.router.page.params.get("article_id", "")

        if not article_id_str or article_id_str == "":
            self.error = "No article ID provided"
            return

        try:
            self.current_article_id = int(article_id_str)
            await self.load_article(self.current_article_id)
        except ValueError:
            self.error = f"Invalid article ID: {article_id_str}"

    async def load_article(self, article_id: int):
        """Load and transform article to match main app structure"""
        self.loading = True
        self.error = ""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/articles/{article_id}",
                    headers=self.get_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    # Transform staging data to match main app structure
                    article_data = data["article"]
                    products = data["products"]
                    article_images = data.get("article_images", [])
                    article_texts = data.get("article_texts", [])

                    # Find specific images
                    hook_img = next(
                        (
                            ArticleImage(**img)
                            for img in article_images
                            if img["image_type"] == "hook"
                        ),
                        None,
                    )
                    mindmap_img = next(
                        (
                            ArticleImage(**img)
                            for img in article_images
                            if img["image_type"] == "mindmap"
                        ),
                        None,
                    )

                    # Find mindmap summary text
                    mindmap_summary = next(
                        (
                            ArticleText(**txt)
                            for txt in article_texts
                            if txt["section_type"] == "mindmap_summary"
                        ),
                        None,
                    )

                    # Find introduction text
                    introduction = next(
                        (
                            ArticleText(**txt)
                            for txt in article_texts
                            if txt["section_type"] == "introduction"
                        ),
                        None,
                    )

                    # Find full article HTML
                    full_article_text = next(
                        (
                            txt
                            for txt in article_texts
                            if txt["section_type"] == "full_article"
                        ),
                        None,
                    )
                    full_article_html = (
                        full_article_text["content"] if full_article_text else None
                    )

                    # Find bullet points
                    bullet_points_text = next(
                        (
                            txt
                            for txt in article_texts
                            if txt["section_type"] == "bullet_points"
                        ),
                        None,
                    )
                    bullet_points = (
                        bullet_points_text["content"] if bullet_points_text else None
                    )

                    # Get methodology texts
                    methodology_texts = [
                        ArticleText(**txt)
                        for txt in article_texts
                        if txt["section_type"] in ["methodology", "general"]
                    ]

                    # Transform products
                    def transform_product(prod_data):
                        return Product(
                            name=prod_data["name"],
                            brand=prod_data["brand"],
                            price=prod_data["price"],
                            description=prod_data["description"],
                            image_url=prod_data["image_url"],
                            affiliate_links=prod_data.get("affiliate_links", {})
                            if isinstance(prod_data.get("affiliate_links"), dict)
                            else {},
                            images=[
                                ProductImage(**img)
                                for img in prod_data.get("images", [])
                            ],
                            texts=[
                                ProductText(**txt) for txt in prod_data.get("texts", [])
                            ],
                        )

                    top_pick = (
                        transform_product(
                            products[str(article_data["top_pick_staging_id"])]
                        )
                        if str(article_data["top_pick_staging_id"]) in products
                        else None
                    )
                    runner_up = (
                        transform_product(
                            products[str(article_data["runner_up_staging_id"])]
                        )
                        if article_data.get("runner_up_staging_id")
                        and str(article_data["runner_up_staging_id"]) in products
                        else None
                    )
                    budget_pick = (
                        transform_product(
                            products[str(article_data["budget_pick_staging_id"])]
                        )
                        if article_data.get("budget_pick_staging_id")
                        and str(article_data["budget_pick_staging_id"]) in products
                        else None
                    )

                    self.article = Article(
                        title=article_data["title"],
                        category=article_data["category"],
                        submitted_at=article_data["submitted_at"],
                        hook_image=hook_img,
                        introduction=introduction,
                        mindmap_image=mindmap_img,
                        mindmap_summary=mindmap_summary,
                        full_article_html=full_article_html,
                        bullet_points=bullet_points,
                        methodology_texts=methodology_texts,
                        top_pick=top_pick,
                        runner_up=runner_up,
                        budget_pick=budget_pick,
                    )
                else:
                    self.error = f"Error loading article: {response.status_code}"
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.loading = False

    async def approve_article(self):
        """Approve the article"""
        self.action_loading = True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/articles/{self.current_article_id}/approve",
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

    async def reject_article(self):
        """Reject the article"""
        if not self.comments:
            self.error = "Comments are required for rejection"
            return

        self.action_loading = True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/articles/{self.current_article_id}/reject",
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


# Component functions matching main app
def render_product_image(image: ProductImage):
    return rx.image(
        src=image.image_url,
        alt=image.alt_text,
        width="100%",
        height="200px",
        object_fit="contain",
        margin_bottom="1em",
        border_radius="8px",
    )


def render_product_text(text: ProductText):
    return rx.box(
        rx.cond(
            text.heading, rx.heading(text.heading, size="4", margin_bottom="0.5em")
        ),
        rx.markdown(text.content, margin_bottom="1em"),
        width="100%",
    )


def render_methodology_text(text: ArticleText):
    """Render methodology/testing process text sections."""
    return rx.box(
        rx.markdown(
            text.content,
            font_size="1.05em",
            line_height="1.7",
            margin_bottom="1.5em",
            color="#444",
        ),
        width="100%",
    )


def render_pick_box(product: Product, label: str, color_scheme: str = "red"):
    """Render a product pick box - matches main app exactly"""
    return rx.box(
        rx.flex(
            # Left Column: Details & Texts
            rx.box(
                rx.badge(
                    label,
                    color_scheme=color_scheme,
                    padding="0.5em 1em",
                    font_size="1em",
                    border_radius="4px",
                ),
                rx.heading(product.name, size="6", margin_top="0.5em"),
                rx.text(product.brand, color="#666", font_size="0.9em"),
                rx.text(
                    f"${product.price}",
                    font_size="1.5em",
                    font_weight="bold",
                    color="#333",
                    margin_y="0.5em",
                ),
                # Dynamic Texts (product descriptions)
                rx.foreach(product.texts, render_product_text),
                # Affiliate Buttons Section (always show - links may be present)
                rx.vstack(
                    rx.text(
                        "Where to Buy",
                        font_weight="bold",
                        font_size="0.9em",
                        color="#666",
                        margin_top="1em",
                    ),
                    rx.hstack(
                        rx.link(
                            rx.button(
                                "Amazon",
                                background_color="#FF9900",
                                color="white",
                                padding_x="1.5em",
                                padding_y="0.75em",
                                font_weight="bold",
                            ),
                            href=product.affiliate_links.get("amazon", "#"),
                            is_external=True,
                        ),
                        rx.link(
                            rx.button(
                                "Best Buy",
                                background_color="#0046BE",
                                color="white",
                                padding_x="1.5em",
                                padding_y="0.75em",
                                font_weight="bold",
                            ),
                            href=product.affiliate_links.get("bestbuy", "#"),
                            is_external=True,
                        ),
                        spacing="2",
                        wrap="wrap",
                    ),
                    align_items="start",
                    width="100%",
                ),
                flex="1",
                padding="1em",
            ),
            # Right Column: Images Gallery
            rx.box(
                rx.foreach(product.images, render_product_image),
                flex="1",
                padding="1em",
                min_width="250px",
                max_width="400px",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            background_color="white",
            border=f"2px solid var(--{color_scheme}-6)",
            border_radius="12px",
            padding="1.5em",
            gap="2em",
            box_shadow="0 2px 8px rgba(0,0,0,0.08)",
        ),
        margin_bottom="3em",
        width="100%",
    )


def review_page() -> rx.Component:
    """Review page component - matches main app structure exactly"""
    return rx.container(
        rx.cond(
            ReviewState.article,
            rx.vstack(
                # Action buttons at top
                rx.flex(
                    rx.button("← Back", on_click=lambda: rx.redirect("/")),
                    rx.spacer(),
                    rx.button(
                        "✓ Approve",
                        on_click=ReviewState.approve_article,
                        color_scheme="green",
                        loading=ReviewState.action_loading,
                    ),
                    rx.button(
                        "✗ Reject",
                        on_click=ReviewState.reject_article,
                        color_scheme="red",
                        loading=ReviewState.action_loading,
                    ),
                    spacing="4",
                    width="100%",
                    margin_bottom="2em",
                ),
                # Rejection comments (only show when rejecting)
                rx.box(
                    rx.heading("Rejection Comments", size="5", margin_bottom="0.5em"),
                    rx.text_area(
                        placeholder="Enter comments for rejection...",
                        value=ReviewState.comments,
                        on_change=ReviewState.set_comments,
                        width="100%",
                    ),
                    margin_bottom="2em",
                ),
                # Error message
                rx.cond(
                    ReviewState.error != "",
                    rx.callout(
                        ReviewState.error, color_scheme="red", margin_bottom="1em"
                    ),
                ),
                # Article Header
                rx.heading(ReviewState.article.title, size="9"),
                rx.hstack(
                    rx.text(
                        f"Category: {ReviewState.article.category}",
                        color="#333",
                        font_weight="500",
                    ),
                    rx.text(
                        f"Submitted: {ReviewState.article.submitted_at[:10]}",
                        color="#666",
                        font_style="italic",
                    ),
                    spacing="3",
                    margin_bottom="2em",
                ),
                # 1. Hook Image
                rx.cond(
                    ReviewState.article.hook_image,
                    rx.image(
                        src=ReviewState.article.hook_image.image_url,
                        alt=ReviewState.article.hook_image.alt_text,
                        width="100%",
                        max_height="500px",
                        object_fit="cover",
                        border_radius="12px",
                        margin_bottom="1em",
                    ),
                ),
                # Hook Image Upload Section
                rx.box(
                    rx.heading("Hook Image", size="5", margin_bottom="0.5em"),
                    rx.text(
                        "Upload a hook image for this article (recommended 1200x630px)",
                        color="#666",
                        font_size="0.9em",
                        margin_bottom="1em",
                    ),
                    rx.upload(
                        rx.vstack(
                            rx.button(
                                "Select Image",
                                color_scheme="blue",
                                loading=ReviewState.hook_image_uploading,
                            ),
                            rx.text(
                                "or drag and drop",
                                color="#888",
                                font_size="0.85em",
                            ),
                        ),
                        id="hook_image_upload",
                        accept={
                            "image/png": [".png"],
                            "image/jpeg": [".jpg", ".jpeg"],
                            "image/webp": [".webp"],
                        },
                        max_files=1,
                        border="2px dashed #ccc",
                        border_radius="8px",
                        padding="2em",
                        width="100%",
                        text_align="center",
                    ),
                    rx.button(
                        "Upload Hook Image",
                        on_click=lambda: ReviewState.handle_hook_image_upload(
                            rx.upload_files(upload_id="hook_image_upload")
                        ),
                        color_scheme="green",
                        margin_top="1em",
                        loading=ReviewState.hook_image_uploading,
                    ),
                    background_color="#f9f9f9",
                    border_radius="8px",
                    padding="1.5em",
                    margin_bottom="2em",
                    border="1px solid #eee",
                ),
                # 2. Introduction Section (above mindmap)
                rx.cond(
                    ReviewState.article.introduction,
                    rx.box(
                        rx.heading("Introduction", size="7", margin_bottom="1em"),
                        rx.markdown(
                            ReviewState.article.introduction.content,
                            font_size="1.1em",
                            line_height="1.7",
                            color="#333",
                        ),
                        width="100%",
                        padding="1.5em",
                        background_color="#fff",
                        border_radius="8px",
                        border="1px solid #eee",
                        margin_bottom="2em",
                    ),
                ),
                # 3. Mindmap Section
                rx.heading("How We Picked", size="7", margin_bottom="1em"),
                rx.cond(
                    ReviewState.article.mindmap_image,
                    rx.image(
                        src=ReviewState.article.mindmap_image.image_url,
                        alt=ReviewState.article.mindmap_image.alt_text,
                        width="100%",
                        object_fit="contain",
                        border_radius="8px",
                        margin_bottom="1.5em",
                        border="1px solid #eee",
                    ),
                ),
                rx.cond(
                    ReviewState.article.mindmap_summary,
                    rx.markdown(
                        ReviewState.article.mindmap_summary.content,
                        font_size="1.1em",
                        line_height="1.6",
                        margin_bottom="3em",
                        padding="1.5em",
                        background_color="#f9f9f9",
                        border_radius="8px",
                        border_left="4px solid #333",
                    ),
                ),
                # Full Article Content
                rx.cond(
                    ReviewState.article.full_article_html,
                    rx.vstack(
                        rx.divider(margin_y="2em"),
                        rx.heading("Full Article", size="7", margin_bottom="1.5em"),
                        rx.el.iframe(
                            src=ReviewState.get_full_article_html_dataurl,
                            style={
                                "width": "100%",
                                "minHeight": "800px",
                                "border": "none",
                            },
                        ),
                        width="100%",
                        padding="2em",
                        background_color="#fff",
                        border_radius="8px",
                        border="1px solid #eee",
                        margin_bottom="2em",
                        align_items="start",
                    ),
                ),
                rx.divider(margin_y="2em"),
                rx.heading("Top Picks", size="8", margin_bottom="1.5em"),
                # 3. Top Pick
                rx.cond(
                    ReviewState.article.top_pick,
                    render_pick_box(
                        ReviewState.article.top_pick, "Our Top Pick", "red"
                    ),
                ),
                # 4. Runner Up
                rx.cond(
                    ReviewState.article.runner_up,
                    render_pick_box(ReviewState.article.runner_up, "Runner Up", "blue"),
                ),
                # 5. Budget Pick
                rx.cond(
                    ReviewState.article.budget_pick,
                    render_pick_box(
                        ReviewState.article.budget_pick, "Budget Pick", "green"
                    ),
                ),
                # 6. Methodology/Testing Section
                rx.cond(
                    ReviewState.article.methodology_texts.length() > 0,
                    rx.box(
                        rx.divider(margin_y="2em"),
                        rx.heading(
                            "How We Tested",
                            size="7",
                            margin_bottom="1.5em",
                        ),
                        rx.foreach(
                            ReviewState.article.methodology_texts,
                            render_methodology_text,
                        ),
                        width="100%",
                        padding_y="2em",
                        background_color="#fafafa",
                        border_radius="8px",
                        padding_x="2em",
                        margin_top="2em",
                    ),
                ),
                width="100%",
                align_items="start",
                padding="2em",
            ),
            rx.cond(
                ReviewState.loading,
                rx.center(rx.spinner(), width="100%", padding="5em"),
                rx.center(
                    rx.text("Article not found or error loading"),
                    width="100%",
                    padding="5em",
                ),
            ),
        ),
        on_mount=ReviewState.on_load,
        max_width="1200px",
        padding="2em",
    )
