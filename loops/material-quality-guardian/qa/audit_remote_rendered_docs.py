from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import urllib.error
import urllib.request

from common import repo_root


ROOT = repo_root()


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"])
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def skill_roots() -> list[str]:
    skills_root = ROOT / "docs" / "skills"
    roots: list[str] = ["/skills/"]
    for index in sorted(skills_root.glob("*/index.md")):
        roots.append(f"/skills/{index.parent.name}/")
    return roots


def fetch(url: str, timeout: int) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "material-quality-guardian/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, response.headers.get("Content-Type", ""), body


def check_url(url: str, timeout: int) -> tuple[int | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "material-quality-guardian/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, None
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def same_site_content_link(base_url: str, href: str) -> str | None:
    if not href or href.startswith(("#", "mailto:", "javascript:")):
        return None
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    if not (parsed.path.startswith("/skills/") or parsed.path.startswith("/skill-static/")):
        return None
    if parsed.fragment:
        absolute = absolute.split("#", 1)[0]
    return absolute


def crawl_rendered_docs(remote_base_url: str, timeout: int) -> dict[str, object]:
    root_url = remote_base_url.rstrip("/")
    checked_pages: list[dict[str, object]] = []
    broken_links: list[dict[str, object]] = []
    seen_links: set[str] = set()

    for path in skill_roots():
        url = root_url + path
        try:
            status, content_type, body = fetch(url, timeout)
        except Exception as exc:  # noqa: BLE001
            broken_links.append(
                {
                    "source": path,
                    "target": url,
                    "status": None,
                    "error": str(exc),
                }
            )
            continue

        parser = AnchorParser()
        parser.feed(body)
        checked_pages.append(
            {
                "url": url,
                "status": status,
                "content_type": content_type,
                "title": parser.title.strip(),
                "link_count": len(parser.links),
            }
        )

        for href in parser.links:
            absolute = same_site_content_link(url, href)
            if not absolute or absolute in seen_links:
                continue
            seen_links.add(absolute)
            link_status, error = check_url(absolute, timeout)
            if link_status != 200:
                broken_links.append(
                    {
                        "source": url,
                        "target": absolute,
                        "status": link_status,
                        "error": error,
                    }
                )

    return {
        "status": "ok" if not broken_links else "broken-links",
        "checked_page_count": len(checked_pages),
        "checked_link_count": len(seen_links),
        "pages": checked_pages,
        "broken_links": broken_links,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit rendered remote docs pages and same-site content links.")
    parser.add_argument("--remote-base-url", default="http://docs.haohaoxiaoyu.top:8888")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--output")
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args()

    result = crawl_rendered_docs(args.remote_base_url, args.timeout)
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[check] remote-rendered-docs")
    print(f"[target] {args.remote_base_url}")
    print(f"[status] {result.get('status')}")
    print(f"[pages] {result.get('checked_page_count')}")
    print(f"[links] {result.get('checked_link_count')}")
    broken_links = result.get("broken_links", [])
    if isinstance(broken_links, list) and broken_links:
        for item in broken_links:
            if isinstance(item, dict):
                print(f"[broken] {item.get('target')} :: status={item.get('status')}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.fail_on_broken and result["status"] != "ok":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
