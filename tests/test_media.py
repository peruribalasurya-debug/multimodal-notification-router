"""Media invariants that must never regress:

- Extraction results are cached: a second extract_image()/extract_voice() call for
  the same media_id never re-invokes the (real or mocked) extraction backend.
- A missing media file -- whether the file itself is absent from disk or the
  media_id was never registered in images.csv/voice_notes.csv at all, or the file
  exists but is unreadable -- degrades gracefully to an "unavailable" extraction
  rather than raising. End to end, that flows through Router.route() as
  action=digest, message_type=unknown, with confidence kept out of the
  high-confidence band (never treated as a confident decision).
"""

from __future__ import annotations

from conftest import make_message_row


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

def test_image_extraction_is_cached_on_repeat_calls(make_media_extractor, tmp_path, monkeypatch):
    extractor = make_media_extractor()
    fake_image_path = tmp_path / "fake.png"
    fake_image_path.write_bytes(b"stand-in image bytes")

    calls: list[str] = []

    def fake_extract(file_path: str) -> dict:
        calls.append(file_path)
        return {"method": "tesseract", "ocr_text": "hello", "visual_description": None}

    monkeypatch.setattr(extractor, "_extract_image_via_tesseract", fake_extract)

    result1 = extractor.extract_image("img_1", str(fake_image_path))
    result2 = extractor.extract_image("img_1", str(fake_image_path))

    assert len(calls) == 1, "extraction backend should only run once; the second call must hit the cache"
    assert result1 == result2 == {"method": "tesseract", "ocr_text": "hello", "visual_description": None}


def test_voice_extraction_is_cached_on_repeat_calls(make_media_extractor, tmp_path, monkeypatch):
    extractor = make_media_extractor()
    fake_audio_path = tmp_path / "fake.ogg"
    fake_audio_path.write_bytes(b"stand-in audio bytes")

    calls: list[str] = []

    def fake_extract(file_path: str) -> dict:
        calls.append(file_path)
        return {"method": "faster_whisper", "transcript": "hello there", "language": "en", "language_probability": 0.99}

    monkeypatch.setattr(extractor, "_extract_voice_via_whisper", fake_extract)

    result1 = extractor.extract_voice("voice_1", str(fake_audio_path))
    result2 = extractor.extract_voice("voice_1", str(fake_audio_path))

    assert len(calls) == 1, "extraction backend should only run once; the second call must hit the cache"
    assert result1 == result2


def test_cache_persists_across_extractor_instances(dataset_builder, tmp_path, monkeypatch):
    """The cache is a file on disk, not an in-memory fixture of one instance --
    confirms a second MediaExtractor pointed at the same cache path reuses it."""
    from media import MediaExtractor

    dataset_dir = dataset_builder.write()
    cache_path = str(tmp_path / "shared_media_cache.json")
    fake_image_path = tmp_path / "fake.png"
    fake_image_path.write_bytes(b"stand-in image bytes")

    extractor1 = MediaExtractor(dataset_dir, cache_path=cache_path)
    monkeypatch.setattr(
        extractor1, "_extract_image_via_tesseract",
        lambda file_path: {"method": "tesseract", "ocr_text": "first run", "visual_description": None},
    )
    extractor1.extract_image("img_shared", str(fake_image_path))

    extractor2 = MediaExtractor(dataset_dir, cache_path=cache_path)
    calls: list[str] = []
    monkeypatch.setattr(extractor2, "_extract_image_via_tesseract", lambda fp: calls.append(fp) or {})

    result = extractor2.extract_image("img_shared", str(fake_image_path))

    assert calls == [], "a fresh extractor instance sharing the cache file must not re-extract"
    assert result["ocr_text"] == "first run"


# ---------------------------------------------------------------------------
# Missing / unreadable media -> graceful degradation, never a crash
# ---------------------------------------------------------------------------

def test_missing_file_on_disk_degrades_to_unavailable(dataset_builder, make_media_extractor):
    dataset_builder.add_image("img_missing", "media/images/does_not_exist.png")
    extractor = make_media_extractor()

    msg = make_message_row(media_type="image", media_id="img_missing")
    result = extractor.extract_for_message(msg)

    assert result["extraction"]["method"] == "unavailable"


def test_media_id_never_registered_degrades_to_unavailable(dataset_builder, make_media_extractor):
    extractor = make_media_extractor()  # no images.csv rows at all

    msg = make_message_row(media_type="image", media_id="img_never_registered")
    result = extractor.extract_for_message(msg)

    assert result["extraction"]["method"] == "unavailable"
    assert result["file_path"] is None


def test_missing_voice_file_degrades_to_unavailable(dataset_builder, make_media_extractor):
    dataset_builder.add_voice_note("voice_missing", "media/audio/does_not_exist.ogg")
    extractor = make_media_extractor()

    msg = make_message_row(media_type="voice", media_id="voice_missing")
    result = extractor.extract_for_message(msg)

    assert result["extraction"]["method"] == "unavailable"


def test_corrupt_image_file_degrades_gracefully_not_crash(make_media_extractor, tmp_path):
    extractor = make_media_extractor()
    bad_path = tmp_path / "corrupt.png"
    bad_path.write_bytes(b"this is not a valid png file at all")

    result = extractor.extract_image("img_bad", str(bad_path))

    assert result["method"] == "unavailable"


def test_no_media_referenced_returns_empty_extraction_not_crash(make_media_extractor):
    extractor = make_media_extractor()
    msg = make_message_row(media_type=None, media_id=None)

    result = extractor.extract_for_message(msg)

    assert result == {"media_type": None, "media_id": None, "file_path": None, "extraction": None}


# ---------------------------------------------------------------------------
# End to end via Router: missing media -> digest/unknown, not a confident guess
# ---------------------------------------------------------------------------

def test_router_degrades_to_digest_unknown_with_non_confident_score_when_media_missing(
    dataset_builder, make_router
):
    dataset_builder.add_user("u_1")
    router = make_router()

    msg = make_message_row(
        user_id="u_1", conversation_type="personal", sender_user_id="u_total_stranger",
        message_text=None, media_type="image", media_id="img_missing_entirely",
    )
    result = router.route(msg)

    assert result["action"] == "digest"
    assert result["message_type"] == "unknown"
    # Never lands in the high-confidence band (0.85-0.95) reserved for
    # unambiguous cases like scam -- a missing-media guess must not present as
    # confident.
    assert result["confidence"] < 0.8
