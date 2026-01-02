from __future__ import annotations

"""Utilities for detecting and capturing preview artifacts from detail pages."""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Tuple
from urllib.parse import urljoin

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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
    """Collect preview targets quickly without processing them.
    
    Smart optimization: PDFs are detected early and handled via URL extraction only,
    avoiding expensive modal interaction.
    """

    targets: List[PreviewTarget] = []
    missing: List[Tuple[str, str]] = []

    for placeholder in preview_placeholders.values():
        label = placeholder.notes or placeholder.field_key

        # OPTIMIZATION 1: Check if notes field already contains a PDF URL
        # This catches URLs like "../Content/ProjectDocuments/xxx.pdf"
        if placeholder.notes and _is_pdf_url(placeholder.notes):
            pdf_url = urljoin(page.url, placeholder.notes)
            LOGGER.info(f"Fast-path: PDF URL detected in notes for {placeholder.field_key}, skipping modal")
            targets.append(
                PreviewTarget(
                    field_key=placeholder.field_key,
                    label=label,
                    target_type="url",
                    value=pdf_url,
                )
            )
            continue

        # OPTIMIZATION 2: Check for direct HTTP URLs
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
        onclick: str | None = None
        try:
            href = locator.first.get_attribute("href", timeout=1_000)
            onclick = locator.first.get_attribute("onclick", timeout=1_000)
        except Exception:
            href = None
            onclick = None

        # OPTIMIZATION 3: Check href attribute for PDF
        if href and _is_pdf_url(href):
            pdf_url = urljoin(page.url, href)
            LOGGER.info(f"Fast-path: PDF detected in href for {placeholder.field_key}, skipping modal")
            targets.append(
                PreviewTarget(
                    field_key=placeholder.field_key,
                    label=label,
                    target_type="url",
                    value=pdf_url,
                )
            )
            continue

        # OPTIMIZATION 4: Check onclick attribute for PDF
        if onclick and _is_pdf_onclick(onclick):
            pdf_url = _extract_url_from_onclick(onclick, page.url)
            if pdf_url:
                LOGGER.info(f"Fast-path: PDF detected in onclick for {placeholder.field_key}, skipping modal")
                targets.append(
                    PreviewTarget(
                        field_key=placeholder.field_key,
                        label=label,
                        target_type="url",
                        value=pdf_url,
                    )
                )
                continue

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

        # For non-PDF content (tables, images), use click-based modal capture
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


def _is_pdf_onclick(onclick: str) -> bool:
    """Check if onclick JavaScript opens a PDF document."""
    if not onclick:
        return False
    onclick_lower = onclick.lower()
    return ".pdf" in onclick_lower and ("openmodel" in onclick_lower or "window.open" in onclick_lower)


def _is_pdf_url(url: str) -> bool:
    """Check if URL points to a PDF file."""
    if not url:
        return False
    url_lower = url.lower().strip()
    return url_lower.endswith(".pdf") or ".pdf?" in url_lower or ".pdf#" in url_lower


def _extract_url_from_onclick(onclick: str, base_url: str) -> str | None:
    """Extract URL from onclick JavaScript like OpenModel('documents/abc.pdf')."""
    import re
    
    # Try to extract URL from OpenModel(...) or window.open(...)
    patterns = [
        r'''OpenModel\s*\(\s*['"]([^'"]+)['"]\s*\)''',
        r'''window\.open\s*\(\s*['"]([^'"]+)['"]\s*\)''',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, onclick, re.IGNORECASE)
        if match:
            relative_url = match.group(1)
            return urljoin(base_url, relative_url)
    
    return None


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
        LOGGER.info(f"Opening URL preview: {target.value}")
        new_page.goto(target.value, wait_until="load", timeout=timeout_ms)
        
        # Capture the actual URL after any redirects
        actual_url = new_page.url
        artifact.source_url = actual_url
        LOGGER.debug(f"URL resolved to: {actual_url}")
        
        artifact = _save_page_artifact(
            new_page,
            context,
            artifact,
            target_dir,
            output_base,
            prefix="preview",
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.error(f"URL preview failed for {target.value}: {exc}")
        artifact.notes = _merge_notes(artifact.notes, f"URL preview failed: {exc}")
        
        # Try HTTP fallback if playwright fails
        artifact = _try_http_fallback(
            target.value,
            artifact,
            target_dir,
            output_base,
            context.pages[0].url if context.pages else None
        )
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
        LOGGER.info(f"Clicking preview button for: {target.label}")
        with page.expect_popup(timeout=timeout_ms) as popup_info:
            locator.click()
        new_page = popup_info.value
        
        # Capture the actual URL that opened
        actual_url = new_page.url
        artifact.source_url = actual_url
        LOGGER.debug(f"Popup opened to: {actual_url}")
        
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
    """Download artifact with robust error handling and verification."""
    LOGGER.info(f"[DOWNLOAD] Starting download: {url}")
    
    try:
        # Try playwright request first
        response = context.request.get(url, timeout=30_000)  # Increased timeout
        content_type = response.headers.get("content-type", "")
        
        LOGGER.debug(f"[DOWNLOAD] Response status: {response.status}, Content-Type: {content_type}")
        
        if response.status != 200:
            raise Exception(f"HTTP {response.status}")
        
        body = response.body()
        
        if not body or len(body) == 0:
            raise Exception("Empty response body")
        
        extension = _extension_from_content_type(content_type)
        
        # Generate unique filename based on field_key
        filename = f"{artifact.field_key}{extension}" if artifact.field_key else f"{prefix}{extension}"
        file_path = target_dir / filename
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        LOGGER.debug(f"[DOWNLOAD] Writing {len(body)} bytes to {file_path}")
        file_path.write_bytes(body)
        
        # Verify file was written
        if not file_path.exists():
            raise Exception("File not created after write")
        
        actual_size = file_path.stat().st_size
        if actual_size == 0:
            raise Exception("File is empty after write")
        
        LOGGER.info(f"[DOWNLOAD_OK] Saved {filename} ({actual_size:,} bytes)")
        
        artifact.artifact_type = _artifact_type_from_content_type(content_type)
        artifact.files.append(str(file_path.relative_to(output_base)))
        artifact.notes = _merge_notes(artifact.notes, f"Downloaded: {actual_size:,} bytes")
        
    except Exception as exc:
        LOGGER.warning(f"[DOWNLOAD_FAIL] Playwright download failed: {exc}")
        
        # Try HTTP fallback
        base_url = context.pages[0].url if context.pages else None
        artifact = _try_http_fallback(url, artifact, target_dir, output_base, base_url)
    
    return artifact


def _try_http_fallback(
    url: str,
    artifact: PreviewArtifact,
    target_dir: Path,
    output_base: Path,
    base_url: str | None = None,
) -> PreviewArtifact:
    """Try direct HTTP download as fallback when browser methods fail."""
    if not HAS_REQUESTS:
        LOGGER.warning("[HTTP_FALLBACK] requests library not available")
        artifact.notes = _merge_notes(artifact.notes, "HTTP fallback unavailable (no requests)")
        return artifact
    
    try:
        # Resolve relative URLs
        if base_url and url.startswith("../"):
            download_url = urljoin(base_url, url)
        else:
            download_url = url
        
        LOGGER.info(f"[HTTP_FALLBACK] Trying direct download: {download_url}")
        
        response = requests.get(download_url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        content = response.content
        if not content or len(content) == 0:
            raise Exception("Empty response")
        
        content_type = response.headers.get("content-type", "")
        extension = _extension_from_content_type(content_type)
        
        # Generate filename
        filename = f"{artifact.field_key}{extension}" if artifact.field_key else f"fallback{extension}"
        file_path = target_dir / filename
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        
        # Verify
        if not file_path.exists() or file_path.stat().st_size == 0:
            raise Exception("File verification failed")
        
        actual_size = file_path.stat().st_size
        LOGGER.info(f"[HTTP_FALLBACK_OK] Saved {filename} ({actual_size:,} bytes)")
        
        artifact.artifact_type = _artifact_type_from_content_type(content_type)
        artifact.files.append(str(file_path.relative_to(output_base)))
        artifact.notes = _merge_notes(artifact.notes, f"HTTP fallback: {actual_size:,} bytes")
        
    except Exception as exc:
        LOGGER.error(f"[HTTP_FALLBACK_FAIL] {exc}")
        artifact.notes = _merge_notes(artifact.notes, f"HTTP fallback failed: {exc}")
    
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
            time.sleep(1)  # Wait for modal animation
        except Exception as exc:  # pragma: no cover - defensive logging
            artifact.notes = _merge_notes(artifact.notes, f"Preview click failed: {exc}")
            return artifact

    modal = _wait_for_modal(page)
    if modal is None:
        artifact.notes = _merge_notes(artifact.notes, "No preview modal detected")
        return artifact

    LOGGER.info("Collecting preview content for %s (inline modal)", artifact.field_key)
    
    try:
        inner = modal.inner_html()
        
        # Save raw HTML
        html_path = target_dir / "modal.html"
        html_path.write_text(inner, encoding="utf-8")
        artifact.files.append(str(html_path.relative_to(output_base)))
        
        # Detect content type and handle accordingly
        content_type = _detect_modal_content_type(inner)
        LOGGER.info(f"Modal content type detected: {content_type}")
        
        if content_type == "table":
            # Extract structured table data
            artifact.artifact_type = "html_table"
            try:
                table_data = _extract_table_data(modal)
                if table_data:
                    json_path = target_dir / "table_data.json"
                    json_path.write_text(
                        json.dumps(table_data, ensure_ascii=False, indent=2),
                        encoding="utf-8"
                    )
                    artifact.files.append(str(json_path.relative_to(output_base)))
                    artifact.notes = _merge_notes(
                        artifact.notes, 
                        f"Extracted {len(table_data.get('rows', []))} table rows"
                    )
                    LOGGER.info(f"Extracted {len(table_data.get('rows', []))} rows from table")
            except Exception as exc:
                LOGGER.warning(f"Table extraction failed: {exc}")
                artifact.notes = _merge_notes(artifact.notes, f"Table extraction failed: {exc}")
        
        elif content_type == "image":
            # Handle image in modal
            artifact.artifact_type = "image"
            try:
                img_locator = modal.locator("img").first
                if img_locator:
                    img_src = img_locator.get_attribute("src")
                    if img_src:
                        artifact.notes = _merge_notes(artifact.notes, f"Image URL: {img_src}")
            except Exception:
                pass
        
        elif content_type == "iframe":
            # PDF or other embedded content in iframe
            artifact.artifact_type = "iframe"
            try:
                iframe_locator = modal.locator("iframe").first
                if iframe_locator:
                    iframe_src = iframe_locator.get_attribute("src")
                    if iframe_src:
                        artifact.notes = _merge_notes(artifact.notes, f"Iframe URL: {iframe_src}")
            except Exception:
                pass
        
        else:
            # Generic HTML content
            artifact.artifact_type = "html"
        
        # Take screenshot for visual reference (optional)
        try:
            screenshot_path = target_dir / "modal_screenshot.png"
            modal.screenshot(path=str(screenshot_path))
            artifact.files.append(str(screenshot_path.relative_to(output_base)))
        except Exception:
            LOGGER.debug("Modal screenshot skipped")
            
    except Exception as exc:  # pragma: no cover - defensive logging
        artifact.notes = _merge_notes(artifact.notes, f"Modal capture failed: {exc}")

    _close_modal_if_possible(modal)
    return artifact


def _detect_modal_content_type(html: str) -> str:
    """Detect the type of content in the modal."""
    html_lower = html.lower()
    
    if "<table" in html_lower:
        return "table"
    elif "<iframe" in html_lower:
        return "iframe"
    elif "<img" in html_lower:
        return "image"
    else:
        return "html"


def _extract_table_data(modal: Locator) -> Dict | None:
    """Extract structured data from HTML table in modal."""
    try:
        # Find table element
        table = modal.locator("table").first
        if not table:
            return None
        
        # Extract headers
        headers = []
        header_cells = table.locator("thead tr th, thead tr td, tr:first-child th, tr:first-child td").all()
        for cell in header_cells:
            headers.append(cell.inner_text().strip())
        
        # If no headers found, use generic column names
        if not headers:
            # Count columns from first row
            first_row = table.locator("tr").first
            if first_row:
                cells = first_row.locator("td, th").all()
                headers = [f"Column_{i+1}" for i in range(len(cells))]
        
        # Extract rows
        rows = []
        row_locators = table.locator("tbody tr, tr").all()
        
        # Skip first row if it was used for headers
        start_idx = 1 if not table.locator("thead").count() and headers else 0
        
        for row_locator in row_locators[start_idx:]:
            cells = row_locator.locator("td, th").all()
            if not cells:
                continue
                
            row_data = {}
            for idx, cell in enumerate(cells):
                header = headers[idx] if idx < len(headers) else f"Column_{idx+1}"
                row_data[header] = cell.inner_text().strip()
            
            if any(row_data.values()):  # Skip empty rows
                rows.append(row_data)
        
        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers)
        }
        
    except Exception as exc:
        LOGGER.warning(f"Table extraction error: {exc}")
        return None


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

