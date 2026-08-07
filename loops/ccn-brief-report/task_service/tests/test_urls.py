from __future__ import annotations

from app.domain.urls import normalize_http_iri


def test_normalize_http_iri_decodes_utf8_path_but_preserves_ascii_escapes():
    value = (
        "https://example.test/%E5%AD%A6%E6%9C%AF/"
        "report%20name%2Fpart"
    )

    assert normalize_http_iri(value) == "https://example.test/学术/report%20name%2Fpart"


def test_normalize_http_iri_is_stable_for_unicode_input():
    value = "https://example.test/学术论文分析/报告"

    assert normalize_http_iri(value) == value
