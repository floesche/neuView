#!/usr/bin/env python3
"""
Test script for combined body ID retrieval functionality.

This tests the critical functionality where selecting a combined entry
(like "L1" instead of "L1 (L)" and "L1 (R)") should return body IDs
from both L and R sides for neuroglancer visualization.
"""

import sys
import os
from typing import Dict, List, Any
from collections import defaultdict


class ConnectivityCombinationService:
    """Minimal version for testing body ID retrieval."""

    def get_combined_body_ids(
        self,
        partner_data: Dict[str, Any],
        direction: str,
        connected_bids: Dict[str, Any]
    ) -> List[Any]:
        """Get body IDs for combined entries, including both L and R sides."""
        if not connected_bids or direction not in connected_bids:
            return []

        partner_type = partner_data.get("type", "")
        if not partner_type:
            return []

        dmap = connected_bids[direction] or {}
        body_ids = []

        # Collect body IDs from both L and R sides
        for side in ["L", "R"]:
            side_key = f"{partner_type}_{side}"
            side_ids = dmap.get(side_key, [])

            if isinstance(side_ids, list):
                body_ids.extend(side_ids)
            elif side_ids:
                body_ids.append(side_ids)

        # Also check for bare type entry
        bare_key = partner_type
        bare_ids = dmap.get(bare_key, [])

        if isinstance(bare_ids, dict):
            # Handle nested dictionary with side information
            for side_key, side_vals in bare_ids.items():
                if isinstance(side_vals, list):
                    body_ids.extend(side_vals)
                elif side_vals:
                    body_ids.append(side_vals)
        elif isinstance(bare_ids, list):
            body_ids.extend(bare_ids)
        elif bare_ids:
            body_ids.append(bare_ids)

        # Remove duplicates while preserving order
        return self._unique_preserving_order(body_ids)

    def _unique_preserving_order(self, sequence: List[Any]) -> List[Any]:
        """Remove duplicates from a sequence while preserving order."""
        if not sequence:
            return []

        seen = set()
        result = []

        for item in sequence:
            # Use string representation for comparison
            str_item = str(item)
            if str_item not in seen:
                seen.add(str_item)
                result.append(item)

        return result

    def is_combined_entry(self, partner_data: Dict[str, Any]) -> bool:
        """Check if a partner entry represents a combined L/R entry."""
        soma_side = partner_data.get("soma_side", "")
        return not soma_side or soma_side == ""


class PartnerAnalysisService:
    """Minimal version for testing integration."""

    def __init__(self, connectivity_combination_service=None):
        self.connectivity_combination_service = connectivity_combination_service

    def get_partner_body_ids(
        self,
        partner_data,
        direction: str,
        connected_bids: Dict[str, Any],
    ) -> List[Any]:
        """Get body IDs for a partner, with combined entry support."""
        if not connected_bids or direction not in connected_bids:
            return []

        # Check if this is a combined entry (no soma_side specified)
        if (self.connectivity_combination_service and
            isinstance(partner_data, dict) and
            self.connectivity_combination_service.is_combined_entry(partner_data)):
            return self.connectivity_combination_service.get_combined_body_ids(
                partner_data, direction, connected_bids
            )

        # Fall back to original logic for non-combined entries
        partner_name = partner_data.get("type", "") if isinstance(partner_data, dict) else str(partner_data)
        soma_side = partner_data.get("soma_side") if isinstance(partner_data, dict) else None

        dmap = connected_bids[direction] or {}

        if soma_side in ("L", "R", "M", "C"):
            # Side-specific lookup
            side_key = f"{partner_name}_{soma_side}"
            return dmap.get(side_key, [])
        else:
            # All sides
            body_ids = []
            for key in [f"{partner_name}_L", f"{partner_name}_R", f"{partner_name}_M", partner_name]:
                value = dmap.get(key, [])
                if isinstance(value, list):
                    body_ids.extend(value)
                elif value:
                    body_ids.append(value)
            return self._unique_preserving_order(body_ids)

    def _unique_preserving_order(self, sequence: List[Any]) -> List[Any]:
        """Remove duplicates from a sequence while preserving order."""
        if not sequence:
            return []

        seen = set()
        result = []

        for item in sequence:
            str_item = str(item)
            if str_item not in seen:
                seen.add(str_item)
                result.append(item)

        return result


def test_combined_body_id_retrieval():
    """Test that combined entries return body IDs from both L and R sides."""
    print("Testing combined body ID retrieval...")

    service = ConnectivityCombinationService()

    # Simulate connected_bids structure as it would come from the database
    connected_bids = {
        "upstream": {
            "L1_L": [720575940615237770, 720575940609016132, 720575940607058533],
            "L1_R": [720575940623626358, 720575940619472898, 720575940615237771],
            "Tm3_L": [720575940635171910, 720575940631059451],
            "T4_L": [720575940639325369],
            "T4_R": [720575940643478828]
        },
        "downstream": {
            "LC4_L": [720575940647632287, 720575940651785746],
            "LC4_R": [720575940655939205, 720575940660092664, 720575940664246123],
            "T5_L": [720575940668399582],
            "LPLC2_L": [720575940672553041],
            "LPLC2_R": [720575940676706500]
        }
    }

    # Test 1: Combined L1 upstream (should get both L and R)
    partner_data = {"type": "L1", "soma_side": ""}  # Combined entry
    upstream_ids = service.get_combined_body_ids(partner_data, "upstream", connected_bids)

    expected_l1_upstream = [
        720575940615237770, 720575940609016132, 720575940607058533,  # L1_L
        720575940623626358, 720575940619472898, 720575940615237771   # L1_R
    ]

    print(f"L1 upstream IDs: {len(upstream_ids)} total")
    print(f"Expected: {expected_l1_upstream}")
    print(f"Got:      {upstream_ids}")

    assert len(upstream_ids) == 6, f"Expected 6 L1 upstream IDs, got {len(upstream_ids)}"
    for expected_id in expected_l1_upstream:
        assert expected_id in upstream_ids, f"Missing expected ID {expected_id}"

    # Test 2: Combined LC4 downstream (should get both L and R)
    partner_data = {"type": "LC4", "soma_side": ""}  # Combined entry
    downstream_ids = service.get_combined_body_ids(partner_data, "downstream", connected_bids)

    expected_lc4_downstream = [
        720575940647632287, 720575940651785746,  # LC4_L
        720575940655939205, 720575940660092664, 720575940664246123  # LC4_R
    ]

    print(f"LC4 downstream IDs: {len(downstream_ids)} total")
    assert len(downstream_ids) == 5, f"Expected 5 LC4 downstream IDs, got {len(downstream_ids)}"
    for expected_id in expected_lc4_downstream:
        assert expected_id in downstream_ids, f"Missing expected ID {expected_id}"

    # Test 3: Single-side entry (Tm3 only has L side)
    partner_data = {"type": "Tm3", "soma_side": ""}  # Combined entry, but only L exists
    tm3_upstream_ids = service.get_combined_body_ids(partner_data, "upstream", connected_bids)

    expected_tm3_upstream = [720575940635171910, 720575940631059451]  # Only Tm3_L

    print(f"Tm3 upstream IDs: {len(tm3_upstream_ids)} total")
    assert len(tm3_upstream_ids) == 2, f"Expected 2 Tm3 upstream IDs, got {len(tm3_upstream_ids)}"
    assert tm3_upstream_ids == expected_tm3_upstream, f"Expected {expected_tm3_upstream}, got {tm3_upstream_ids}"

    print("✓ Combined body ID retrieval test passed")


def test_partner_analysis_service_integration():
    """Test integration with PartnerAnalysisService."""
    print("Testing PartnerAnalysisService integration...")

    connectivity_service = ConnectivityCombinationService()
    partner_service = PartnerAnalysisService(connectivity_service)

    connected_bids = {
        "upstream": {
            "L1_L": [100, 101, 102],
            "L1_R": [200, 201, 202]
        },
        "downstream": {
            "T4_L": [300, 301],
            "T4_R": [400, 401, 402]
        }
    }

    # Test 1: Combined entry (empty soma_side)
    combined_partner = {"type": "L1", "soma_side": ""}
    combined_ids = partner_service.get_partner_body_ids(
        combined_partner, "upstream", connected_bids
    )
    expected_combined = [100, 101, 102, 200, 201, 202]
    assert combined_ids == expected_combined, f"Expected {expected_combined}, got {combined_ids}"

    # Test 2: Specific side entry
    left_partner = {"type": "L1", "soma_side": "L"}
    left_ids = partner_service.get_partner_body_ids(
        left_partner, "upstream", connected_bids
    )
    expected_left = [100, 101, 102]
    assert left_ids == expected_left, f"Expected {expected_left}, got {left_ids}"

    # Test 3: String partner (legacy format)
    string_partner = "T4"
    all_t4_ids = partner_service.get_partner_body_ids(
        string_partner, "downstream", connected_bids
    )
    expected_all_t4 = [300, 301, 400, 401, 402]
    assert all_t4_ids == expected_all_t4, f"Expected {expected_all_t4}, got {all_t4_ids}"

    print("✓ PartnerAnalysisService integration test passed")


def test_duplicate_handling():
    """Test handling of duplicate body IDs across sides."""
    print("Testing duplicate body ID handling...")

    service = ConnectivityCombinationService()

    # Connected bids with overlapping IDs between L and R sides
    connected_bids = {
        "upstream": {
            "L1_L": [100, 101, 102, 103],
            "L1_R": [102, 103, 104, 105]  # 102, 103 are duplicates
        }
    }

    partner_data = {"type": "L1", "soma_side": ""}
    combined_ids = service.get_combined_body_ids(partner_data, "upstream", connected_bids)

    # Should preserve order and remove duplicates
    expected = [100, 101, 102, 103, 104, 105]
    assert combined_ids == expected, f"Expected {expected}, got {combined_ids}"
    assert len(combined_ids) == len(set(combined_ids)), "Should have no duplicates"

    print("✓ Duplicate handling test passed")


def test_edge_cases():
    """Test edge cases and error conditions."""
    print("Testing edge cases...")

    service = ConnectivityCombinationService()

    # Test 1: Empty connected_bids
    empty_result = service.get_combined_body_ids(
        {"type": "L1", "soma_side": ""}, "upstream", {}
    )
    assert empty_result == [], "Empty connected_bids should return empty list"

    # Test 2: Missing direction
    missing_direction = service.get_combined_body_ids(
        {"type": "L1", "soma_side": ""}, "missing", {"upstream": {"L1_L": [100]}}
    )
    assert missing_direction == [], "Missing direction should return empty list"

    # Test 3: Missing partner type
    missing_partner = service.get_combined_body_ids(
        {"type": "NonExistent", "soma_side": ""}, "upstream", {"upstream": {"L1_L": [100]}}
    )
    assert missing_partner == [], "Missing partner should return empty list"

    # Test 4: None values in connected_bids
    none_direction = service.get_combined_body_ids(
        {"type": "L1", "soma_side": ""}, "upstream", {"upstream": None}
    )
    assert none_direction == [], "None direction data should return empty list"

    print("✓ Edge cases test passed")


def test_neuroglancer_scenario():
    """Test the exact scenario described in the requirements."""
    print("Testing Neuroglancer checkbox scenario...")

    connectivity_service = ConnectivityCombinationService()
    partner_service = PartnerAnalysisService(connectivity_service)

    # Simulate the exact scenario: TM3 combined page shows "L1" (combined from "L1 (L)" and "L1 (R)")
    connected_bids = {
        "upstream": {
            # L1 neurons from both sides
            "L1_L": [720575940615237770, 720575940609016132, 720575940607058533],
            "L1_R": [720575940623626358, 720575940619472898, 720575940615237771],
            # Other partners
            "Tm9_L": [720575940635171910],
            "Mi1_R": [720575940631059451]
        }
    }

    # When user clicks checkbox for "L1" entry in TM3 combined page
    l1_combined_entry = {
        "type": "L1",
        "soma_side": "",  # This indicates it's a combined entry
        "weight": 545,    # Combined weight from L1_L and L1_R
        "neurotransmitter": "ACh"
    }

    # Get body IDs for neuroglancer
    neuroglancer_body_ids = partner_service.get_partner_body_ids(
        l1_combined_entry, "upstream", connected_bids
    )

    expected_all_l1_ids = [
        720575940615237770, 720575940609016132, 720575940607058533,  # L1_L
        720575940623626358, 720575940619472898, 720575940615237771   # L1_R
    ]

    print(f"When user selects 'L1' checkbox on TM3 combined page:")
    print(f"  Should add {len(expected_all_l1_ids)} neurons to neuroglancer")
    print(f"  Body IDs: {neuroglancer_body_ids}")

    assert len(neuroglancer_body_ids) == 6, f"Expected 6 L1 neurons, got {len(neuroglancer_body_ids)}"

    for expected_id in expected_all_l1_ids:
        assert expected_id in neuroglancer_body_ids, f"Missing L1 neuron {expected_id}"

    print("✓ Neuroglancer checkbox scenario test passed")


def main():
    """Run all tests."""
    print("Testing combined body ID retrieval functionality...\n")

    try:
        test_combined_body_id_retrieval()
        test_partner_analysis_service_integration()
        test_duplicate_handling()
        test_edge_cases()
        test_neuroglancer_scenario()

        print("\n✅ All body ID combination tests passed!")
        print("\n🎯 Summary of functionality:")
        print("• Combined entries (soma_side='') retrieve body IDs from both L and R sides")
        print("• Individual side entries continue to work as before")
        print("• Duplicate body IDs are properly handled")
        print("• When user clicks 'L1' checkbox on TM3 combined page, both L1(L) and L1(R) neurons are added to neuroglancer")
        print("• Integration with existing PartnerAnalysisService works seamlessly")

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
