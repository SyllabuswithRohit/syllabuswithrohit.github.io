from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from validate_static_library import validate  # noqa: E402


VALID_SERVICE_WORKER = """
const CACHE_NAME = 'fixture-v2';
const urlsToCache = ['./index.html', './manifest.json', './myprofile.jpg', './qr.png'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => Promise.allSettled(urlsToCache.map(url => cache.add(url)))));
});
self.addEventListener('fetch', event => {
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(fetchResponse => {
    const requestUrl = new URL(event.request.url);
    if (fetchResponse.ok && requestUrl.origin === self.location.origin) return fetchResponse;
    return fetchResponse;
  }).catch(async () => {
    if (event.request.mode === 'navigate') return caches.match('./index.html');
    return new Response('Offline', { status: 504 });
  })));
});
"""


class StaticLibraryValidatorTest(unittest.TestCase):
    def create_fixture(self, root: pathlib.Path) -> None:
        (root / "books").mkdir(parents=True)
        (root / "index.html").write_text(
            """<!doctype html><html><body id="home">
            <img src="myprofile.jpg" alt="Profile">
            <a href="books/book.html">Read</a>
            <script src="sw.js"></script>
            </body></html>""",
            encoding="utf-8",
        )
        (root / "books/book.html").write_text(
            '<!doctype html><html><body id="book"><a href="../index.html">Library</a></body></html>',
            encoding="utf-8",
        )
        (root / "manifest.json").write_text(
            """{
              "name": "Fixture Library",
              "short_name": "Fixture",
              "start_url": "./index.html",
              "display": "standalone",
              "icons": [{"src": "myprofile.jpg", "sizes": "192x192", "type": "image/jpeg"}]
            }""",
            encoding="utf-8",
        )
        (root / "sw.js").write_text(VALID_SERVICE_WORKER, encoding="utf-8")
        (root / "myprofile.jpg").write_bytes(b"fixture-image")
        (root / "qr.png").write_bytes(b"fixture-qr")

    def test_accepts_a_complete_offline_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            self.create_fixture(root)
            report = validate(root)
            self.assertTrue(report.valid, report.errors)
            self.assertEqual(report.html_files, 2)
            self.assertGreaterEqual(report.local_references, 4)

    def test_rejects_a_missing_local_book_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            self.create_fixture(root)
            (root / "books/book.html").unlink()
            report = validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any("missing local target" in error for error in report.errors))

    def test_rejects_duplicate_ids_and_images_without_alt_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            self.create_fixture(root)
            (root / "index.html").write_text(
                """<!doctype html><html><body>
                <div id="duplicate"></div><div id="duplicate"></div>
                <img src="myprofile.jpg">
                </body></html>""",
                encoding="utf-8",
            )
            report = validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any("duplicate HTML id" in error for error in report.errors))
            self.assertTrue(any("non-empty alt text" in error for error in report.errors))

    def test_rejects_service_worker_without_a_real_offline_response(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            self.create_fixture(root)
            (root / "sw.js").write_text(
                "const CACHE_NAME='bad'; const x='./index.html';",
                encoding="utf-8",
            )
            report = validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any("offline navigation fallback" in error for error in report.errors))
            self.assertTrue(any("return a Response" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
