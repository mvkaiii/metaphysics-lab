import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.build_bazi_decadal_external_source_binding import (
    build_external_source_binding,
    sha256_file,
)


class BaziDecadalExternalSourceBindingTests(unittest.TestCase):
    def test_hashes_raw_bytes_without_normalization(self):
        raw = b"line1\r\nline2\n\x00binary"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.html"
            path.write_bytes(raw)
            self.assertEqual(sha256_file(path), hashlib.sha256(raw).hexdigest())

    def test_binding_matches_preoracle_source_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Solar_Term_2016.htm"
            path.write_bytes(b"exact-hko-bytes")
            binding = build_external_source_binding(
                path,
                provider="Hong Kong Observatory",
                source_url="https://www.hko.gov.hk/en/gts/astron2016/Solar_Term_2016.htm",
                timezone="UTC+08:00",
                published_precision_seconds=60,
            )
            self.assertEqual(
                set(binding),
                {
                    "provider",
                    "role",
                    "source_url",
                    "source_file_label",
                    "source_sha256",
                    "timezone",
                    "published_precision_seconds",
                },
            )
            self.assertEqual(binding["role"], "astronomical_input")
            self.assertEqual(binding["source_file_label"], "Solar_Term_2016.htm")
            self.assertEqual(
                binding["source_sha256"],
                hashlib.sha256(b"exact-hko-bytes").hexdigest(),
            )

    def test_empty_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty"
            path.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "must not be empty"):
                sha256_file(path)

    def test_invalid_precision_and_non_https_url_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source"
            path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "positive integer"):
                build_external_source_binding(
                    path,
                    provider="Hong Kong Observatory",
                    source_url="https://example.test/source",
                    timezone="UTC+08:00",
                    published_precision_seconds=0,
                )
            with self.assertRaisesRegex(ValueError, "https URL"):
                build_external_source_binding(
                    path,
                    provider="Hong Kong Observatory",
                    source_url="http://example.test/source",
                    timezone="UTC+08:00",
                    published_precision_seconds=60,
                )


if __name__ == "__main__":
    unittest.main()
