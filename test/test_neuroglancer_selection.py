#!/usr/bin/env python3
"""
Test for neuroglancer soma side-aware bodyId selection.

This test verifies that the PageGenerator properly selects neurons based on
synapse count percentiles with soma side awareness.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import Mock


# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickpage.page_generator import PageGenerator
from quickpage.config import Config


class TestNeuroglancerSelection:
    """Test cases for neuroglancer bodyId selection."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock config
        self.config = Mock()
        self.config.output = Mock()
        self.config.output.template_dir = "templates"

        # Create page generator
        self.generator = PageGenerator(self.config, "test_output")

    def create_test_neurons_df(self, synapse_counts):
        """
        Create a test neurons DataFrame with specified synapse counts.

        Args:
            synapse_counts: List of tuples (bodyId, pre, post)
        """
        data = []
        for bodyid, pre, post in synapse_counts:
            data.append({
                'bodyId': bodyid,
                'pre': pre,
                'post': post,
                'type': 'TestType',
                'instance': f'TestType_{bodyid:03d}'
            })
        return pd.DataFrame(data)

    def test_select_95th_percentile_basic(self):
        """Test basic 95th percentile selection."""
        # Create test data with clear 95th percentile
        synapse_counts = [
            (1001, 10, 20),   # total: 30
            (1002, 20, 30),   # total: 50
            (1003, 30, 40),   # total: 70
            (1004, 40, 50),   # total: 90
            (1005, 50, 60),   # total: 110 <- this should be closest to 95th percentile
        ]

        neurons_df = self.create_test_neurons_df(synapse_counts)

        # Calculate expected 95th percentile
        total_synapses = [30, 50, 70, 90, 110]
        expected_percentile = np.percentile(total_synapses, 95)  # Should be 106

        # The neuron with 110 total synapses should be closest
        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)

        assert selected_bodyid == 1005, f"Expected bodyId 1005, got {selected_bodyid}"

    def test_select_different_percentiles(self):
        """Test selection with different percentile values."""
        synapse_counts = [
            (1001, 5, 5),     # total: 10
            (1002, 15, 15),   # total: 30
            (1003, 25, 25),   # total: 50
            (1004, 35, 35),   # total: 70
            (1005, 45, 45),   # total: 90
        ]

        neurons_df = self.create_test_neurons_df(synapse_counts)

        # Test 50th percentile (median) - should select middle value
        selected_50 = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 50)
        assert selected_50 == 1003, f"50th percentile should select bodyId 1003, got {selected_50}"

        # Test 90th percentile - should select high value
        selected_90 = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 90)
        assert selected_90 == 1005, f"90th percentile should select bodyId 1005, got {selected_90}"

        # Test 10th percentile - should select low value
        selected_10 = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 10)
        assert selected_10 == 1001, f"10th percentile should select bodyId 1001, got {selected_10}"

    def test_single_neuron(self):
        """Test selection with only one neuron."""
        synapse_counts = [(1001, 50, 60)]
        neurons_df = self.create_test_neurons_df(synapse_counts)

        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)
        assert selected_bodyid == 1001, "Should select the only available neuron"

    def test_identical_synapse_counts(self):
        """Test selection when multiple neurons have identical synapse counts."""
        synapse_counts = [
            (1001, 25, 25),   # total: 50
            (1002, 25, 25),   # total: 50
            (1003, 25, 25),   # total: 50
        ]

        neurons_df = self.create_test_neurons_df(synapse_counts)

        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)
        assert selected_bodyid in [1001, 1002, 1003], "Should select one of the neurons with identical counts"

    def test_missing_synapse_columns(self):
        """Test behavior when synapse columns are missing."""
        # Test with only pre column
        neurons_df = pd.DataFrame([
            {'bodyId': 1001, 'pre': 30},
            {'bodyId': 1002, 'pre': 50},
            {'bodyId': 1003, 'pre': 70}
        ])

        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)
        assert selected_bodyid == 1003, "Should use pre column when post is missing"

        # Test with only post column
        neurons_df = pd.DataFrame([
            {'bodyId': 1001, 'post': 20},
            {'bodyId': 1002, 'post': 40},
            {'bodyId': 1003, 'post': 60}
        ])

        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)
        assert selected_bodyid == 1003, "Should use post column when pre is missing"

        # Test with neither column (should fall back to first neuron)
        neurons_df = pd.DataFrame([
            {'bodyId': 1001, 'type': 'Test'},
            {'bodyId': 1002, 'type': 'Test'},
            {'bodyId': 1003, 'type': 'Test'}
        ])

        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)
        assert selected_bodyid == 1001, "Should fall back to first neuron when no synapse columns"

    def test_empty_dataframe(self):
        """Test error handling with empty DataFrame."""
        empty_df = pd.DataFrame()

        try:
            self.generator._select_bodyid_by_synapse_percentile(empty_df, 95)
            assert False, "Should have raised ValueError for empty DataFrame"
        except ValueError as e:
            assert "Cannot select from empty neurons DataFrame" in str(e)

    def test_real_world_scenario(self):
        """Test with realistic neuron data distribution."""
        # Create realistic synapse count distribution
        np.random.seed(42)  # For reproducible tests

        synapse_counts = []
        for i in range(50):  # Reduced for streamlined test
            pre = int(np.random.normal(200, 50))
            post = int(np.random.normal(150, 40))
            pre = max(10, pre)  # Ensure non-negative
            post = max(10, post)
            synapse_counts.append((2000 + i, pre, post))

        neurons_df = self.create_test_neurons_df(synapse_counts)
        selected_bodyid = self.generator._select_bodyid_by_synapse_percentile(neurons_df, 95)

        # Verify selection quality
        total_synapses = neurons_df['pre'] + neurons_df['post']
        percentile_95 = np.percentile(total_synapses, 95)
        selected_row = neurons_df[neurons_df['bodyId'] == selected_bodyid].iloc[0]
        selected_total = selected_row['pre'] + selected_row['post']

        # Should be close to 95th percentile
        assert abs(selected_total - percentile_95) <= 50, \
            f"Selected neuron should be close to 95th percentile: {percentile_95:.1f}, got {selected_total}"

    def test_integration_with_neuroglancer_url(self):
        """Test integration with the actual neuroglancer URL generation."""
        # Create mock environment and template
        mock_env = Mock()
        mock_template = Mock()
        mock_template.render.return_value = '{"test": "neuroglancer_state"}'
        mock_env.get_template.return_value = mock_template

        self.generator.env = mock_env

        # Create test neuron data
        synapse_counts = [
            (1001, 10, 20),   # total: 30
            (1002, 40, 50),   # total: 90
            (1003, 50, 60),   # total: 110 <- should be selected for 95th percentile
        ]

        neurons_df = self.create_test_neurons_df(synapse_counts)

        # Mock neuron data structure that would be passed to the method
        neuron_data = {
            'neurons': neurons_df,
            'summary': {'total_count': 3}
        }

        # Call the neuroglancer URL generation method
        url, template_vars = self.generator._generate_neuroglancer_url("TestType", neuron_data)

        # Verify that the template was called with the correct bodyId
        mock_template.render.assert_called_once()
        call_args = mock_template.render.call_args[1]

        assert 'visible_neurons' in call_args
        visible_neurons = call_args['visible_neurons']
        assert len(visible_neurons) == 1
        assert visible_neurons[0] == '1003', f"Expected bodyId 1003 to be selected, got {visible_neurons[0]}"

        # Verify URL structure
        assert url.startswith('https://clio-ng.janelia.org/#!')
        assert 'test' in url  # Should contain the encoded JSON

    def test_combined_soma_sides_selection(self):
        """Test selection with 'combined' soma sides - should select one neuron from each side."""
        # Create test data with left and right neurons
        synapse_counts = [
            # Left side neurons
            (1001, 10, 20, 'L'),   # total: 30
            (1002, 20, 30, 'L'),   # total: 50
            (1003, 50, 60, 'L'),   # total: 110 <- highest on left (95th percentile)

            # Right side neurons
            (1004, 15, 25, 'R'),   # total: 40
            (1005, 25, 35, 'R'),   # total: 60
            (1006, 45, 55, 'R'),   # total: 100 <- highest on right (95th percentile)
        ]

        neurons_df = self.create_test_neurons_df_with_soma_side(synapse_counts)

        # Test 'combined' selection
        selected_bodyids = self.generator._select_bodyids_by_soma_side(neurons_df, 'combined', 95)

        assert len(selected_bodyids) == 2, f"Expected 2 neurons for 'combined' sides, got {len(selected_bodyids)}"
        assert 1003 in selected_bodyids, "Should select highest left-side neuron (1003)"
        assert 1006 in selected_bodyids, "Should select highest right-side neuron (1006)"

    def test_specific_soma_side_selection(self):
        """Test selection with specific soma side."""
        synapse_counts = [
            (1001, 10, 20, 'L'),   # total: 30
            (1002, 50, 60, 'L'),   # total: 110 <- should be selected for left
            (1003, 15, 25, 'R'),   # total: 40
            (1004, 45, 55, 'R'),   # total: 100 <- should be selected for right
        ]

        neurons_df = self.create_test_neurons_df_with_soma_side(synapse_counts)

        # Test left side selection
        selected_bodyids = self.generator._select_bodyids_by_soma_side(neurons_df, 'left', 95)
        assert len(selected_bodyids) == 1, "Should select one neuron for specific side"
        assert selected_bodyids[0] == 1002, "Should select highest left-side neuron"

        # Test right side selection
        selected_bodyids = self.generator._select_bodyids_by_soma_side(neurons_df, 'right', 95)
        assert len(selected_bodyids) == 1, "Should select one neuron for specific side"
        assert selected_bodyids[0] == 1004, "Should select highest right-side neuron"

    def test_missing_soma_side_column(self):
        """Test behavior when somaSide column is missing."""
        # Create neurons without somaSide column
        synapse_counts = [
            (1001, 10, 20),
            (1002, 50, 60),  # Should be selected as highest
            (1003, 15, 25),
        ]
        neurons_df = self.create_test_neurons_df(synapse_counts)

        # Should fall back to single selection
        selected_bodyids = self.generator._select_bodyids_by_soma_side(neurons_df, 'combined', 95)
        assert len(selected_bodyids) == 1, "Should fall back to single selection"
        assert selected_bodyids[0] == 1002, "Should select highest synapse count neuron"

    def test_only_one_side_available(self):
        """Test 'combined' selection when only one side has neurons."""
        synapse_counts = [
            (1001, 10, 20, 'L'),   # total: 30
            (1002, 20, 30, 'L'),   # total: 50
            (1003, 50, 60, 'L'),   # total: 110 <- should be selected
        ]

        neurons_df = self.create_test_neurons_df_with_soma_side(synapse_counts)

        # Test 'combined' selection with only left side available
        selected_bodyids = self.generator._select_bodyids_by_soma_side(neurons_df, 'combined', 95)
        assert len(selected_bodyids) == 1, "Should select one neuron when only one side available"
        assert selected_bodyids[0] == 1003, "Should select highest available neuron"

    def test_neuroglancer_with_combined_sides(self):
        """Test neuroglancer URL generation with combined soma sides."""
        # Create mock environment and template
        mock_env = Mock()
        mock_template = Mock()
        mock_template.render.return_value = '{"test": "neuroglancer_state"}'
        mock_env.get_template.return_value = mock_template

        self.generator.env = mock_env

        # Create test neuron data with combined sides
        synapse_counts = [
            (1001, 10, 20, 'L'),   # total: 30
            (1002, 50, 60, 'L'),   # total: 110 <- highest left
            (1003, 15, 25, 'R'),   # total: 40
            (1004, 45, 55, 'R'),   # total: 100 <- highest right
        ]

        neurons_df = self.create_test_neurons_df_with_soma_side(synapse_counts)

        neuron_data = {
            'neurons': neurons_df,
            'summary': {'total_count': 4}
        }

        # Call neuroglancer URL generation with 'combined' soma side
        url, template_vars = self.generator._generate_neuroglancer_url("TestType", neuron_data, 'combined')

        # Verify template was called
        mock_template.render.assert_called_once()
        call_args = mock_template.render.call_args[1]

        assert 'visible_neurons' in call_args
        visible_neurons = call_args['visible_neurons']
        assert len(visible_neurons) == 2, f"Expected 2 visible neurons for both sides, got {len(visible_neurons)}"
        assert '1002' in visible_neurons, "Should include highest left-side neuron"
        assert '1004' in visible_neurons, "Should include highest right-side neuron"



    def create_test_neurons_df_with_soma_side(self, synapse_counts):
        """Create test neurons DataFrame with soma side information."""
        data = []
        for bodyid, pre, post, soma_side in synapse_counts:
            data.append({
                'bodyId': bodyid,
                'pre': pre,
                'post': post,
                'somaSide': soma_side,
                'type': 'TestType',
                'instance': f'TestType_{bodyid:03d}_{soma_side}'
            })
        return pd.DataFrame(data)


def test_percentile_selection():
    """Standalone test function for the percentile selection logic."""
    config = Mock()
    config.output = Mock()
    config.output.template_dir = "templates"

    generator = PageGenerator(config, "test_output")

    # Test basic functionality
    synapse_counts = [
        (1001, 10, 10),   # total: 20
        (1002, 20, 30),   # total: 50
        (1003, 30, 40),   # total: 70
        (1004, 40, 50),   # total: 90
        (1005, 45, 55),   # total: 100
    ]

    data = []
    for bodyid, pre, post in synapse_counts:
        data.append({
            'bodyId': bodyid,
            'pre': pre,
            'post': post
        })

    neurons_df = pd.DataFrame(data)

    # 95th percentile of [20, 50, 70, 90, 100] is 96
    # Neuron with 100 total synapses should be closest
    selected = generator._select_bodyid_by_synapse_percentile(neurons_df, 95)
    assert selected == 1005

    print("✓ Percentile selection test passed")


def run_all_tests():
    """Run core test methods."""
    test_instance = TestNeuroglancerSelection()

    tests = [
        ("Basic 95th percentile selection", lambda: (test_instance.setup_method(), test_instance.test_select_95th_percentile_basic())),
        ("Different percentiles", lambda: (test_instance.setup_method(), test_instance.test_select_different_percentiles())),
        ("Missing synapse columns", lambda: (test_instance.setup_method(), test_instance.test_missing_synapse_columns())),
        ("Empty dataframe", lambda: (test_instance.setup_method(), test_instance.test_empty_dataframe())),
        ("Combined soma sides selection", lambda: (test_instance.setup_method(), test_instance.test_combined_soma_sides_selection())),
        ("Specific soma side selection", lambda: (test_instance.setup_method(), test_instance.test_specific_soma_side_selection())),
        ("Missing soma side column", lambda: (test_instance.setup_method(), test_instance.test_missing_soma_side_column())),
        ("Neuroglancer with combined sides", lambda: (test_instance.setup_method(), test_instance.test_neuroglancer_with_combined_sides())),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: {e}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("Testing neuroglancer soma side-aware selection...")
    print("=" * 60)

    # Run basic validation
    test_percentile_selection()

    # Run core test suite
    print("\nRunning core test suite...")
    success = run_all_tests()

    if success:
        print("\n🎉 All core tests passed!")
        print("\nKey features verified:")
        print("  ✓ 95th percentile selection with soma side awareness")
        print("  ✓ Combined soma sides: one neuron from each hemisphere")
        print("  ✓ Specific sides: optimal neuron from target side")
        print("  ✓ Graceful fallback handling")
        print("  ✓ Integration with neuroglancer URL generation")
        print("\nSoma side-aware neuroglancer selection is working correctly!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
