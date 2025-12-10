"""
Tests for mapper date parsing and pincode extraction.

Created: 2024-12-10 (Data Audit implementation)
"""
import pytest

from cg_rera_extractor.parsing.mapper import (
    _normalize_date,
    _extract_pincode,
    _infer_doc_type,
)


class TestDateParsing:
    """Tests for date normalization function."""
    
    def test_date_dd_mm_yyyy_slash(self):
        """Test DD/MM/YYYY format."""
        result = _normalize_date("25/12/2024")
        assert result == "2024-12-25"
    
    def test_date_dd_mm_yyyy_dash(self):
        """Test DD-MM-YYYY format."""
        result = _normalize_date("25-12-2024")
        assert result == "2024-12-25"
    
    def test_date_yyyy_mm_dd(self):
        """Test YYYY-MM-DD format (ISO already)."""
        result = _normalize_date("2024-12-25")
        assert result == "2024-12-25"
    
    def test_date_dd_mm_yyyy_dot(self):
        """Test DD.MM.YYYY format."""
        result = _normalize_date("25.12.2024")
        assert result == "2024-12-25"
    
    def test_date_with_whitespace(self):
        """Test date with leading/trailing whitespace."""
        result = _normalize_date("  25/12/2024  ")
        assert result == "2024-12-25"
    
    def test_date_none_input(self):
        """Test None input returns None."""
        assert _normalize_date(None) is None
    
    def test_date_empty_string(self):
        """Test empty string returns None."""
        assert _normalize_date("") is None
        assert _normalize_date("   ") is None
    
    def test_date_invalid_format(self):
        """Test invalid date format returns None."""
        result = _normalize_date("invalid date")
        assert result is None
    
    def test_date_dd_mmm_yyyy(self):
        """Test DD Mon YYYY format."""
        result = _normalize_date("25 Dec 2024")
        assert result == "2024-12-25"
    
    def test_date_dd_mmmm_yyyy(self):
        """Test DD Month YYYY format."""
        result = _normalize_date("25 December 2024")
        assert result == "2024-12-25"


class TestPincodeExtraction:
    """Tests for pincode extraction from address."""
    
    def test_pincode_at_end(self):
        """Test pincode at end of address."""
        result = _extract_pincode("123 Main Street, Raipur 492001")
        assert result == "492001"
    
    def test_pincode_with_prefix(self):
        """Test pincode with PIN prefix."""
        result = _extract_pincode("123 Main Street, Raipur, PIN: 492001")
        assert result == "492001"
    
    def test_pincode_middle_of_address(self):
        """Test pincode in middle of address."""
        result = _extract_pincode("Office 101, Block A, 492001 Raipur, CG")
        assert result == "492001"
    
    def test_no_pincode(self):
        """Test address without pincode returns None."""
        result = _extract_pincode("123 Main Street, Raipur")
        assert result is None
    
    def test_pincode_none_input(self):
        """Test None input returns None."""
        assert _extract_pincode(None) is None
    
    def test_pincode_five_digits_ignored(self):
        """Test 5-digit numbers are not extracted as pincode."""
        result = _extract_pincode("Building 12345, Main Road")
        assert result is None
    
    def test_pincode_seven_digits_ignored(self):
        """Test 7-digit numbers are not extracted as pincode."""
        result = _extract_pincode("Phone: 9876543, Address: Main Road")
        assert result is None
    
    def test_multiple_six_digit_first_match(self):
        """Test that first 6-digit number is extracted."""
        result = _extract_pincode("From 492001 to 492002")
        assert result == "492001"


class TestDocTypeInference:
    """Tests for document type inference from field key."""
    
    def test_registration_certificate(self):
        """Test registration document detection."""
        assert _infer_doc_type("registrationcertificate") == "registration_certificate"
    
    def test_building_plan(self):
        """Test building plan detection."""
        assert _infer_doc_type("buildingplan") == "building_plan"
        assert _infer_doc_type("approvedbuildingplan") == "building_plan"
    
    def test_layout_plan(self):
        """Test layout plan detection."""
        assert _infer_doc_type("layoutplan") == "layout_plan"
        assert _infer_doc_type("approvedlayoutplan") == "layout_plan"
    
    def test_fire_noc(self):
        """Test fire NOC detection."""
        assert _infer_doc_type("firenoc") == "fire_noc"
    
    def test_environment_noc(self):
        """Test environment NOC detection."""
        assert _infer_doc_type("environmentnoc") == "environment_noc"
        assert _infer_doc_type("environmentclearance") == "environment_noc"
    
    def test_encumbrance(self):
        """Test encumbrance certificate detection."""
        assert _infer_doc_type("encumbrancecertificate") == "encumbrance_certificate"
    
    def test_commencement(self):
        """Test commencement certificate detection."""
        assert _infer_doc_type("commencementcertificate") == "commencement_certificate"
    
    def test_occupancy(self):
        """Test occupancy certificate detection."""
        assert _infer_doc_type("occupancycertificate") == "occupancy_certificate"
    
    def test_unknown_type(self):
        """Test unknown document type."""
        assert _infer_doc_type("somethingelse") == "unknown"
    
    def test_revenue_document(self):
        """Test revenue document detection."""
        assert _infer_doc_type("revenuedocument") == "revenue_document"
    
    def test_site_photo(self):
        """Test photo detection."""
        assert _infer_doc_type("sitephoto") == "site_photo"
        assert _infer_doc_type("projectphoto") == "site_photo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
