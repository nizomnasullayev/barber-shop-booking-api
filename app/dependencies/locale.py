from fastapi import Header
from typing import Optional

async def get_locale(accept_language: Optional[str] = Header(None)) -> str:
    """Get locale from Accept-Language header"""
    from app.utils.i18n import get_locale_from_header
    return get_locale_from_header(accept_language)