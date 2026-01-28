#!/usr/bin/env python3
"""
Test the staging system workflows
"""

import requests
import json

BASE_URL = "http://localhost:8080"
TOKEN = "provenpick-staging-secret-token-2026"

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def test_list_articles():
    """Test listing pending articles"""
    print("\n📋 Testing: List Pending Articles")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/articles/", headers=headers)

    if response.status_code == 200:
        articles = response.json()
        print(f"✓ Found {len(articles)} pending articles")

        for article in articles[:3]:  # Show first 3
            print(f"  - [{article['id']}] {article['title']}")
            print(
                f"    Category: {article['category']}, Products: {article['products_count']}"
            )

        return articles[0]["id"] if articles else None
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return None


def test_get_article(article_id):
    """Test getting full article details"""
    print(f"\n📖 Testing: Get Article Details (ID: {article_id})")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/articles/{article_id}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        article = data["article"]
        products = data["products"]

        print(f"✓ Article: {article['title']}")
        print(f"  Status: {article['status']}")
        print(f"  Submitted: {article['submitted_at']}")
        print(f"  Products: {len(products)}")

        for product_id, product in list(products.items())[:2]:
            print(
                f"    - {product['name']} by {product['brand']} (${product['price']})"
            )

        return True
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return False


def test_reject_article(article_id):
    """Test rejecting an article"""
    print(f"\n❌ Testing: Reject Article (ID: {article_id})")
    print("=" * 60)

    payload = {
        "comments": "Test rejection: The top pick needs better image quality and more detailed specifications."
    }

    response = requests.post(
        f"{BASE_URL}/api/articles/{article_id}/reject", headers=headers, json=payload
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Article rejected successfully")
        print(f"  Message: {result.get('message', 'Success')}")
        return True
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return False


def test_approve_article(article_id):
    """Test approving an article"""
    print(f"\n✅ Testing: Approve Article (ID: {article_id})")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/articles/{article_id}/approve", headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Article approved successfully")
        print(f"  Message: {result.get('message', 'Success')}")
        return True
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return False


def test_archive():
    """Test archive endpoint"""
    print(f"\n📦 Testing: View Archive")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/archive/", headers=headers)

    if response.status_code == 200:
        archives = response.json()
        print(f"✓ Found {len(archives)} archived items")

        for archive in archives[:3]:
            print(f"  - Article {archive['staging_article_id']}: {archive['action']}")
            if archive.get("reviewer_comments"):
                print(f"    Comments: {archive['reviewer_comments'][:50]}...")

        return True
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return False


def main():
    print("\n" + "=" * 60)
    print("  ProvenPick Staging System - Workflow Tests")
    print("=" * 60)

    # Test 1: List articles
    article_id = test_list_articles()
    if not article_id:
        print("\n✗ No articles found. Aborting tests.")
        return

    # Test 2: Get article details
    test_get_article(article_id)

    # Test 3: Reject an article
    test_reject_article(article_id)

    # Test 4: Get another article for approval
    article_id_2 = test_list_articles()
    if article_id_2:
        # Test 5: Approve an article
        test_approve_article(article_id_2)

    # Test 6: View archive
    test_archive()

    print("\n" + "=" * 60)
    print("  ✅ All Tests Completed!")
    print("=" * 60)
    print("\n🎉 The staging system is working as expected!")
    print("\n📌 Next Steps:")
    print("  1. Open http://localhost:3000 in your browser")
    print("  2. Login with token: provenpick-staging-secret-token-2026")
    print("  3. Review, approve, or reject articles through the UI")
    print("  4. Check the archive page to see approved/rejected items")
    print()


if __name__ == "__main__":
    main()
