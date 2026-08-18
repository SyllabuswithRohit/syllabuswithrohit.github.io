#!/usr/bin/env python3
"""Validate the preserved GitHub Pages Library without network access."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit


PRIVATE_KEY = re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")
CREDENTIAL = re.compile(
    r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})"
)
INSECURE_HTTP = re.compile(r"http://", re.IGNORECASE)
CACHE_LOCAL = re.compile(r"['\"](\./[^'\"]+)['\"]")
TEXT_SUFFIXES = {
    ".html",
    ".htm",
    ".js",
    ".json",
    ".css",
    ".md",
    ".txt",
    ".xml",
    ".webmanifest",
}
SKIPPED_SCHEMES = {
    "data",
    "mailto",
    "tel",
    "upi",
    "blob",
}


@dataclass(frozen=True)
class Reference:
    source: pathlib.Path
    attribute: str
    value: str


class PageParser(HTMLParser):
    def __init__(self, source: pathlib.Path) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.references: list[Reference] = []
        self.ids: list[str] = []
        self.images_without_alt: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value for name, value in attrs}
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        for attribute in ("href", "src", "poster"):
            value = values.get(attribute)
            if value:
                self.references.append(Reference(self.source, attribute, value.strip()))
        if tag.lower() == "img":
            alt = values.get("alt")
            if alt is None or not alt.strip():
                self.images_without_alt.append(values.get("src") or "<unknown image>")


@dataclass
class ValidationReport:
    errors: list[str]
    warnings: list[str]
    tracked_files: int = 0
    html_files: int = 0
    local_references: int = 0
    external_references: int = 0

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_json(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "valid": self.valid,
            "trackedFiles": self.tracked_files,
            "htmlFiles": self.html_files,
            "localReferences": self.local_references,
            "externalReferences": self.external_references,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def tracked_paths(root: pathlib.Path) -> list[pathlib.Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode == 0:
        return [
            root / path.decode("utf-8")
            for path in completed.stdout.split(b"\0")
            if path
        ]
    return sorted(path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts)


def display(root: pathlib.Path, path: pathlib.Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def resolve_local_reference(root: pathlib.Path, source: pathlib.Path, value: str) -> pathlib.Path | None:
    if not value or value.startswith("#") or value.startswith("//"):
        return None
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    if scheme in SKIPPED_SCHEMES or scheme in {"http", "https"}:
        return None
    if scheme:
        raise ValueError(f"unsupported URL scheme {scheme!r}")
    decoded = unquote(parsed.path)
    if not decoded:
        return None
    if "\x00" in decoded:
        raise ValueError("NUL byte in path")
    candidate = root / decoded.lstrip("/") if decoded.startswith("/") else source.parent / decoded
    candidate = candidate.resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as failure:
        raise ValueError("local reference escapes repository root") from failure
    if decoded.endswith("/"):
        candidate = candidate / "index.html"
    return candidate


def validate_manifest(root: pathlib.Path, report: ValidationReport) -> None:
    path = root / "manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as failure:
        report.errors.append(f"manifest.json: cannot parse manifest: {failure}")
        return
    if not isinstance(manifest, dict):
        report.errors.append("manifest.json: top level must be an object")
        return
    for key in ("name", "short_name", "start_url", "display", "icons"):
        if key not in manifest:
            report.errors.append(f"manifest.json: missing {key}")
    start_url = manifest.get("start_url")
    if isinstance(start_url, str):
        try:
            target = resolve_local_reference(root, path, start_url)
            if target is not None and not target.is_file():
                report.errors.append(f"manifest.json: start_url target is missing: {start_url}")
        except ValueError as failure:
            report.errors.append(f"manifest.json: invalid start_url {start_url!r}: {failure}")
    icons = manifest.get("icons")
    if not isinstance(icons, list) or not icons:
        report.errors.append("manifest.json: icons must be a non-empty array")
        return
    for index, icon in enumerate(icons):
        if not isinstance(icon, dict):
            report.errors.append(f"manifest.json: icons[{index}] must be an object")
            continue
        source = icon.get("src")
        if not isinstance(source, str) or not source.strip():
            report.errors.append(f"manifest.json: icons[{index}].src is required")
            continue
        try:
            target = resolve_local_reference(root, path, source)
            if target is None or not target.is_file():
                report.errors.append(f"manifest.json: icon target is missing: {source}")
        except ValueError as failure:
            report.errors.append(f"manifest.json: invalid icon source {source!r}: {failure}")


def validate_service_worker(root: pathlib.Path, report: ValidationReport) -> None:
    path = root / "sw.js"
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as failure:
        report.errors.append(f"sw.js: cannot read service worker: {failure}")
        return
    required_fragments = {
        "Promise.allSettled": "install must await independent cache attempts",
        "fetchResponse.ok": "runtime cache must reject failed HTTP responses",
        "requestUrl.origin === self.location.origin": "runtime page caching must remain same-origin",
        "event.request.mode === 'navigate'": "offline navigation fallback is required",
        "status: 504": "non-navigation offline failure must return a Response",
    }
    for fragment, message in required_fragments.items():
        if fragment not in source:
            report.errors.append(f"sw.js: {message}")
    cache_match = re.search(r"CACHE_NAME\s*=\s*['\"]([^'\"]+)['\"]", source)
    if not cache_match or not cache_match.group(1).strip():
        report.errors.append("sw.js: CACHE_NAME must be a non-empty literal")
    for value in CACHE_LOCAL.findall(source):
        try:
            target = resolve_local_reference(root, path, value)
            if target is not None and not target.is_file():
                report.errors.append(f"sw.js: cached local target is missing: {value}")
        except ValueError as failure:
            report.errors.append(f"sw.js: invalid cached target {value!r}: {failure}")


def validate_text_safety(root: pathlib.Path, paths: Iterable[pathlib.Path], report: ValidationReport) -> None:
    for path in paths:
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "CNAME"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative = display(root, path)
        if PRIVATE_KEY.search(text):
            report.errors.append(f"{relative}: private-key marker is prohibited")
        if CREDENTIAL.search(text):
            report.errors.append(f"{relative}: credential-like token is prohibited")
        if INSECURE_HTTP.search(text):
            report.errors.append(f"{relative}: insecure http:// reference is prohibited")


def validate_html(root: pathlib.Path, paths: Iterable[pathlib.Path], report: ValidationReport) -> None:
    for path in sorted(path for path in paths if path.suffix.lower() in {".html", ".htm"}):
        report.html_files += 1
        relative = display(root, path)
        try:
            parser = PageParser(path)
            parser.feed(path.read_text(encoding="utf-8"))
            parser.close()
        except (OSError, UnicodeDecodeError) as failure:
            report.errors.append(f"{relative}: cannot parse HTML: {failure}")
            continue
        duplicate_ids = sorted(identifier for identifier, count in Counter(parser.ids).items() if count > 1)
        if duplicate_ids:
            report.errors.append(f"{relative}: duplicate HTML id values: {', '.join(duplicate_ids)}")
        for image in parser.images_without_alt:
            report.errors.append(f"{relative}: image requires non-empty alt text: {image}")
        for reference in parser.references:
            value = reference.value
            parsed = urlsplit(value)
            if parsed.scheme.lower() in {"http", "https"} or value.startswith("//"):
                report.external_references += 1
                if parsed.scheme.lower() == "http":
                    report.errors.append(f"{relative}: insecure external reference: {value}")
                continue
            if parsed.scheme.lower() in SKIPPED_SCHEMES:
                continue
            if parsed.scheme.lower() == "javascript":
                report.errors.append(f"{relative}: javascript: URL is prohibited in {reference.attribute}")
                continue
            try:
                target = resolve_local_reference(root, path, value)
            except ValueError as failure:
                report.errors.append(f"{relative}: invalid {reference.attribute}={value!r}: {failure}")
                continue
            if target is None:
                continue
            report.local_references += 1
            if not target.exists():
                report.errors.append(
                    f"{relative}: missing local target for {reference.attribute}={value!r}"
                )


def validate(root: pathlib.Path) -> ValidationReport:
    report = ValidationReport(errors=[], warnings=[])
    required = ["index.html", "manifest.json", "sw.js", "myprofile.jpg", "qr.png"]
    for relative in required:
        if not (root / relative).is_file():
            report.errors.append(f"missing required site file: {relative}")
    paths = tracked_paths(root)
    report.tracked_files = len(paths)
    validate_html(root, paths, report)
    validate_manifest(root, report)
    validate_service_worker(root, report)
    validate_text_safety(root, paths, report)
    if report.html_files == 0:
        report.errors.append("no tracked HTML files were found")
    if not (root / "books").is_dir():
        report.warnings.append("books/ directory is absent")
    return report


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--output", type=pathlib.Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(argv or sys.argv[1:])
    root = arguments.root.resolve()
    report = validate(root)
    encoded = json.dumps(report.to_json(), indent=2, sort_keys=True) + "\n"
    print(encoded, end="")
    if arguments.output:
        output = arguments.output
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
