"""
Test suite for NeuronSelectionService combined link generation logic.
"""

import pytest
from unittest.mock import Mock, MagicMock
from quickpage.services.neuron_selection_service import NeuronSelectionService
from quickpage.services.file_service import FileService


@pytest.fixture
def selection_service():
    """Create NeuronSelectionService instance."""
    mock_config = Mock()
    return NeuronSelectionService(mock_config)


@pytest.fixture
def mock_connector():
    """Create mock connector for testing."""
    connector = Mock()
    connector.dataset_adapter = Mock()
    connector.dataset_adapter.dataset_info = Mock()
    connector.dataset_adapter.dataset_info.name = "hemibrain"
    connector.client = Mock()
    return connector


class TestNeuronSelectionService:
    """Test cases for NeuronSelectionService combined link logic."""

    def test_get_available_soma_sides_single_side_no_combined_link(
        self, selection_service, mock_connector
    ):
        """Test that single-side neuron types don't get combined navigation links."""
        # Mock query result with only one soma side
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L"
        ]  # Only left side

        # Mock count query result (single left side, no unknowns)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 5, "rightCount": 0, "middleCount": 0, "totalCount": 5}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides("CB0674", mock_connector)

        # Should only have left link, no combined link
        expected_left_filename = FileService.generate_filename("CB0674", "left")
        expected = {"left": expected_left_filename}

        assert result == expected
        assert "combined" not in result
        assert len(result) == 1

    def test_get_available_soma_sides_multiple_sides_gets_combined_link(
        self, selection_service, mock_connector
    ):
        """Test that multi-side neuron types get combined navigation links."""
        # Mock query result with multiple soma sides
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L",
            "R",
        ]  # Left and right sides

        # Mock count query result (left and right sides)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 8, "rightCount": 12, "middleCount": 0, "totalCount": 20}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides("TM3", mock_connector)

        # Should have left, right, and combined links
        expected_left_filename = FileService.generate_filename("TM3", "left")
        expected_right_filename = FileService.generate_filename("TM3", "right")
        expected_combined_filename = FileService.generate_filename("TM3", "combined")

        expected = {
            "left": expected_left_filename,
            "right": expected_right_filename,
            "combined": expected_combined_filename,
        }

        assert result == expected
        assert "combined" in result
        assert len(result) == 3

    def test_get_available_soma_sides_right_only_no_combined_link(
        self, selection_service, mock_connector
    ):
        """Test that right-only neuron types don't get combined navigation links."""
        # Mock query result with only right soma side
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "R"
        ]  # Only right side

        # Mock count query result (single right side, no unknowns)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 0, "rightCount": 12, "middleCount": 0, "totalCount": 12}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides("RightOnly", mock_connector)

        # Should only have right link, no combined link
        expected_right_filename = FileService.generate_filename("RightOnly", "right")
        expected = {"right": expected_right_filename}

        assert result == expected
        assert "combined" not in result
        assert len(result) == 1

    def test_get_available_soma_sides_middle_only_no_combined_link(
        self, selection_service, mock_connector
    ):
        """Test that middle-only neuron types don't get combined navigation links."""
        # Mock query result with only middle soma side
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "M"
        ]  # Only middle side

        # Mock count query result (single middle side, no unknowns)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 0, "rightCount": 0, "middleCount": 8, "totalCount": 8}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides(
            "MiddleOnly", mock_connector
        )

        # Should only have middle link, no combined link
        expected_middle_filename = FileService.generate_filename("MiddleOnly", "middle")
        expected = {"middle": expected_middle_filename}

        assert result == expected
        assert "combined" not in result
        assert len(result) == 1

    def test_get_available_soma_sides_with_c_mapping_to_middle(
        self, selection_service, mock_connector
    ):
        """Test that 'C' soma side maps to middle, not combined."""
        # Mock query result with 'C' soma side (which maps to middle)
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L",
            "C",
        ]  # Left and center (maps to middle)

        # Mock count query result - two sides with data should get combined link
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 3, "rightCount": 0, "middleCount": 4, "totalCount": 7}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides(
            "WithCenter", mock_connector
        )

        # Should have left, middle (from C mapping), and combined (because multiple sides)
        expected_left_filename = FileService.generate_filename("WithCenter", "left")
        expected_middle_filename = FileService.generate_filename("WithCenter", "middle")
        expected_combined_filename = FileService.generate_filename(
            "WithCenter", "combined"
        )

        expected = {
            "left": expected_left_filename,
            "middle": expected_middle_filename,
            "combined": expected_combined_filename,
        }

        assert result == expected
        assert len(result) == 3
        # C maps to middle, and combined is added because there are multiple sides

    def test_get_available_soma_sides_three_sides_gets_combined_link(
        self, selection_service, mock_connector
    ):
        """Test that three-side neuron types get combined navigation links."""
        # Mock query result with all three soma sides
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L",
            "R",
            "M",
        ]  # All sides

        # Mock count query result (all three sides)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 4, "rightCount": 3, "middleCount": 2, "totalCount": 9}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides("AllSides", mock_connector)

        # Should have left, right, middle, and combined links
        expected_left_filename = FileService.generate_filename("AllSides", "left")
        expected_right_filename = FileService.generate_filename("AllSides", "right")
        expected_middle_filename = FileService.generate_filename("AllSides", "middle")
        expected_combined_filename = FileService.generate_filename(
            "AllSides", "combined"
        )

        expected = {
            "left": expected_left_filename,
            "right": expected_right_filename,
            "middle": expected_middle_filename,
            "combined": expected_combined_filename,
        }

        assert result == expected
        assert "combined" in result
        assert len(result) == 4

    def test_get_available_soma_sides_empty_result(
        self, selection_service, mock_connector
    ):
        """Test handling of empty query results."""
        # Mock empty query result
        mock_result = MagicMock()
        mock_result.empty = True

        mock_connector.client.fetch_custom.return_value = mock_result

        result = selection_service.get_available_soma_sides("NoData", mock_connector)

        # Should return empty dict
        assert result == {}

    def test_get_available_soma_sides_none_result(
        self, selection_service, mock_connector
    ):
        """Test handling of None query results."""
        # Mock None query result
        mock_connector.client.fetch_custom.return_value = None

        result = selection_service.get_available_soma_sides("NoData", mock_connector)

        # Should return empty dict
        assert result == {}

    def test_get_available_soma_sides_fafb_dataset_single_side(
        self, selection_service, mock_connector
    ):
        """Test FAFB dataset with single soma side doesn't get combined link."""
        # Configure mock for FAFB dataset
        mock_connector.dataset_adapter.dataset_info.name = "flywire-fafb"

        # Mock query result with only one soma side for FAFB
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L"
        ]  # Only left side

        # Mock count query result (single left side for FAFB)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 5, "rightCount": 0, "middleCount": 0, "totalCount": 5}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides(
            "FAFB_Single", mock_connector
        )

        # Should only have left link, no combined link (same behavior as other datasets)
        expected_left_filename = FileService.generate_filename("FAFB_Single", "left")
        expected = {"left": expected_left_filename}

        assert result == expected
        assert "combined" not in result
        assert len(result) == 1

    def test_get_available_soma_sides_fafb_dataset_multiple_sides(
        self, selection_service, mock_connector
    ):
        """Test FAFB dataset with multiple soma sides gets combined link."""
        # Configure mock for FAFB dataset
        mock_connector.dataset_adapter.dataset_info.name = "flywire-fafb"

        # Mock query result with multiple soma sides for FAFB
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L",
            "R",
        ]  # Left and right sides

        # Mock count query result (left and right sides for FAFB)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 6, "rightCount": 8, "middleCount": 0, "totalCount": 14}
        ]

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides(
            "FAFB_Multi", mock_connector
        )

        # Should have left, right, and combined links
        expected_left_filename = FileService.generate_filename("FAFB_Multi", "left")
        expected_right_filename = FileService.generate_filename("FAFB_Multi", "right")
        expected_combined_filename = FileService.generate_filename(
            "FAFB_Multi", "combined"
        )

        expected = {
            "left": expected_left_filename,
            "right": expected_right_filename,
            "combined": expected_combined_filename,
        }

        assert result == expected
        assert "combined" in result
        assert len(result) == 3

    def test_get_available_soma_sides_single_side_with_unknown_gets_combined(
        self, selection_service, mock_connector
    ):
        """Test that single side with unknown neurons gets combined navigation links."""
        # Mock query result with single side available
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.__getitem__.return_value.tolist.return_value = [
            "L"
        ]  # Only left side visible

        # Mock count query result (single left side with unknown neurons)
        mock_count_result = MagicMock()
        mock_count_result.empty = False
        mock_count_result.iloc = [
            {"leftCount": 3, "rightCount": 0, "middleCount": 0, "totalCount": 8}
        ]  # 5 unknown

        # Set up mock to return different results for different queries
        def mock_fetch(query):
            if "COUNT(" in query:
                return mock_count_result
            else:
                return mock_result

        mock_connector.client.fetch_custom.side_effect = mock_fetch

        result = selection_service.get_available_soma_sides(
            "MixedWithUnknown", mock_connector
        )

        # Should have left and combined links (because of unknown neurons)
        expected_left_filename = FileService.generate_filename(
            "MixedWithUnknown", "left"
        )
        expected_combined_filename = FileService.generate_filename(
            "MixedWithUnknown", "combined"
        )

        expected = {
            "left": expected_left_filename,
            "combined": expected_combined_filename,
        }

        assert result == expected
        assert "combined" in result
        assert len(result) == 2
