"""Resolve request-driven language codes for serializers / translations."""

from django.conf import settings


def negotiate_request_lang(request, default_override: bool = True):
    """Return a short language code usable with translation.override()."""
    default = getattr(settings, "LANGUAGE_CODE", "fa")
    accept = getattr(request, "META", {}).get("HTTP_ACCEPT_LANGUAGE", "") or ""
    lang_code = accept.split(",")[0].strip().split("-")[0].lower() or default
    supported = {code for code, _ in getattr(settings, "LANGUAGES", [])}
    if lang_code not in supported:
        lang_code = str(default).split("-")[0].lower()
    return lang_code


def resolve_public_factor_pdf_lang(request) -> str:
    """
    Language for anonymous public factor PDF downloads.

    Matches the frontend default (Persian). Optional ``?lang=fa|en`` overrides;
    ``Accept-Language`` is ignored so English browser defaults do not change the PDF.
    """
    default = str(getattr(settings, "LANGUAGE_CODE", "fa")).split("-")[0].lower()
    supported = {code for code, _ in getattr(settings, "LANGUAGES", [])}
    query = (request.query_params.get("lang") or "").strip().lower()[:2]
    if query in supported:
        return query
    return default
