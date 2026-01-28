"""
Simple token-based authentication for staging system.
"""

import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

STAGING_ADMIN_TOKEN = os.getenv("STAGING_ADMIN_TOKEN", "")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the authorization token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        The token if valid

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials

    if not STAGING_ADMIN_TOKEN:
        raise HTTPException(
            status_code=500, detail="STAGING_ADMIN_TOKEN not configured"
        )

    if token != STAGING_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return token
