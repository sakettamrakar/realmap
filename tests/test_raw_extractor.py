from pathlib import Path

from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.parsing.schema import FieldValueType

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "project_detail_sample.html"


def _get_field(result, label):
    for section in result.sections:
        for field in section.fields:
            if field.label == label:
                return field
    return None


def test_extract_raw_sections_and_fields():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    result = extract_raw_from_html(html, source_file="sample.html")

    assert result.sections, "Expected at least one section"

    labels = [field.label for section in result.sections for field in section.fields]
    assert "Project Name" in labels
    assert "Registration Date" in labels

    project_name = _get_field(result, "Project Name")
    assert project_name is not None
    assert project_name.value == "Sunshine Residency"
    assert project_name.value_type == FieldValueType.TEXT

    registration_date = _get_field(result, "Registration Date")
    assert registration_date is not None
    assert registration_date.value_type == FieldValueType.DATE

    total_units = _get_field(result, "Total Units")
    assert total_units is not None
    assert total_units.value_type == FieldValueType.NUMBER


def test_extract_raw_links_are_captured():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    result = extract_raw_from_html(html, source_file="sample.html")

    brochure = _get_field(result, "Project Brochure")
    assert brochure is not None
    assert brochure.links == ["https://example.com/brochure.pdf"]
    assert brochure.value_type == FieldValueType.URL

    certificate = _get_field(result, "Completion Certificate")
    assert certificate is not None
    assert certificate.links == ["https://example.com/cc.pdf"]


def test_extract_raw_handles_form_controls_and_selects():
    html = """
    <html>
      <body>
        <h3>Project Details [ Registration No : CG-REG-001 ] [ Project Web Address : example.com ]</h3>
        <div class="control-group">
          <label class="control-label">Project Status</label>
          <input type="text" value="Ongoing" disabled />
        </div>
        <div class="control-group">
          <label>Project Address</label>
          <div class="controls">
            <textarea>Plot 12, Near City Center</textarea>
          </div>
        </div>
        <div class="control-group">
          <label>District</label>
          <div class="controls">
            <select>
              <option value="0">Select District</option>
              <option value="14" selected="selected">Raipur</option>
            </select>
          </div>
        </div>
        <div class="control-group">
          <label>Tehsil</label>
          <div class="controls">
            <select>
              <option value="0" selected="selected">Select Tehsil</option>
              <option value="99">Tilda</option>
            </select>
          </div>
        </div>
        <div class="control-group">
          <label>Launch Date</label>
          <input type="text" value="2024-01-15" />
        </div>
      </body>
    </html>
    """

    result = extract_raw_from_html(html, source_file="form.html")

    status = _get_field(result, "Project Status")
    assert status is not None
    assert status.value == "Ongoing"
    assert status.value_type == FieldValueType.TEXT

    address = _get_field(result, "Project Address")
    assert address is not None
    assert address.value == "Plot 12, Near City Center"

    district = _get_field(result, "District")
    assert district is not None
    assert district.value == "Raipur"

    tehsil = _get_field(result, "Tehsil")
    assert tehsil is not None
    assert tehsil.value is None

    launch = _get_field(result, "Launch Date")
    assert launch is not None
    assert launch.value == "2024-01-15"
    assert launch.value_type == FieldValueType.DATE
