import i18n
from pathlib import Path
from typing import Optional

# Set up i18n
i18n.set('filename_format', '{locale}.{format}')
i18n.set('file_format', 'yml')
i18n.set('fallback', 'ru')
i18n.set('skip_locale_root_data', True)

# Load translations
locale_path = Path(__file__).parent.parent.parent / 'locales'
i18n.load_path.append(str(locale_path))

def translate(key: str, locale: str = 'ru', **kwargs) -> str:
    """
    Translate a message key to the specified locale
    
    Args:
        key: Translation key (e.g., 'auth.invalid_credentials')
        locale: Language code ('ru' or 'uz')
        **kwargs: Variables to interpolate into the message
    
    Returns:
        Translated message
    """
    return i18n.t(key, locale=locale, **kwargs)

def get_locale_from_header(accept_language: Optional[str]) -> str:
    """
    Extract locale from Accept-Language header
    
    Args:
        accept_language: HTTP Accept-Language header value
    
    Returns:
        Locale code ('ru' or 'uz'), defaults to 'ru'
    """
    if not accept_language:
        return 'ru'
    
    # Simple parsing - you can make this more sophisticated
    if 'uz' in accept_language.lower():
        return 'uz'
    return 'ru'