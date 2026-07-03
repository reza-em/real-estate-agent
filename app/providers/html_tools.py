from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser


class StructuredHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: dict[str, list[str]] = defaultdict(list)
        self.scripts: list[tuple[dict[str, str], str]] = []
        self._anchor_href: str | None = None
        self._anchor_parts: list[str] = []
        self._script_attrs: dict[str, str] | None = None
        self._script_parts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "a" and attributes.get("href"):
            self._anchor_href = attributes["href"]
            self._anchor_parts = []
        elif tag == "script":
            self._script_attrs = attributes
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._anchor_href is not None:
            self._anchor_parts.append(data)
        if self._script_attrs is not None:
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href is not None:
            text = " ".join("".join(self._anchor_parts).split())
            if text:
                self.anchors[self._anchor_href].append(text)
            self._anchor_href = None
            self._anchor_parts = []
        elif tag == "script" and self._script_attrs is not None:
            self.scripts.append(
                (self._script_attrs, "".join(self._script_parts).strip())
            )
            self._script_attrs = None
            self._script_parts = []


def parse_html(value: str) -> StructuredHtmlParser:
    parser = StructuredHtmlParser()
    parser.feed(value)
    parser.close()
    return parser
