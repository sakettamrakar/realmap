"""
Tests for data normalization utilities.

Created: 2024-12-10 (Data Audit implementation)
"""
import pytest
from decimal import Decimal

from cg_rera_extractor.utils.normalize import (
    normalize_area_to_sqm,
    normalize_area_to_sqft,
    normalize_price,
    price_per_sqft,
    format_price_lakhs,
    normalize_project_status,
    normalize_project_type,
    normalize_whitespace,
    normalize_name,
    extract_numeric,
)


class TestAreaNormalization:
    """Tests for area conversion functions."""
    
    def test_sqft_to_sqm_basic(self):
        """Test basic square feet to square meters conversion."""
        result = normalize_area_to_sqm(1000, "sqft")
        assert result is not None
        # 1000 sqft ≈ 92.903 sqm
        assert abs(result - Decimal("92.903")) < Decimal("0.01")
    
    def test_sqm_to_sqft_basic(self):
        """Test basic square meters to square feet conversion."""
        result = normalize_area_to_sqft(100, "sqm")
        assert result is not None
        # 100 sqm ≈ 1076.39 sqft
        assert abs(result - Decimal("1076.39")) < Decimal("1")
    
    def test_area_with_string_unit(self):
        """Test area parsing with unit in string."""
        result = normalize_area_to_sqm("1000 sq.ft")
        assert result is not None
        assert abs(result - Decimal("92.903")) < Decimal("0.01")
    
    def test_area_with_commas(self):
        """Test area parsing with thousands separator."""
        result = normalize_area_to_sqm("1,000 sqft")
        assert result is not None
        assert abs(result - Decimal("92.903")) < Decimal("0.01")
    
    def test_area_acres(self):
        """Test acre to sqm conversion."""
        result = normalize_area_to_sqm(1, "acre")
        assert result is not None
        # 1 acre ≈ 4046.86 sqm
        assert abs(result - Decimal("4046.86")) < Decimal("1")
    
    def test_area_hectares(self):
        """Test hectare to sqm conversion."""
        result = normalize_area_to_sqm(1, "hectare")
        assert result is not None
        assert result == Decimal("10000")
    
    def test_area_none_input(self):
        """Test None input returns None."""
        assert normalize_area_to_sqm(None) is None
        assert normalize_area_to_sqft(None) is None
    
    def test_area_invalid_input(self):
        """Test invalid input returns None."""
        assert normalize_area_to_sqm("invalid") is None


class TestPriceNormalization:
    """Tests for price conversion functions."""
    
    def test_price_basic_number(self):
        """Test basic numeric price."""
        result = normalize_price(100000)
        assert result == Decimal("100000")
    
    def test_price_with_rupee_symbol(self):
        """Test price with rupee symbol."""
        result = normalize_price("₹1,00,000")
        assert result == Decimal("100000")
    
    def test_price_with_crores(self):
        """Test price in crores."""
        result = normalize_price("1.5 Cr")
        assert result == Decimal("15000000")
    
    def test_price_with_lakhs(self):
        """Test price in lakhs."""
        result = normalize_price("50 Lakh")
        assert result == Decimal("5000000")
    
    def test_price_with_lac(self):
        """Test price with 'lac' variant."""
        result = normalize_price("50 L")
        assert result == Decimal("5000000")
    
    def test_price_with_rs(self):
        """Test price with Rs. prefix."""
        result = normalize_price("Rs. 1,00,000")
        assert result == Decimal("100000")
    
    def test_price_crore_variant(self):
        """Test crore spelling variants."""
        assert normalize_price("1 Crore") == Decimal("10000000")
        assert normalize_price("1cr") == Decimal("10000000")
    
    def test_price_none_input(self):
        """Test None input returns None."""
        assert normalize_price(None) is None
    
    def test_price_already_decimal(self):
        """Test Decimal passthrough."""
        result = normalize_price(Decimal("100000"))
        assert result == Decimal("100000")
    
    def test_price_per_sqft_calculation(self):
        """Test price per sqft calculation."""
        result = price_per_sqft(Decimal("5000000"), Decimal("1000"))
        assert result == Decimal("5000")
    
    def test_price_per_sqft_zero_area(self):
        """Test price per sqft with zero area returns None."""
        assert price_per_sqft(Decimal("5000000"), Decimal("0")) is None
    
    def test_format_price_lakhs(self):
        """Test price formatting in lakhs."""
        result = format_price_lakhs(Decimal("5000000"))
        assert result == "50.00 L"
    
    def test_format_price_crores(self):
        """Test price formatting in crores."""
        result = format_price_lakhs(Decimal("20000000"))
        assert result == "2.00 Cr"


class TestCategoryNormalization:
    """Tests for category normalization functions."""
    
    def test_project_status_ongoing(self):
        """Test ongoing status variants."""
        assert normalize_project_status("ongoing") == "ongoing"
        assert normalize_project_status("UNDER CONSTRUCTION") == "ongoing"
        assert normalize_project_status("In Progress") == "ongoing"
    
    def test_project_status_completed(self):
        """Test completed status variants."""
        assert normalize_project_status("completed") == "completed"
        assert normalize_project_status("Ready to Move") == "completed"
        assert normalize_project_status("possession") == "completed"
    
    def test_project_status_unknown(self):
        """Test unknown status passthrough."""
        assert normalize_project_status("Some Unknown Status") == "Some Unknown Status"
    
    def test_project_status_none(self):
        """Test None input returns None."""
        assert normalize_project_status(None) is None
    
    def test_project_type_residential(self):
        """Test residential type variants."""
        assert normalize_project_type("residential") == "residential"
        assert normalize_project_type("Group Housing") == "residential"
        assert normalize_project_type("apartment") == "residential"
    
    def test_project_type_commercial(self):
        """Test commercial type variants."""
        assert normalize_project_type("commercial") == "commercial"
        assert normalize_project_type("shop") == "commercial"


class TestTextNormalization:
    """Tests for text normalization functions."""
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        result = normalize_whitespace("  Hello    World  ")
        assert result == "Hello World"
    
    def test_normalize_whitespace_with_newlines(self):
        """Test whitespace normalization with newlines."""
        result = normalize_whitespace("Hello\n\n  World")
        assert result == "Hello World"
    
    def test_normalize_name(self):
        """Test name normalization to title case."""
        result = normalize_name("john DOE")
        assert result == "John Doe"
    
    def test_extract_numeric(self):
        """Test numeric extraction."""
        result = extract_numeric("PIN: 492001")
        assert result == "492001"
    
    def test_extract_numeric_mixed(self):
        """Test numeric extraction from mixed content."""
        result = extract_numeric("₹1,00,000/-")
        assert result == "100000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
