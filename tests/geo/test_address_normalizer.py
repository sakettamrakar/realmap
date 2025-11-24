from cg_rera_extractor.geo import AddressParts, normalize_address


def test_normalize_address_orders_and_cleans_components() -> None:
    parts = AddressParts(
        address_line=" Plot 123 , Near Market  ",
        village_or_locality="  Village  Name  ",
        tehsil="Tah. Raipur",
        district="Dist. Durg",
        state_code="CG",
        pincode="492001",
    )

    result = normalize_address(parts)

    assert (
        result.normalized_address
        == "Plot 123 Near Market, Village Name, Tehsil Raipur, District Durg, Chhattisgarh, 492001, India"
    )
    assert not result.is_low_confidence


def test_missing_district_flagged_as_low_confidence() -> None:
    parts = AddressParts(address_line="Bus Stand", state_code="CG")

    result = normalize_address(parts)

    assert result.normalized_address == "Bus Stand, Chhattisgarh, India"
    assert result.is_low_confidence


def test_ignores_empty_components() -> None:
    parts = AddressParts(
        address_line="   ",
        village_or_locality="",
        district="Raipur",
        state="Chhattisgarh",
        pincode=" 492001 ",
    )

    result = normalize_address(parts)

    assert result.normalized_address == "Raipur, Chhattisgarh, 492001, India"
    assert "address_line" in result.missing_components
