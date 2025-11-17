from pathlib import Path

from cg_rera_extractor.detail.preview_capture import (
    build_preview_placeholders,
    capture_previews,
)


class FakeResponse:
    def __init__(self, body: bytes, headers: dict[str, str]):
        self._body = body
        self.headers = headers

    def body(self):
        return self._body


class FakeRequest:
    def __init__(self, response: "FakeResponse"):
        self._response = response

    def get(self, _url: str, *_args, **_kwargs):
        return self._response


class FakeBrowserContext:
    def __init__(self, response: FakeResponse):
        self.request = FakeRequest(response)


class FakeLocator:
    def click(self):
        return None

    def locator(self, *_args, **_kwargs):  # pragma: no cover - modal closing noop
        return self

    def press(self, *_args, **_kwargs):  # pragma: no cover - modal closing noop
        return None

    def wait_for_selector(self, *_args, **_kwargs):  # pragma: no cover - modal noop
        return None

    def inner_html(self):  # pragma: no cover - modal noop
        return ""

    def screenshot(self, *args, **kwargs):  # pragma: no cover - modal noop
        Path(kwargs.get("path", "")).write_bytes(b"")


class _PopupContext:
    def __init__(self, popup_page):
        self._popup_page = popup_page
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.value = self._popup_page
        return False


class FakePopupPage:
    def __init__(self, url: str, content: str = ""):
        self.url = url
        self._content = content

    def wait_for_load_state(self, *_args, **_kwargs):  # pragma: no cover - noop
        return None

    def content(self):
        return self._content

    def close(self):  # pragma: no cover - noop
        return None


class FakePage:
    def __init__(self, popup_page: FakePopupPage, context: FakeBrowserContext, locator_hint: str):
        self._popup_page = popup_page
        self.context = context
        self._locator_hint = locator_hint

    def expect_popup(self, *_args, **_kwargs):
        return _PopupContext(self._popup_page)

    def locator(self, selector: str):
        assert selector == self._locator_hint
        return FakeLocator()

    def get_by_text(self, _text: str):  # pragma: no cover - not exercised in test
        return FakeLocator()


def test_capture_preview_saves_pdf(tmp_path):
    html = """
    <h2>Project Details</h2>
    <table>
      <tr>
        <td><label>Project Name</label></td>
        <td><button id="preview-btn">Preview</button></td>
      </tr>
    </table>
    """

    placeholders = build_preview_placeholders(
        html,
        source_file="source.html",
        state_code="CG",
        registration_number="CG/123",
        project_name="Sample",
    )

    popup_page = FakePopupPage(url="https://example.com/doc.pdf", content="<html></html>")
    response = FakeResponse(b"%PDF-1.4", {"content-type": "application/pdf"})
    context = FakeBrowserContext(response)
    page = FakePage(popup_page=popup_page, context=context, locator_hint="#preview-btn")

    captured = capture_previews(
        page=page,
        context=context,
        project_key="CG_CG_123",
        output_base=tmp_path,
        preview_placeholders=placeholders,
    )

    assert "project_name" in captured
    artifact = captured["project_name"]
    assert artifact.artifact_type == "pdf"
    assert artifact.files, "Expected file paths to be recorded"
    saved_file = tmp_path / artifact.files[0]
    assert saved_file.exists()

