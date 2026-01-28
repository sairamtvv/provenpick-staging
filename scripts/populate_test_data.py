#!/usr/bin/env python3
"""
Populate the staging database with test data.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.tables import (
    StagingArticleTable,
    StagingProductTable,
    StagingArticleImageTable,
    StagingArticleTextTable,
    StagingProductImageTable,
    StagingProductTextTable,
)


# Sample data
CATEGORIES = ["Laptops", "Headphones", "Smartphones", "Cameras", "Monitors"]
BRANDS = ["Sony", "Samsung", "Apple", "Dell", "LG", "Bose", "Canon", "Logitech"]

SAMPLE_ARTICLES = [
    {
        "title": "Best Wireless Headphones for 2026",
        "category": "Headphones",
        "products": [
            {
                "name": "Sony WH-1000XM6",
                "brand": "Sony",
                "price": 349.99,
                "is_top": True,
            },
            {"name": "Bose QuietComfort Ultra", "brand": "Bose", "price": 429.99},
            {"name": "Apple AirPods Max", "brand": "Apple", "price": 549.99},
        ],
    },
    {
        "title": "Top Gaming Laptops Under $2000",
        "category": "Laptops",
        "products": [
            {
                "name": "ASUS ROG Zephyrus G16",
                "brand": "ASUS",
                "price": 1899.99,
                "is_top": True,
            },
            {"name": "Dell XPS 15", "brand": "Dell", "price": 1699.99},
            {"name": "MSI Stealth 16", "brand": "MSI", "price": 1799.99},
        ],
    },
    {
        "title": "Best Budget Smartphones of 2026",
        "category": "Smartphones",
        "products": [
            {
                "name": "Google Pixel 8a",
                "brand": "Google",
                "price": 499.99,
                "is_top": True,
            },
            {"name": "Samsung Galaxy A54", "brand": "Samsung", "price": 449.99},
            {"name": "OnePlus Nord 3", "brand": "OnePlus", "price": 399.99},
        ],
    },
    {
        "title": "Professional Cameras for Content Creators",
        "category": "Cameras",
        "products": [
            {
                "name": "Canon EOS R6 Mark II",
                "brand": "Canon",
                "price": 2499.99,
                "is_top": True,
            },
            {"name": "Sony A7 IV", "brand": "Sony", "price": 2498.99},
            {"name": "Nikon Z6 III", "brand": "Nikon", "price": 2299.99},
        ],
    },
    {
        "title": "Best 4K Monitors for Productivity",
        "category": "Monitors",
        "products": [
            {
                "name": "LG UltraFine 27UN880",
                "brand": "LG",
                "price": 699.99,
                "is_top": True,
            },
            {"name": "Dell UltraSharp U2723DE", "brand": "Dell", "price": 649.99},
            {"name": "BenQ PD2725U", "brand": "BenQ", "price": 749.99},
        ],
    },
    {
        "title": "Top Mechanical Keyboards for 2026",
        "category": "Keyboards",
        "products": [
            {
                "name": "Logitech MX Mechanical",
                "brand": "Logitech",
                "price": 169.99,
                "is_top": True,
            },
            {"name": "Keychron Q1 Pro", "brand": "Keychron", "price": 199.99},
            {"name": "Corsair K70 RGB Pro", "brand": "Corsair", "price": 179.99},
        ],
    },
    {
        "title": "Best Wireless Mice for Productivity",
        "category": "Mice",
        "products": [
            {
                "name": "Logitech MX Master 3S",
                "brand": "Logitech",
                "price": 99.99,
                "is_top": True,
            },
            {"name": "Razer Pro Click", "brand": "Razer", "price": 99.99},
            {
                "name": "Microsoft Surface Precision",
                "brand": "Microsoft",
                "price": 99.95,
            },
        ],
    },
    {
        "title": "Best Webcams for Remote Work",
        "category": "Webcams",
        "products": [
            {
                "name": "Logitech Brio 4K",
                "brand": "Logitech",
                "price": 199.99,
                "is_top": True,
            },
            {"name": "Razer Kiyo Pro", "brand": "Razer", "price": 199.99},
            {"name": "Elgato Facecam", "brand": "Elgato", "price": 169.99},
        ],
    },
    {
        "title": "Top Portable SSDs for 2026",
        "category": "Storage",
        "products": [
            {
                "name": "Samsung T7 Shield 2TB",
                "brand": "Samsung",
                "price": 179.99,
                "is_top": True,
            },
            {"name": "SanDisk Extreme Pro 2TB", "brand": "SanDisk", "price": 199.99},
            {"name": "WD My Passport SSD 2TB", "brand": "WD", "price": 159.99},
        ],
    },
    {
        "title": "Best Noise-Cancelling Earbuds",
        "category": "Audio",
        "products": [
            {
                "name": "Sony WF-1000XM5",
                "brand": "Sony",
                "price": 299.99,
                "is_top": True,
            },
            {"name": "Apple AirPods Pro 2", "brand": "Apple", "price": 249.99},
            {"name": "Bose QuietComfort Earbuds II", "brand": "Bose", "price": 299.99},
        ],
    },
]

SAMPLE_IMAGES = [
    "https://picsum.photos/800/600?random=1",
    "https://picsum.photos/800/600?random=2",
    "https://picsum.photos/800/600?random=3",
    "https://picsum.photos/800/600?random=4",
    "https://picsum.photos/800/600?random=5",
]

SAMPLE_PRODUCT_IMAGES = [
    "https://picsum.photos/400/400?random=10",
    "https://picsum.photos/400/400?random=11",
    "https://picsum.photos/400/400?random=12",
    "https://picsum.photos/400/400?random=13",
]


async def populate_test_data(count: int = 10):
    """Populate the database with test articles and products."""

    print(f"Populating database with {count} test articles...")

    # Limit to available sample data
    count = min(count, len(SAMPLE_ARTICLES))

    for i in range(count):
        article_data = SAMPLE_ARTICLES[i]

        print(f"\n[{i + 1}/{count}] Creating article: {article_data['title']}")

        # Create products first
        product_ids = []
        top_pick_id = None

        for j, product_info in enumerate(article_data["products"]):
            product = StagingProductTable(
                name=product_info["name"],
                brand=product_info["brand"],
                category=article_data["category"],
                price=product_info["price"],
                description=f"High-quality {product_info['name']} - Perfect for {article_data['category'].lower()} enthusiasts. "
                f"Features advanced technology and premium build quality.",
                image_url=SAMPLE_PRODUCT_IMAGES[j % len(SAMPLE_PRODUCT_IMAGES)],
                specs={
                    "warranty": "1 year",
                    "color": "Black",
                    "weight": "200g",
                },
                affiliate_links={
                    "amazon": f"https://amazon.com/dp/{product_info['name'][:10]}",
                    "bestbuy": f"https://bestbuy.com/{product_info['name'][:10]}",
                },
                created_at=datetime.now(),
            )

            await product.save()
            product_ids.append(product.staging_product_id)

            if product_info.get("is_top", False):
                top_pick_id = product.staging_product_id

            # Add product images
            await StagingProductImageTable(
                staging_product_id=product.staging_product_id,
                image_url=SAMPLE_PRODUCT_IMAGES[j % len(SAMPLE_PRODUCT_IMAGES)],
                alt_text=f"{product_info['name']} product image",
                sequence_order=0,
                created_at=datetime.now(),
            ).save()

            # Add product text content
            await StagingProductTextTable(
                staging_product_id=product.staging_product_id,
                content=f"**Key Features:**\n- Premium build quality\n- Advanced features\n- Excellent value\n\n"
                f"The {product_info['name']} stands out with its exceptional performance and reliability.",
                heading="Product Overview",
                sequence_order=0,
                created_at=datetime.now(),
            ).save()

            print(
                f"  ✓ Created product: {product_info['name']} (ID: {product.staging_product_id})"
            )

        # Use first product as top pick if none specified
        if not top_pick_id:
            top_pick_id = product_ids[0]

        # Create article
        article = StagingArticleTable(
            title=article_data["title"],
            category=article_data["category"],
            author_name="AI Content Generator",
            top_pick_staging_id=top_pick_id,
            runner_up_staging_id=product_ids[1] if len(product_ids) > 1 else None,
            budget_pick_staging_id=product_ids[2] if len(product_ids) > 2 else None,
            status="pending",
            submitted_at=datetime.now(),
            created_at=datetime.now(),
        )

        await article.save()
        print(f"  ✓ Created article (ID: {article.staging_article_id})")

        # Update products with article ID
        for product_id in product_ids:
            product = (
                await StagingProductTable.objects()
                .where(StagingProductTable.staging_product_id == product_id)
                .first()
            )
            product.staging_article_id = article.staging_article_id
            await product.save()

        # Add article images
        for img_idx, img_type in enumerate(["hook", "mindmap", "general"]):
            await StagingArticleImageTable(
                staging_article_id=article.staging_article_id,
                image_url=SAMPLE_IMAGES[img_idx % len(SAMPLE_IMAGES)],
                alt_text=f"{article_data['title']} - {img_type} image",
                image_type=img_type,
                sequence_order=img_idx,
                created_at=datetime.now(),
            ).save()

        print(f"  ✓ Added {3} images")

        # Add article text content
        sections = [
            (
                "mindmap_summary",
                f"# {article_data['title']}\n\n"
                f"In this comprehensive guide, we'll explore the best {article_data['category'].lower()} "
                f"available in 2026. We've tested and reviewed dozens of options to bring you our top picks.",
            ),
            (
                "methodology",
                "## Our Testing Methodology\n\n"
                "We conducted extensive hands-on testing over several weeks, evaluating each product based on:\n"
                "- Performance and features\n- Build quality and design\n- Value for money\n- User experience",
            ),
            (
                "general",
                f"## Why Trust Our Reviews?\n\n"
                f"Our team has over 50 years of combined experience in reviewing {article_data['category'].lower()}. "
                f"We purchase all products at full price and test them in real-world scenarios to provide unbiased recommendations.",
            ),
        ]

        for seq, (section_type, content) in enumerate(sections):
            await StagingArticleTextTable(
                staging_article_id=article.staging_article_id,
                content=content,
                section_type=section_type,
                sequence_order=seq,
                created_at=datetime.now(),
            ).save()

        print(f"  ✓ Added {len(sections)} text sections")

    print(
        f"\n✅ Successfully populated database with {count} articles and {count * 3} products!"
    )
    print(f"\n📝 Admin token for testing: provenpick-staging-secret-token-2026")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(populate_test_data(count))
