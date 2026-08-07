from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from pydantic import HttpUrl, TypeAdapter

from app.domain.percent_encoding import decode_non_ascii_percent_escapes


HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


def normalize_http_iri(value: str) -> str:
    """Validate an HTTP URL and return a stable Unicode-path representation."""
    canonical = str(HTTP_URL_ADAPTER.validate_python(value))
    parsed = urlsplit(canonical)
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            decode_non_ascii_percent_escapes(parsed.path),
            parsed.query,
            parsed.fragment,
        )
    )
