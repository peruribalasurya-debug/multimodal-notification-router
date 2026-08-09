"""Stage 2: media understanding for the message notification router.

For each message with media_type in {image, voice}, resolves the referenced
file via images.csv / voice_notes.csv and extracts its content:

  - images: OCR text + a short visual description, in one call
  - voice notes: a transcript

Images prefer a single Claude vision call (OCR + visual description together,
since a vision model reads stylized poster text and layout better than raw
OCR alone) when ANTHROPIC_API_KEY is set; otherwise falls back to local
Tesseract OCR (text only — no visual description without a vision model).

Voice notes always use faster-whisper. The Anthropic Messages API has no
native audio input, so there is no "prefer the LLM" path for audio the way
there is for images — local ASR is mandatory, not a fallback.

Every extraction is cached to a local JSON file keyed by image_id /
voice_note_id, so the same file is never processed twice across runs.

See docs/architecture.md (Stage 2) for the design this implements.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
from typing import Any, Optional

import pandas as pd

try:
    from dotenv import load_dotenv

    load_dotenv()  # populates os.environ from a .env file at the repo root, if present
except ImportError:
    pass  # python-dotenv not installed -- fall back to whatever's already in the environment

CACHE_PATH_DEFAULT = os.path.join("src", ".cache", "media_cache.json")
# Kept in sync with router.py's DEFAULT_MODEL -- both read ROUTER_MODEL, so they must
# agree on the same cheapest-by-default model or an unset ROUTER_MODEL would silently
# route classification and image extraction to different models.
DEFAULT_MODEL = os.environ.get("ROUTER_MODEL", "claude-haiku-4-5")
DEFAULT_WHISPER_SIZE = os.environ.get("ROUTER_WHISPER_MODEL", "base")

# Common Windows install locations for the Tesseract-OCR binary, checked when it isn't
# already on PATH. Order: explicit env override, PATH, standard admin-installed locations,
# then the no-admin-required per-user location (LOCALAPPDATA) that a setup script can use
# on a machine without admin rights.
_TESSERACT_CANDIDATES = [
    os.environ.get("TESSERACT_CMD"),
    shutil.which("tesseract"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
]


def _resolve_tesseract_cmd() -> Optional[str]:
    for candidate in _TESSERACT_CANDIDATES:
        if candidate and os.path.exists(candidate):
            return candidate
    return None

IMAGE_PROMPT = (
    "Extract information from this WhatsApp image message. Respond with ONLY a JSON"
    " object (no markdown fences, no commentary) with exactly two keys:\n"
    '  "ocr_text": all legible text in the image, verbatim, in reading order.'
    ' Empty string if there is no text.\n'
    '  "visual_description": one or two sentences describing what the image visually'
    " shows — subject, layout, style — and calling out any urgency, marketing, or"
    " scam-style visual cues (banners, countdown graphics, spoofed logos, etc.) if"
    " present."
)


class MediaCache:
    """Flat JSON-backed cache: {"image:<id>": {...}, "voice:<id>": {...}}."""

    def __init__(self, path: str = CACHE_PATH_DEFAULT):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._data: dict[str, Any] = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self._data = json.load(f)

    def get(self, key: str) -> Any | None:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)


class MediaExtractor:
    def __init__(
        self,
        dataset_dir: str = "dataset",
        cache_path: str = CACHE_PATH_DEFAULT,
        model: str = DEFAULT_MODEL,
        whisper_model_size: str = DEFAULT_WHISPER_SIZE,
    ):
        self.dataset_dir = dataset_dir
        self.images = pd.read_csv(os.path.join(dataset_dir, "images.csv"))
        self.voice_notes = pd.read_csv(os.path.join(dataset_dir, "voice_notes.csv"))
        self.cache = MediaCache(cache_path)
        self.model = model
        self.whisper_model_size = whisper_model_size

        self._anthropic_client = None
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            try:
                import anthropic

                self._anthropic_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                pass

        self._whisper_model = None  # lazy-loaded on first actual use

    @property
    def llm_available(self) -> bool:
        return self._anthropic_client is not None

    # -- path resolution --------------------------------------------------

    def resolve_media_path(self, media_type: str, media_id: str) -> Optional[str]:
        if media_type == "image":
            rows = self.images[self.images.image_id == media_id]
        elif media_type == "voice":
            rows = self.voice_notes[self.voice_notes.voice_note_id == media_id]
        else:
            return None
        if rows.empty:
            return None
        return os.path.join(self.dataset_dir, rows.iloc[0].file_path)

    # -- public entry point -------------------------------------------------

    def extract_for_message(self, message: pd.Series) -> dict[str, Any]:
        """Resolve and extract the media (if any) referenced by a messages.csv row."""
        media_type = message.get("media_type")
        media_id = message.get("media_id")

        if pd.isna(media_type) or pd.isna(media_id):
            return {"media_type": None, "media_id": None, "file_path": None, "extraction": None}

        file_path = self.resolve_media_path(media_type, media_id)
        if file_path is None or not os.path.exists(file_path):
            return {
                "media_type": media_type,
                "media_id": media_id,
                "file_path": file_path,
                "extraction": {"method": "unavailable", "error": "file not found"},
            }

        if media_type == "image":
            extraction = self.extract_image(media_id, file_path)
        elif media_type == "voice":
            extraction = self.extract_voice(media_id, file_path)
        else:
            extraction = {"method": "unavailable", "error": f"unsupported media_type {media_type!r}"}

        return {
            "media_type": media_type,
            "media_id": media_id,
            "file_path": file_path,
            "extraction": extraction,
        }

    # -- images ---------------------------------------------------------------

    def extract_image(self, image_id: str, file_path: str) -> dict[str, Any]:
        cache_key = f"image:{image_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.llm_available:
            result = self._extract_image_via_llm(file_path)
        else:
            result = self._extract_image_via_tesseract(file_path)

        # Don't persist hard failures (no API key + no tesseract binary) — an
        # "unavailable" result should be retried on the next run once the
        # environment is fixed, not locked in forever by the cache.
        if result.get("method") != "unavailable":
            self.cache.set(cache_key, result)
        return result

    def _extract_image_via_llm(self, file_path: str) -> dict[str, Any]:
        media_type = "image/png" if file_path.lower().endswith(".png") else "image/jpeg"
        with open(file_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")

        try:
            response = self._anthropic_client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {"type": "base64", "media_type": media_type, "data": data},
                            },
                            {"type": "text", "text": IMAGE_PROMPT},
                        ],
                    }
                ],
            )
        except Exception as exc:  # network error, auth error, rate limit, etc.
            fallback = self._extract_image_via_tesseract(file_path)
            fallback["method"] = "tesseract_fallback_after_llm_error"
            fallback["llm_error"] = str(exc)
            return fallback

        if getattr(response, "stop_reason", None) == "refusal":
            fallback = self._extract_image_via_tesseract(file_path)
            fallback["method"] = "tesseract_fallback_after_llm_refusal"
            return fallback

        text = "".join(block.text for block in response.content if block.type == "text")
        parsed = self._parse_json_object(text)
        if parsed is None:
            return {"method": "llm_vision_unparseable", "ocr_text": None, "visual_description": None, "raw_response": text}

        return {
            "method": "llm_vision",
            "ocr_text": parsed.get("ocr_text", ""),
            "visual_description": parsed.get("visual_description", ""),
        }

    def _extract_image_via_tesseract(self, file_path: str) -> dict[str, Any]:
        try:
            import pytesseract
            from PIL import Image

            cmd = _resolve_tesseract_cmd()
            if cmd:
                pytesseract.pytesseract.tesseract_cmd = cmd

            text = pytesseract.image_to_string(Image.open(file_path)).strip()
            return {"method": "tesseract", "ocr_text": text, "visual_description": None}
        except Exception as exc:
            return {
                "method": "unavailable",
                "ocr_text": None,
                "visual_description": None,
                "error": str(exc),
            }

    @staticmethod
    def _parse_json_object(text: str) -> Optional[dict[str, Any]]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return None
            return None

    # -- voice notes ------------------------------------------------------

    def extract_voice(self, voice_note_id: str, file_path: str) -> dict[str, Any]:
        cache_key = f"voice:{voice_note_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._extract_voice_via_whisper(file_path)
        if result.get("method") != "unavailable":
            self.cache.set(cache_key, result)
        return result

    def _get_whisper_model(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel

            self._whisper_model = WhisperModel(
                self.whisper_model_size, device="cpu", compute_type="int8"
            )
        return self._whisper_model

    def _extract_voice_via_whisper(self, file_path: str) -> dict[str, Any]:
        try:
            model = self._get_whisper_model()
            segments, info = model.transcribe(file_path, beam_size=5)
            transcript = " ".join(seg.text.strip() for seg in segments).strip()
            return {
                "method": "faster_whisper",
                "transcript": transcript,
                "language": info.language,
                "language_probability": round(float(info.language_probability), 3),
            }
        except Exception as exc:
            return {"method": "unavailable", "transcript": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# Quick test: extract 2 images and 2 voice notes referenced by messages.csv
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    extractor = MediaExtractor(dataset_dir="dataset")
    print(f"LLM vision available (ANTHROPIC_API_KEY set): {extractor.llm_available}\n")

    messages = pd.read_csv(os.path.join("dataset", "messages.csv"))

    image_msgs = messages[messages.media_type == "image"].head(2)
    voice_msgs = messages[messages.media_type == "voice"].head(2)

    for label, subset in (("IMAGE", image_msgs), ("VOICE", voice_msgs)):
        for _, row in subset.iterrows():
            print(f"=== {label} - message {row.message_id} (media_id={row.media_id}) ===")
            result = extractor.extract_for_message(row)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()
