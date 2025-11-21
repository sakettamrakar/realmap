from __future__ import annotations

"""Utilities for detecting and capturing preview artifacts from detail pages."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Tuple
from urllib.parse import urljoin

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


@dataclass
class PreviewTarget:
    field_key: str
    label: str
    target_type: Literal["url", "click"]
    value: str
    locator_type: Literal["css", "text"] | None = None


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
    """Capture preview artifacts with a two-phase approach for speed and reliability."""

    captured: Dict[str, PreviewArtifact] = {}
    LOGGER.info("Collecting preview targets in a single pass...")
    targets, missing_notes = _collect_preview_targets(page, preview_placeholders)

    for field_key, note in missing_notes:
        placeholder = preview_placeholders[field_key]
        artifact = PreviewArtifact(**placeholder.model_dump())
        artifact.notes = _merge_notes(artifact.notes, note)
        captured[field_key] = artifact

    LOGGER.info("Collected %d preview targets; beginning processing...", len(targets))
    for idx, target in enumerate(targets):
        placeholder = preview_placeholders[target.field_key]
        target_dir = make_preview_dir(str(output_base), project_key, placeholder.field_key)
        target_dir.mkdir(parents=True, exist_ok=True)
        artifact = PreviewArtifact(**placeholder.model_dump())

        LOGGER.info(
            "Processing preview %d/%d: %s",
            idx + 1,
            len(targets),
            target.label or placeholder.field_key,
        )

        try:
            artifact = _process_preview(
                page=page,
                context=context,
                target=target,
                artifact=artifact,
                target_dir=target_dir,
                output_base=output_base,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Preview %d/%d failed: %s", idx + 1, len(targets), exc)
            artifact.notes = _merge_notes(artifact.notes, str(exc))

        captured[artifact.field_key] = artifact

    LOGGER.info("Completed preview capture for %d artifacts", len(captured))
    return captured


def _collect_preview_targets(
    page: Page, preview_placeholders: Dict[str, PreviewArtifact]
) -> Tuple[List[PreviewTarget], List[Tuple[str, str]]]:
    """Collect preview targets quickly without processing them."""

    targets: List[PreviewTarget] = []
    missing: List[Tuple[str, str]] = []

    for placeholder in preview_placeholders.values():
        label = placeholder.notes or placeholder.field_key

        if placeholder.notes and placeholder.notes.lower().startswith("http"):
            targets.append(
                PreviewTarget(
                    field_key=placeholder.field_key,
                    label=label,
                    target_type="url",
                    value=urljoin(page.url, placeholder.notes),
                )
            )
            continue

        hint, locator_type = _locator_hint_from_notes(placeholder.notes)
        locator = _resolve_locator(page, hint, locator_type)
        if locator is None:
            missing.append((placeholder.field_key, "Preview element not found"))
            continue

        href: str | None = None
        try:
            href = locator.first.get_attribute("href", timeout=1_000)
        except Exception:
            href = None

        if href and _is_navigable_href(href):
            targets.append(
                PreviewTarget(
                    field_key=placeholder.field_key,
                    label=label,
                    target_type="url",
                    value=urljoin(page.url, href),
                )
            )
            continue

        targets.append(
            PreviewTarget(
                field_key=placeholder.field_key,
                label=label,
                target_type="click",
                value=hint or "Preview",
                locator_type=locator_type,
            )
        )

    return targets, missing


def _process_preview(
    *,
    page: Page,
    context: BrowserContext,
    target: PreviewTarget,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    timeout_ms: int = 20_000,
) -> PreviewArtifact:
    if target.target_type == "url":
        return _process_url_preview(
            context=context,
            target=target,
            artifact=artifact,
            target_dir=target_dir,
            output_base=output_base,
            timeout_ms=timeout_ms,
        )

    return _process_click_preview(
        page=page,
        context=context,
        target=target,
        artifact=artifact,
        target_dir=target_dir,
        output_base=output_base,
        timeout_ms=timeout_ms,
    )


def _process_url_preview(
    *,
    context: BrowserContext,
    target: PreviewTarget,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    timeout_ms: int,
) -> PreviewArtifact:
    new_page = context.new_page()
    try:
        new_page.goto(target.value, wait_until="load", timeout=timeout_ms)
        artifact = _save_page_artifact(
            new_page,
            context,
            artifact,
            target_dir,
            output_base,
            prefix="preview",
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        artifact.notes = _merge_notes(artifact.notes, f"URL preview failed: {exc}")
    finally:
        try:
            new_page.close()
        except Exception:
            LOGGER.debug("Failed to close preview tab")
    return artifact


def _process_click_preview(
    *,
    page: Page,
    context: BrowserContext,
    target: PreviewTarget,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    timeout_ms: int,
) -> PreviewArtifact:
    locator = _resolve_locator(page, target.value, target.locator_type or "text")
    if locator is None:
        artifact.notes = _merge_notes(artifact.notes, "Preview element not found")
        return artifact

    try:
        with page.expect_popup(timeout=timeout_ms) as popup_info:
            locator.click()
        new_page = popup_info.value
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
        LOGGER.info("Falling back to inline modal capture for %s", artifact.field_key)
        artifact = _capture_inline_modal(
            locator,
            page,
            artifact,
            target_dir,
            output_base,
            click_needed=False,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        artifact.notes = _merge_notes(artifact.notes, f"Preview click failed: {exc}")

    return artifact


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


def _locator_hint_from_notes(notes: str | None) -> Tuple[str | None, Literal["css", "text"]]:
    if notes and notes.startswith(("#", ".")):
        return notes, "css"
    if notes:
        return notes, "text"
    return "Preview", "text"


def _is_navigable_href(href: str | None) -> bool:
    if not href:
        return False

    lowered = href.strip().lower()
    if lowered.startswith(("javascript:", "mailto:", "tel:", "#")):
        return False

    return True


def _resolve_locator(
    page: Page, hint: str | None, locator_type: Literal["css", "text"] = "text"
) -> Locator | None:
    if not hint:
        return None

    try:
        if locator_type == "css":
            return page.locator(hint)
        return page.get_by_text(hint)
    except Exception:
        LOGGER.debug("Failed to resolve locator for hint %s", hint)
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

