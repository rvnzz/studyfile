import anthropic
from django.conf import settings


def get_client() -> anthropic.Anthropic:
    # SDK добавляет /v1/messages к base_url, поэтому убираем /v1 если есть
    base_url = settings.ANTHROPIC_BASE_URL.rstrip('/')
    if base_url.endswith('/v1'):
        base_url = base_url[:-3]
    
    return anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        base_url=base_url,
    )


def get_model() -> str:
    return settings.ANTHROPIC_MODEL
