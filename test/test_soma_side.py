"""
Unit tests for SomaSide enum from domain_models.py
"""

import pytest
from quickpage.models.domain_models import SomaSide


@pytest.mark.unit
class TestSomaSide:
    """Test cases for SomaSide enum."""

    def test_enum_values(self):
        """Test that all enum values are correctly defined."""
        assert SomaSide.LEFT.value == "left"
        assert SomaSide.RIGHT.value == "right"
        assert SomaSide.MIDDLE.value == "middle"
        assert SomaSide.COMBINED.value == "combined"
        assert SomaSide.ALL.value == "all"

    def test_from_string_exact_matches(self):
        """Test from_string with exact enum value matches."""
        assert SomaSide.from_string("left") == SomaSide.LEFT
        assert SomaSide.from_string("right") == SomaSide.RIGHT
        assert SomaSide.from_string("middle") == SomaSide.MIDDLE
        assert SomaSide.from_string("combined") == SomaSide.COMBINED
        assert SomaSide.from_string("all") == SomaSide.ALL

    def test_from_string_case_insensitive(self):
        """Test from_string is case insensitive."""
        assert SomaSide.from_string("LEFT") == SomaSide.LEFT
        assert SomaSide.from_string("Right") == SomaSide.RIGHT
        assert SomaSide.from_string("MIDDLE") == SomaSide.MIDDLE
        assert SomaSide.from_string("Combined") == SomaSide.COMBINED
        assert SomaSide.from_string("ALL") == SomaSide.ALL

    def test_from_string_with_whitespace(self):
        """Test from_string handles whitespace correctly."""
        assert SomaSide.from_string("  left  ") == SomaSide.LEFT
        assert SomaSide.from_string("\tright\t") == SomaSide.RIGHT
        assert SomaSide.from_string(" middle ") == SomaSide.MIDDLE

    def test_from_string_aliases_left(self):
        """Test from_string with left aliases."""
        assert SomaSide.from_string("l") == SomaSide.LEFT
        assert SomaSide.from_string("L") == SomaSide.LEFT
        assert SomaSide.from_string("left") == SomaSide.LEFT
        assert SomaSide.from_string("LEFT") == SomaSide.LEFT

    def test_from_string_aliases_right(self):
        """Test from_string with right aliases."""
        assert SomaSide.from_string("r") == SomaSide.RIGHT
        assert SomaSide.from_string("R") == SomaSide.RIGHT
        assert SomaSide.from_string("right") == SomaSide.RIGHT
        assert SomaSide.from_string("RIGHT") == SomaSide.RIGHT

    def test_from_string_aliases_middle(self):
        """Test from_string with middle aliases."""
        assert SomaSide.from_string("m") == SomaSide.MIDDLE
        assert SomaSide.from_string("M") == SomaSide.MIDDLE
        assert SomaSide.from_string("middle") == SomaSide.MIDDLE
        assert SomaSide.from_string("center") == SomaSide.MIDDLE
        assert SomaSide.from_string("CENTER") == SomaSide.MIDDLE

    def test_from_string_aliases_combined(self):
        """Test from_string with combined aliases."""
        assert SomaSide.from_string("bilateral") == SomaSide.COMBINED
        assert SomaSide.from_string("BILATERAL") == SomaSide.COMBINED
        assert SomaSide.from_string("combined") == SomaSide.COMBINED

    def test_from_string_aliases_all(self):
        """Test from_string with all aliases."""
        assert SomaSide.from_string("all") == SomaSide.ALL
        assert SomaSide.from_string("*") == SomaSide.ALL
        assert SomaSide.from_string("ALL") == SomaSide.ALL

    def test_from_string_with_existing_enum(self):
        """Test from_string when passed an existing SomaSide enum."""
        assert SomaSide.from_string(SomaSide.LEFT) == SomaSide.LEFT
        assert SomaSide.from_string(SomaSide.RIGHT) == SomaSide.RIGHT
        assert SomaSide.from_string(SomaSide.MIDDLE) == SomaSide.MIDDLE
        assert SomaSide.from_string(SomaSide.COMBINED) == SomaSide.COMBINED
        assert SomaSide.from_string(SomaSide.ALL) == SomaSide.ALL

    def test_from_string_invalid_values(self):
        """Test from_string raises ValueError for invalid values."""
        with pytest.raises(ValueError, match="Invalid soma side: invalid"):
            SomaSide.from_string("invalid")

        with pytest.raises(ValueError, match="Invalid soma side: xyz"):
            SomaSide.from_string("xyz")

        with pytest.raises(ValueError, match="Invalid soma side: 123"):
            SomaSide.from_string("123")

    def test_from_string_empty_string(self):
        """Test from_string with empty or whitespace-only strings."""
        with pytest.raises(ValueError, match="Invalid soma side: "):
            SomaSide.from_string("")

        with pytest.raises(ValueError, match="Invalid soma side: "):
            SomaSide.from_string("   ")

        with pytest.raises(ValueError, match="Invalid soma side: "):
            SomaSide.from_string("\t")

    def test_string_representation(self):
        """Test string representation of enum values."""
        assert str(SomaSide.LEFT) == "SomaSide.LEFT"
        assert str(SomaSide.RIGHT) == "SomaSide.RIGHT"
        assert str(SomaSide.MIDDLE) == "SomaSide.MIDDLE"
        assert str(SomaSide.COMBINED) == "SomaSide.COMBINED"
        assert str(SomaSide.ALL) == "SomaSide.ALL"

    def test_enum_membership(self):
        """Test enum membership and iteration."""
        all_sides = list(SomaSide)
        assert len(all_sides) == 5
        assert SomaSide.LEFT in all_sides
        assert SomaSide.RIGHT in all_sides
        assert SomaSide.MIDDLE in all_sides
        assert SomaSide.COMBINED in all_sides
        assert SomaSide.ALL in all_sides

    def test_enum_equality(self):
        """Test enum equality comparisons."""
        assert SomaSide.LEFT == SomaSide.LEFT
        assert SomaSide.LEFT != SomaSide.RIGHT
        assert SomaSide.from_string("left") == SomaSide.LEFT
        assert SomaSide.from_string("right") != SomaSide.LEFT

    def test_enum_is_hashable(self):
        """Test that enum values can be used as dictionary keys."""
        side_dict = {
            SomaSide.LEFT: "left_value",
            SomaSide.RIGHT: "right_value",
            SomaSide.MIDDLE: "middle_value",
        }

        assert side_dict[SomaSide.LEFT] == "left_value"
        assert side_dict[SomaSide.RIGHT] == "right_value"
        assert side_dict[SomaSide.MIDDLE] == "middle_value"

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("left", SomaSide.LEFT),
            ("RIGHT", SomaSide.RIGHT),
            ("m", SomaSide.MIDDLE),
            ("bilateral", SomaSide.COMBINED),
            ("*", SomaSide.ALL),
            ("  center  ", SomaSide.MIDDLE),
            ("L", SomaSide.LEFT),
            ("r", SomaSide.RIGHT),
        ],
    )
    def test_from_string_parametrized(self, input_str, expected):
        """Parametrized test for various valid from_string inputs."""
        assert SomaSide.from_string(input_str) == expected

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "invalid",
            "leftright",
            "123",
            "",
            "   ",
            "\t\n",
            "none",
            "null",
        ],
    )
    def test_from_string_invalid_parametrized(self, invalid_input):
        """Parametrized test for various invalid from_string inputs."""
        with pytest.raises(ValueError):
            SomaSide.from_string(invalid_input)
