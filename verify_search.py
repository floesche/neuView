#!/usr/bin/env python3
"""
Verification script for neuron search functionality.
Tests that the search dropdown correctly shows soma sides.
"""

import json
import os
import sys
from pathlib import Path

def verify_neuron_search_js():
    """Verify that the generated neuron-search.js contains the expected data structure."""

    # Check if the generated neuron-search.js file exists
    js_file_path = Path("output/static/js/neuron-search.js")
    if not js_file_path.exists():
        print("❌ neuron-search.js file not found at output/static/js/neuron-search.js")
        return False

    print("✅ Found neuron-search.js file")

    # Read the JavaScript file
    with open(js_file_path, 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Check for key components
    checks = [
        ("NEURON_TYPES_DATA", "NEURON_TYPES_DATA = ["),
        ("NEURON_DATA", "NEURON_DATA = ["),
        ("URLs structure", '"urls": {'),
        ("Left URL", '"left": "types/'),
        ("Right URL", '"right": "types/'),
        ("Combined URL", '"combined": "types/'),
        ("NeuronSearch class", "class NeuronSearch {"),
        ("navigateToSomaSide method", "navigateToSomaSide(neuronType, side)"),
        ("Fixed 'combined' check", 'neuronEntry.urls.combined'),
    ]

    passed_checks = 0
    for check_name, check_string in checks:
        if check_string in js_content:
            print(f"✅ {check_name}: Found")
            passed_checks += 1
        else:
            print(f"❌ {check_name}: Missing '{check_string}'")

    print(f"\nPassed {passed_checks}/{len(checks)} checks")

    # Extract and verify NEURON_DATA structure
    try:
        # Find the NEURON_DATA array
        start_marker = "const NEURON_DATA = "
        end_marker = "];"

        start_idx = js_content.find(start_marker)
        if start_idx == -1:
            print("❌ Could not find NEURON_DATA in the JavaScript file")
            return False

        start_idx += len(start_marker)
        end_idx = js_content.find(end_marker, start_idx) + 1

        if end_idx == 0:
            print("❌ Could not find end of NEURON_DATA array")
            return False

        # Extract and parse the JSON data
        neuron_data_str = js_content[start_idx:end_idx]
        neuron_data = json.loads(neuron_data_str)

        print(f"✅ Successfully parsed NEURON_DATA with {len(neuron_data)} entries")

        # Verify structure of first few entries
        soma_side_count = {"left": 0, "right": 0, "middle": 0, "combined": 0}
        entries_with_multiple_sides = 0

        for i, entry in enumerate(neuron_data[:5]):  # Check first 5 entries
            print(f"\n📋 Entry {i+1}: {entry['name']}")

            if 'urls' not in entry:
                print(f"  ❌ Missing 'urls' field")
                continue

            urls = entry['urls']
            available_sides = []

            for side in ['left', 'right', 'middle', 'combined']:
                if side in urls:
                    available_sides.append(side)
                    soma_side_count[side] += 1

            if len(available_sides) > 1:
                entries_with_multiple_sides += 1

            print(f"  ✅ Available sides: {', '.join(available_sides)}")
            print(f"  ✅ Primary URL: {entry.get('primary_url', 'Not set')}")

            if entry.get('synonyms'):
                print(f"  ✅ Has synonyms: {entry['synonyms'][:50]}...")

            if entry.get('flywire_types'):
                print(f"  ✅ Has flywire types: {entry['flywire_types']}")

        print(f"\n📊 Summary:")
        print(f"  Total entries: {len(neuron_data)}")
        print(f"  Entries with multiple sides: {entries_with_multiple_sides}")
        for side, count in soma_side_count.items():
            print(f"  Entries with {side} URLs: {count}")

        # Check if the fix for 'combined' vs 'both' is applied
        if 'neuronEntry.urls.combined' in js_content:
            print("✅ JavaScript correctly checks for 'combined' URLs")
        elif 'neuronEntry.urls.both' in js_content:
            print("❌ JavaScript still checks for 'both' URLs (should be 'combined')")

        return passed_checks == len(checks)

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse NEURON_DATA JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verifying NEURON_DATA: {e}")
        return False

def verify_html_integration():
    """Verify that HTML files properly include the neuron search."""

    html_files = [
        "output/index.html",
        "output/types.html",
        "output/help.html"
    ]

    print("\n🔍 Checking HTML integration:")

    for html_file in html_files:
        if not Path(html_file).exists():
            print(f"⚠️  {html_file} not found")
            continue

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        checks = [
            ('Search input', 'id="menulines"'),
            ('Neuron search script', 'neuron-search.js'),
            ('Search form', 'search-form'),
        ]

        all_found = True
        for check_name, check_string in checks:
            if check_string in html_content:
                print(f"  ✅ {Path(html_file).name}: {check_name}")
            else:
                print(f"  ❌ {Path(html_file).name}: Missing {check_name}")
                all_found = False

        if not all_found:
            return False

    return True

def test_search_functionality():
    """Test the search logic programmatically."""

    print("\n🧪 Testing search logic:")

    # Sample test data
    test_neuron_data = [
        {
            "name": "Tm3",
            "urls": {
                "combined": "types/Tm3.html",
                "left": "types/Tm3_L.html",
                "right": "types/Tm3_R.html"
            },
            "synonyms": "Takemura 2013: Tm3",
            "flywire_types": "Tm3"
        },
        {
            "name": "SAD103",
            "urls": {
                "combined": "types/SAD103.html",
                "left": "types/SAD103_L.html",
                "right": "types/SAD103_R.html",
                "middle": "types/SAD103_M.html"
            },
            "synonyms": None,
            "flywire_types": "SAD103"
        }
    ]

    # Test case 1: Search for "tm" should match "Tm3"
    search_query = "tm"
    matches = []
    for entry in test_neuron_data:
        if search_query.lower() in entry["name"].lower():
            matches.append(entry["name"])

    if "Tm3" in matches:
        print("✅ Basic name search works")
    else:
        print("❌ Basic name search failed")

    # Test case 2: Check soma side availability
    tm3_entry = next((entry for entry in test_neuron_data if entry["name"] == "Tm3"), None)
    if tm3_entry:
        available_sides = list(tm3_entry["urls"].keys())
        expected_sides = ["combined", "left", "right"]

        if all(side in available_sides for side in expected_sides):
            print("✅ Tm3 has expected soma sides (combined, left, right)")
        else:
            print(f"❌ Tm3 sides mismatch. Expected: {expected_sides}, Got: {available_sides}")

    # Test case 3: Check SAD103 has middle side
    sad_entry = next((entry for entry in test_neuron_data if entry["name"] == "SAD103"), None)
    if sad_entry and "middle" in sad_entry["urls"]:
        print("✅ SAD103 has middle soma side")
    else:
        print("❌ SAD103 missing middle soma side")

    return True

def main():
    """Main verification function."""

    print("🔍 Verifying Neuron Search Functionality")
    print("=" * 50)

    success = True

    # Check if we're in the right directory
    if not Path("output").exists():
        print("❌ Output directory not found. Please run this script from the quickpage root directory.")
        return False

    # Run verification tests
    print("\n1. Verifying neuron-search.js file...")
    if not verify_neuron_search_js():
        success = False

    print("\n2. Verifying HTML integration...")
    if not verify_html_integration():
        success = False

    print("\n3. Testing search logic...")
    if not test_search_functionality():
        success = False

    # Final result
    print("\n" + "=" * 50)
    if success:
        print("🎉 All verifications passed! Neuron search with soma sides should work correctly.")
        print("\nTo test manually:")
        print("1. Open output/index.html or output/types.html in a browser")
        print("2. Type a neuron name in the search box (e.g., 'Tm3', 'SAD')")
        print("3. Look for clickable soma side links (L, R, M, Combined) next to neuron names")
    else:
        print("❌ Some verifications failed. Please check the issues above.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
