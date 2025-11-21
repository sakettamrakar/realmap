from pathlib import Path

from cg_rera_extractor.qa.field_extractor import extract_label_value_map


def test_extract_label_value_map_handles_tables_and_preview():
    html = Path("tests/qa/fixtures/detail_page.html").read_text(encoding="utf-8")

    result = extract_label_value_map(html)

    assert result["registration_number"] == "CG-REG-001"
    assert result["project_name"] == "Garden Villas"
    assert result["district"] == "Raipur"
    assert result["tehsil"] == "Tilda"
    assert result["project_status"] == "Preview"
    assert result["project_type"] == "Residential"
    assert result["project_address"] == "Near City Center"
    assert result["launch_date"] == "2023-01-15"


def test_extract_label_value_map_handles_control_group_layout():
    html = """
    <html>
      <body>
        <div class="control-group">
          <label class="control-label">District</label>
          <div class="controls">
            <select>
              <option value="0">Select District</option>
              <option value="14" selected="selected">Raipur</option>
            </select>
          </div>
        </div>
        <div class="control-group">
          <label>Project Status</label>
          <input type="text" value="In Progress" />
        </div>
        <div class="control-group">
          <label>Is Project Developed Under EWS Category?</label>
          <div class="controls">
            <select>
              <option value="1">YES</option>
              <option value="0" selected="selected">NO</option>
            </select>
          </div>
        </div>
      </body>
    </html>
    """

    result = extract_label_value_map(html)

    assert result["district"] == "Raipur"
    assert result["project_status"] == "In Progress"
    assert result["is_project_developed_under_ews_category"] == "NO"
