"""
Test suite for SomaDetectionService combined page generation logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from quickpage.services.soma_detection_service import SomaDetectionService
from quickpage.commands import GeneratePageCommand
from quickpage.models.domain_models import NeuronTypeName, SomaSide
from quickpage.result import Ok, Err


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for SomaDetectionService."""
    connector = Mock()
    page_generator = Mock()
    cache_service = Mock()
    neuron_statistics_service = Mock()

    return {
        "connector": connector,
        "page_generator": page_generator,
        "cache_service": cache_service,
        "neuron_statistics_service": neuron_statistics_service,
    }


@pytest.fixture
def detection_service(mock_dependencies):
    """Create SomaDetectionService instance with mocked dependencies."""
    return SomaDetectionService(
        mock_dependencies["connector"],
        mock_dependencies["page_generator"],
        mock_dependencies["cache_service"],
        mock_dependencies["neuron_statistics_service"],
    )


@pytest.fixture
def sample_command():
    """Create a sample GeneratePageCommand."""
    return GeneratePageCommand(
        neuron_type=NeuronTypeName("CB0674"),
        soma_side=SomaSide.ALL,
        output_directory="output",
        image_format="svg",
        embed_images=False,
        minify=False,
    )


class TestSomaDetectionService:
    """Test cases for SomaDetectionService combined page logic."""

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_single_side_no_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that single-side neuron types don't generate combined pages."""
        # Mock neuron statistics service to return single side data
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok({"left": 5, "right": 0, "middle": 0, "total": 5})
        )

        result = await detection_service.analyze_soma_sides("CB0674")

        # Verify the analysis
        assert result["total_count"] == 5
        assert result["left_count"] == 5
        assert result["right_count"] == 0
        assert result["middle_count"] == 0
        assert result["sides_with_data"] == 1
        assert result["unknown_count"] == 0
        # This is the key assertion - single side should NOT generate combined page
        assert not result["should_generate_combined"]

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_multiple_sides_generates_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that multi-side neuron types do generate combined pages."""
        # Mock neuron statistics service to return multi-side data
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok({"left": 3, "right": 4, "middle": 0, "total": 7})
        )

        result = await detection_service.analyze_soma_sides("TM3")

        # Verify the analysis
        assert result["total_count"] == 7
        assert result["left_count"] == 3
        assert result["right_count"] == 4
        assert result["middle_count"] == 0
        assert result["sides_with_data"] == 2
        assert result["unknown_count"] == 0
        # Multi-side should generate combined page
        assert result["should_generate_combined"]

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_single_side_with_unknown_generates_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that single side with unknown sides generates combined pages."""
        # Mock neuron statistics service to return single side with unknown data
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok(
                {
                    "left": 3,
                    "right": 0,
                    "middle": 0,
                    "total": 8,  # 5 unknown neurons
                }
            )
        )

        result = await detection_service.analyze_soma_sides("MixedType")

        # Verify the analysis
        assert result["total_count"] == 8
        assert result["left_count"] == 3
        assert result["right_count"] == 0
        assert result["middle_count"] == 0
        assert result["sides_with_data"] == 1
        assert result["unknown_count"] == 5  # 8 - 3 = 5 unknown
        # Single side with unknown should generate combined page
        assert result["should_generate_combined"]

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_no_sides_with_neurons_generates_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that neuron types with no soma side data but existing neurons generate combined pages."""
        # Mock neuron statistics service to return no soma side data but existing neurons
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok(
                {
                    "left": 0,
                    "right": 0,
                    "middle": 0,
                    "total": 10,  # All unknown
                }
            )
        )

        result = await detection_service.analyze_soma_sides("UnknownSides")

        # Verify the analysis
        assert result["total_count"] == 10
        assert result["left_count"] == 0
        assert result["right_count"] == 0
        assert result["middle_count"] == 0
        assert result["sides_with_data"] == 0
        assert result["unknown_count"] == 10
        # No sides but neurons exist should generate combined page
        assert result["should_generate_combined"]

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_middle_only_no_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that middle-only neuron types don't generate combined pages."""
        # Mock neuron statistics service to return only middle side data
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok({"left": 0, "right": 0, "middle": 8, "total": 8})
        )

        result = await detection_service.analyze_soma_sides("MiddleOnly")

        # Verify the analysis
        assert result["total_count"] == 8
        assert result["left_count"] == 0
        assert result["right_count"] == 0
        assert result["middle_count"] == 8
        assert result["sides_with_data"] == 1
        assert result["unknown_count"] == 0
        # Single middle side should NOT generate combined page
        assert not result["should_generate_combined"]

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_right_only_no_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that right-only neuron types don't generate combined pages."""
        # Mock neuron statistics service to return only right side data
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok({"left": 0, "right": 12, "middle": 0, "total": 12})
        )

        result = await detection_service.analyze_soma_sides("RightOnly")

        # Verify the analysis
        assert result["total_count"] == 12
        assert result["left_count"] == 0
        assert result["right_count"] == 12
        assert result["middle_count"] == 0
        assert result["sides_with_data"] == 1
        assert result["unknown_count"] == 0
        # Single right side should NOT generate combined page
        assert not result["should_generate_combined"]

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_error_handling(
        self, detection_service, mock_dependencies
    ):
        """Test error handling in analyze_soma_sides."""
        # Mock neuron statistics service to return error
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Err("Database connection failed")
        )

        result = await detection_service.analyze_soma_sides("ErrorType")

        # Should return empty dict on error
        assert result == {}

    @pytest.mark.asyncio
    async def test_analyze_soma_sides_left_and_middle_generates_combined(
        self, detection_service, mock_dependencies
    ):
        """Test that left+middle combination generates combined pages."""
        # Mock neuron statistics service to return left and middle sides
        mock_dependencies[
            "neuron_statistics_service"
        ].get_soma_side_distribution = AsyncMock(
            return_value=Ok({"left": 4, "right": 0, "middle": 3, "total": 7})
        )

        result = await detection_service.analyze_soma_sides("LeftMiddle")

        # Verify the analysis
        assert result["total_count"] == 7
        assert result["left_count"] == 4
        assert result["right_count"] == 0
        assert result["middle_count"] == 3
        assert result["sides_with_data"] == 2
        assert result["unknown_count"] == 0
        # Two sides should generate combined page
        assert result["should_generate_combined"]
