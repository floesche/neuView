#!/usr/bin/env python3
"""
Minimal standalone test for connectivity combination logic.
"""

import sys
import os
from typing import Dict, List, Any
from collections import defaultdict

# Inline the ConnectivityCombinationService class for testing
class ConnectivityCombinationService:
    """Minimal version for testing."""

    def process_connectivity_for_display(self, connectivity_data: Dict[str, Any], soma_side: str) -> Dict[str, Any]:
        """Process connectivity data for display based on soma side."""
        if not connectivity_data or soma_side != "combined":
            return connectivity_data

        result = {
            "upstream": self._combine_partner_entries(connectivity_data.get("upstream", [])),
            "downstream": self._combine_partner_entries(connectivity_data.get("downstream", [])),
            "regional_connections": connectivity_data.get("regional_connections", {}),
            "note": connectivity_data.get("note", "")
        }
        return result

    def _combine_partner_entries(self, partners: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine partner entries with the same type but different soma sides."""
        if not partners:
            return []

        # Group partners by type
        type_groups = defaultdict(list)
        for partner in partners:
            partner_type = partner.get("type", "Unknown")
            type_groups[partner_type].append(partner)

        combined_partners = []

        for partner_type, group_partners in type_groups.items():
            if len(group_partners) == 1:
                # Single entry - remove soma side for display
                partner = group_partners[0].copy()
                soma_side = partner.get("soma_side", "")
                if soma_side in ["L", "R"]:
                    partner["soma_side"] = ""
                combined_partners.append(partner)
            else:
                # Multiple entries - combine them
                combined_partner = self._merge_partner_group(partner_type, group_partners)
                combined_partners.append(combined_partner)

        # Sort by weight and recalculate percentages
        combined_partners.sort(key=lambda x: x.get("weight", 0), reverse=True)
        self._recalculate_percentages(combined_partners)

        return combined_partners

    def _merge_partner_group(self, partner_type: str, partners: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple partner entries of the same type."""
        combined = {
            "type": partner_type,
            "soma_side": "",  # No soma side for combined entry
            "weight": 0,
            "connections_per_neuron": 0,
            "percentage": 0,
            "neurotransmitter": "Unknown"
        }

        # Track neurotransmitters by weight
        nt_weights = defaultdict(int)

        for partner in partners:
            weight = partner.get("weight", 0)
            combined["weight"] += weight
            combined["connections_per_neuron"] += partner.get("connections_per_neuron", 0)

            nt = partner.get("neurotransmitter", "Unknown")
            nt_weights[nt] += weight

        # Set most common neurotransmitter
        if nt_weights:
            combined["neurotransmitter"] = max(nt_weights.items(), key=lambda x: x[1])[0]

        return combined

    def _recalculate_percentages(self, partners: List[Dict[str, Any]]) -> None:
        """Recalculate percentages based on combined weights."""
        if not partners:
            return

        total_weight = sum(partner.get("weight", 0) for partner in partners)
        if total_weight == 0:
            return

        for partner in partners:
            weight = partner.get("weight", 0)
            percentage = (weight / total_weight * 100) if total_weight > 0 else 0
            partner["percentage"] = percentage


def test_basic_combination():
    """Test basic L/R partner combination."""
    print("Testing basic L/R partner combination...")

    service = ConnectivityCombinationService()

    connectivity_data = {
        "upstream": [
            {
                "type": "L1",
                "soma_side": "L",
                "neurotransmitter": "ACh",
                "weight": 100,
                "connections_per_neuron": 5.0,
                "percentage": 40.0
            },
            {
                "type": "L1",
                "soma_side": "R",
                "neurotransmitter": "ACh",
                "weight": 150,
                "connections_per_neuron": 7.5,
                "percentage": 60.0
            },
            {
                "type": "Tm3",
                "soma_side": "L",
                "neurotransmitter": "Glu",
                "weight": 80,
                "connections_per_neuron": 4.0,
                "percentage": 100.0
            }
        ]
    }

    # Test combined page processing
    combined_result = service.process_connectivity_for_display(connectivity_data, "combined")

    print(f"Original upstream partners: {len(connectivity_data['upstream'])}")
    print(f"Combined upstream partners: {len(combined_result['upstream'])}")

    # Check L1 combination
    l1_partners = [p for p in combined_result["upstream"] if p["type"] == "L1"]
    assert len(l1_partners) == 1, f"Expected 1 L1 partner, got {len(l1_partners)}"

    l1_partner = l1_partners[0]
    assert l1_partner["weight"] == 250, f"Expected combined weight 250, got {l1_partner['weight']}"
    assert l1_partner["connections_per_neuron"] == 12.5, f"Expected combined connections 12.5, got {l1_partner['connections_per_neuron']}"
    assert l1_partner["soma_side"] == "", f"Expected empty soma_side, got '{l1_partner['soma_side']}'"
    assert l1_partner["neurotransmitter"] == "ACh", f"Expected ACh, got {l1_partner['neurotransmitter']}"

    # Check Tm3 (single entry should have soma_side removed)
    tm3_partners = [p for p in combined_result["upstream"] if p["type"] == "Tm3"]
    assert len(tm3_partners) == 1, f"Expected 1 Tm3 partner, got {len(tm3_partners)}"
    tm3_partner = tm3_partners[0]
    assert tm3_partner["soma_side"] == "", f"Expected empty soma_side for single entry, got '{tm3_partner['soma_side']}'"

    print("✓ Basic combination test passed")


def test_individual_side_passthrough():
    """Test that individual side pages get unmodified data."""
    print("Testing individual side page passthrough...")

    service = ConnectivityCombinationService()

    connectivity_data = {
        "upstream": [
            {
                "type": "L1",
                "soma_side": "L",
                "neurotransmitter": "ACh",
                "weight": 100,
                "connections_per_neuron": 5.0,
                "percentage": 100.0
            }
        ]
    }

    # Test left side - should be unchanged
    left_result = service.process_connectivity_for_display(connectivity_data, "left")
    assert left_result == connectivity_data, "Left side data should be unchanged"

    # Test right side - should be unchanged
    right_result = service.process_connectivity_for_display(connectivity_data, "right")
    assert right_result == connectivity_data, "Right side data should be unchanged"

    print("✓ Individual side passthrough test passed")


def test_percentage_recalculation():
    """Test that percentages are recalculated correctly after combination."""
    print("Testing percentage recalculation...")

    service = ConnectivityCombinationService()

    connectivity_data = {
        "upstream": [
            {
                "type": "L1",
                "soma_side": "L",
                "weight": 100,
                "connections_per_neuron": 5.0,
                "percentage": 50.0  # Will be recalculated
            },
            {
                "type": "L1",
                "soma_side": "R",
                "weight": 100,
                "connections_per_neuron": 5.0,
                "percentage": 50.0  # Will be recalculated
            },
            {
                "type": "Tm3",
                "soma_side": "L",
                "weight": 200,
                "connections_per_neuron": 10.0,
                "percentage": 100.0  # Will be recalculated
            }
        ]
    }

    combined_result = service.process_connectivity_for_display(connectivity_data, "combined")

    # Total combined weight: L1 (200) + Tm3 (200) = 400
    # Expected percentages: L1 = 50%, Tm3 = 50%

    partners = combined_result["upstream"]
    assert len(partners) == 2, f"Expected 2 partners, got {len(partners)}"

    # Check that percentages sum to 100%
    total_percentage = sum(p["percentage"] for p in partners)
    assert abs(total_percentage - 100.0) < 0.01, f"Expected total 100%, got {total_percentage}%"

    print("✓ Percentage recalculation test passed")


def test_tm3_example():
    """Test the specific TM3 example from the user description."""
    print("Testing TM3 example...")

    service = ConnectivityCombinationService()

    # Simulate TM3 connectivity with L1 (L) and L1 (R) as top upstream partners
    connectivity_data = {
        "upstream": [
            {
                "type": "L1",
                "soma_side": "R",
                "neurotransmitter": "ACh",
                "weight": 300,
                "connections_per_neuron": 15.0,
                "percentage": 55.0
            },
            {
                "type": "L1",
                "soma_side": "L",
                "neurotransmitter": "ACh",
                "weight": 245,
                "connections_per_neuron": 12.25,
                "percentage": 45.0
            }
        ]
    }

    # Process for combined page
    combined_result = service.process_connectivity_for_display(connectivity_data, "combined")

    # Should have 1 L1 entry (combined)
    upstream_partners = combined_result["upstream"]
    assert len(upstream_partners) == 1, f"Expected 1 upstream partner, got {len(upstream_partners)}"

    l1_partner = upstream_partners[0]
    assert l1_partner["type"] == "L1", f"Expected L1, got {l1_partner['type']}"
    assert l1_partner["soma_side"] == "", f"Expected empty soma_side, got '{l1_partner['soma_side']}'"
    assert l1_partner["weight"] == 545, f"Expected combined weight 545, got {l1_partner['weight']}"
    assert l1_partner["neurotransmitter"] == "ACh", f"Expected ACh, got {l1_partner['neurotransmitter']}"
    assert abs(l1_partner["percentage"] - 100.0) < 0.01, f"Expected 100%, got {l1_partner['percentage']}%"

    print(f"Combined L1 entry: weight={l1_partner['weight']}, connections_per_neuron={l1_partner['connections_per_neuron']}")
    print("✓ TM3 example test passed")


def main():
    """Run all tests."""
    print("Running connectivity combination tests...\n")

    try:
        test_basic_combination()
        test_individual_side_passthrough()
        test_percentage_recalculation()
        test_tm3_example()

        print("\n✅ All tests passed!")
        print("\nThe connectivity combination service should now:")
        print("1. Combine L1 (L) and L1 (R) into single 'L1' entry for combined pages")
        print("2. Preserve individual L/R entries for side-specific pages")
        print("3. Remove soma side labels from display in combined pages")
        print("4. Correctly aggregate weights and connection counts")
        print("5. Recalculate percentages based on combined totals")

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
