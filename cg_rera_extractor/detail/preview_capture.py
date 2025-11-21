from __future__ import annotations

"""Utilities for detecting and capturing preview artifacts from detail pages."""

import json
import logging
from pathlib import Path
from typing import Dict

from playwright.sync_api import (  # type: ignore
    BrowserContext,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from cg_rera_extractor.detail.storage import make_preview_dir
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.parsing.schema import PreviewArtifact, V1Project

LOGGER = logging.getLogger(__name__)


def build_preview_placeholders(
    html: str,
    *,
    source_file: str,
    state_code: str,
    registration_number: str | None,
    project_name: str | None,
) -> Dict[str, PreviewArtifact]:
    """Parse HTML and return preview placeholders keyed by field key."""

    raw = extract_raw_from_html(
        html,
        source_file=source_file,
        registration_number=registration_number,
        project_name=project_name,
    )
    v1: V1Project = map_raw_to_v1(raw, state_code=state_code)
    return dict(v1.previews)


def capture_previews(
    *,
    page: Page,
    context: BrowserContext,
    project_key: str,
    output_base: Path,
    preview_placeholders: Dict[str, PreviewArtifact],
) -> Dict[str, PreviewArtifact]:
    """Click preview controls and persist any captured artifacts."""

    captured: Dict[str, PreviewArtifact] = {}
    LOGGER.info("Collecting preview images / HTML...")
    for placeholder in preview_placeholders.values():
        field_key = placeholder.field_key
        target_dir = make_preview_dir(str(output_base), project_key, field_key)
        target_dir.mkdir(parents=True, exist_ok=True)
        artifact = PreviewArtifact(**placeholder.model_dump())

        locator = _resolve_locator(page, placeholder.notes)
        if locator is None:
            LOGGER.info("Preview element not found for %s", field_key)
            artifact.notes = _merge_notes(artifact.notes, "Preview element not found")
            captured[field_key] = artifact
            continue

        try:
            LOGGER.info("Clicking preview button for %s", field_key)
            with page.expect_popup(timeout=5_000) as popup_info:
                locator.click()
            new_page = popup_info.value
            LOGGER.info("Collecting preview images / HTML for %s", field_key)
            artifact = _save_page_artifact(
                new_page,
                context,
                artifact,
                target_dir,
                output_base,
                prefix="preview",
            )
            new_page.close()
        except PlaywrightTimeoutError:
            # Popup did not appear. The click already happened.
            # Check for inline modal without clicking again.
            LOGGER.info("Falling back to inline modal capture for %s", field_key)
            artifact = _capture_inline_modal(
                locator,
                page,
                artifact,
                target_dir,
                output_base,
                click_needed=False,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Preview click failed for %s: %s", field_key, exc)
            artifact.notes = _merge_notes(artifact.notes, str(exc))

        captured[field_key] = artifact

    LOGGER.info("Completed preview capture for %d artifacts", len(captured))
    return captured


def save_preview_metadata(
    output_base: Path, project_key: str, previews: Dict[str, PreviewArtifact]
) -> None:
    target_dir = make_preview_dir(str(output_base), project_key)
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {key: artifact.model_dump(mode="json") for key, artifact in previews.items()}
    (target_dir / "metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_preview_metadata(preview_dir: Path) -> Dict[str, PreviewArtifact]:
    metadata_file = preview_dir / "metadata.json"
    if not metadata_file.exists():
        return {}
    raw = json.loads(metadata_file.read_text(encoding="utf-8"))
    return {key: PreviewArtifact(**value) for key, value in raw.items()}


def _resolve_locator(page: Page, hint: str | None) -> Locator | None:
    if not hint:
        try:
            return page.get_by_text("Preview")
        except Exception:
            return None

    if hint.startswith(("#", ".")):
        try:
            return page.locator(hint)
        except Exception:
            LOGGER.debug("Failed to resolve locator for hint %s", hint)
    elif hint.lower().startswith("http"):
        return None
    else:
        try:
            return page.get_by_text(hint)
        except Exception:
            LOGGER.debug("Failed to resolve text locator for hint %s", hint)
    return None


def _save_page_artifact(
    new_page: Page,
    context: BrowserContext,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    *,
    prefix: str,
) -> PreviewArtifact:
    try:
        new_page.wait_for_load_state("load", timeout=5_000)
    except Exception:
        pass

    url = new_page.url
    if url:
        artifact = _download_url(context, url, artifact, target_dir, output_base, prefix)
        if artifact.files:
            return artifact

    try:
        html_content = new_page.content()
        file_path = target_dir / f"{prefix}.html"
        file_path.write_text(html_content, encoding="utf-8")
        artifact.artifact_type = "html"
        artifact.files.append(str(file_path.relative_to(output_base)))
    except Exception as exc:  # pragma: no cover - defensive
        artifact.notes = _merge_notes(artifact.notes, f"Failed to save preview HTML: {exc}")
    return artifact


def _download_url(
    context: BrowserContext,
    url: str,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    prefix: str,
) -> PreviewArtifact:
    LOGGER.info("Downloading artifact: %s", url)
    try:
        response = context.request.get(url, timeout=10_000)
        content_type = response.headers.get("content-type", "")
        body = response.body()
        extension = _extension_from_content_type(content_type)
        file_path = target_dir / f"{prefix}{extension}"
        mode = "wb" if isinstance(body, (bytes, bytearray)) else "w"
        with open(file_path, mode) as handle:
            handle.write(body if mode == "wb" else str(body))
        artifact.artifact_type = _artifact_type_from_content_type(content_type)
        artifact.files.append(str(file_path.relative_to(output_base)))
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.debug("Failed to download preview resource %s: %s", url, exc)
        artifact.notes = _merge_notes(artifact.notes, f"Download failed: {exc}")
    return artifact


def _capture_inline_modal(
    locator: Locator,
    page: Page,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    click_needed: bool = True,
) -> PreviewArtifact:
    if click_needed:
        try:
            locator.click()
        except Exception as exc:  # pragma: no cover - defensive logging
            artifact.notes = _merge_notes(artifact.notes, f"Preview click failed: {exc}")
            return artifact

    modal = _wait_for_modal(page)
    if modal is None:
        artifact.notes = _merge_notes(artifact.notes, "No preview modal detected")
        return artifact

    LOGGER.info("Collecting preview images / HTML for %s (inline modal)", artifact.field_key)
    try:
        inner = modal.inner_html()
        html_path = target_dir / "modal_1.html"
        html_path.write_text(inner, encoding="utf-8")
        artifact.files.append(str(html_path.relative_to(output_base)))
        artifact.artifact_type = "html"
    except Exception as exc:  # pragma: no cover - defensive logging
        artifact.notes = _merge_notes(artifact.notes, f"Modal capture failed: {exc}")

    try:
        screenshot_path = target_dir / "modal_1.png"
        modal.screenshot(path=str(screenshot_path))
        artifact.files.append(str(screenshot_path.relative_to(output_base)))
    except Exception:
        LOGGER.debug("Modal screenshot skipped")

    _close_modal_if_possible(modal)
    return artifact


def _wait_for_modal(page: Page) -> Locator | None:
    modal_selectors = [".modal-dialog", ".modal.show", "#modal", "[role='dialog']"]
    for selector in modal_selectors:
        try:
            modal = page.wait_for_selector(selector, timeout=3_000)
            if modal:
                return modal
        except Exception:
            continue
    return None


def _close_modal_if_possible(modal: Locator) -> None:
    try:
        close_btn = modal.locator("button", has_text="Close")
        close_btn.click()
        return
    except Exception:
        pass
    try:
        modal.press("Escape")
    except Exception:
        return


def _extension_from_content_type(content_type: str) -> str:
    lowered = content_type.lower()
    if "pdf" in lowered:
        return ".pdf"
    if "png" in lowered:
        return ".png"
    if "jpg" in lowered or "jpeg" in lowered:
        return ".jpg"
    if "html" in lowered:
        return ".html"
    return ".bin"


def _artifact_type_from_content_type(content_type: str) -> str:
    lowered = content_type.lower()
    if "pdf" in lowered:
        return "pdf"
    if any(ext in lowered for ext in ("png", "jpg", "jpeg")):
        return "image"
    if "html" in lowered or "text" in lowered:
        return "html"
    return "unknown"


def _merge_notes(existing: str | None, new: str) -> str:
    if not existing:
        return new
    return "; ".join([existing, new])

