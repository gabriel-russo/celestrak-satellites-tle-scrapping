import pytest
from tle import satellite_to_tle
from fixtures.parametrize import line_1_test_cases, line_2_test_cases


@pytest.mark.parametrize("satellite, expected_line1", line_1_test_cases)
def test_json_to_tle(satellite, expected_line1):
    result = satellite_to_tle(satellite)
    assert result["line1"] == expected_line1


@pytest.mark.parametrize("satellite, expected_line2", line_2_test_cases)
def test_satellite_to_tle_reproduces_terra_line2(satellite, expected_line2):
    result = satellite_to_tle(satellite)
    assert result["line2"] == expected_line2
