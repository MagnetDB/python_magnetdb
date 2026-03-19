#!/usr/bin/env python3
"""
Test script for YAML to JSON to YAML conversion.

Tests the conversion of python_magnetgeo YAML files to JSON and back,
ensuring that custom tags and object structure are preserved.
Uses native python_magnetgeo methods instead of yaml_json utilities.
"""

import sys
import os
import json as json_module
import yaml
import pytest
from pathlib import Path

# Add python_magnetdb to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "python_magnetgeo"))

from python_magnetgeo import deserialize


def run_yaml_file_test(yaml_file: Path, class_name: str, show_full: bool = False) -> bool:
    """
    Generic test function for any YAML file.

    Args:
        yaml_file: Path to YAML file
        class_name: Expected class name (e.g., 'Ring', 'Helix')
        show_full: If True, show full output; otherwise truncate

    Returns:
        True if test passed, False otherwise
    """
    print("\n" + "=" * 70)
    print(f"Test: {class_name} - {yaml_file.name}")
    print("=" * 70)

    if not yaml_file.exists():
        print(f"⊘ SKIPPED: File not found: {yaml_file}")
        return None  # None means skipped, not failed

    # Save current directory and change to yaml_file directory
    # This allows referenced YAML files to be found
    original_cwd = os.getcwd()
    yaml_dir = yaml_file.parent

    try:
        os.chdir(yaml_dir)

        with open(yaml_file, "r") as f:
            yaml_str = f.read()

        if not yaml_str.strip():
            print("⊘ SKIPPED: Empty file")
            return None

        # Show original YAML
        lines = yaml_str.split("\n")
        max_lines = len(lines) if show_full else 20
        print("\n1. Original YAML:")
        print("-" * 70)
        print("\n".join(lines[:max_lines]))
        if len(lines) > max_lines:
            print(f"... ({len(lines) - max_lines} more lines)")

        # Load YAML into object
        obj = yaml.load(yaml_str, Loader=yaml.FullLoader)

        # Verify class type
        actual_class = type(obj).__name__
        if actual_class != class_name:
            print(f"✗ Class mismatch: expected {class_name}, got {actual_class}")
            return False

        # Convert object to JSON using to_json()
        json_result = obj.to_json()

        # Show JSON
        json_lines = json_result.split("\n")
        max_json_lines = len(json_lines) if show_full else 30
        print("\n2. Converted to JSON:")
        print("-" * 70)
        print("\n".join(json_lines[:max_json_lines]))
        if len(json_lines) > max_json_lines:
            print(f"... ({len(json_lines) - max_json_lines} more lines)")

        # Verify JSON structure
        json_data = json_module.loads(json_result)
        if "__classname__" not in json_data:
            print("✗ Missing __classname__ in JSON")
            return False

        if json_data["__classname__"] != class_name:
            print(f"✗ Wrong __classname__: {json_data['__classname__']} != {class_name}")
            return False

        # Convert JSON back to object
        obj_from_json = json_module.loads(json_result, object_hook=deserialize.unserialize_object)

        # Verify restored object class type
        restored_class = type(obj_from_json).__name__
        if restored_class != class_name:
            print(f"✗ Restored class mismatch: expected {class_name}, got {restored_class}")
            return False

        # Convert restored object to YAML using to_yaml()
        yaml_result = obj_from_json.to_yaml()

        # Show converted YAML
        result_lines = yaml_result.split("\n")
        max_result_lines = len(result_lines) if show_full else 20
        print("\n3. Converted back to YAML:")
        print("-" * 70)
        print("\n".join(result_lines[:max_result_lines]))
        if len(result_lines) > max_result_lines:
            print(f"... ({len(result_lines) - max_result_lines} more lines)")

        # Verify YAML tag is correct
        expected_tag = f"!<{class_name}>"
        if expected_tag not in yaml_result:
            print(f"✗ Missing YAML tag {expected_tag}")
            return False

        print("\n✓ SUCCESS: Round-trip conversion works!")
        return True

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # Restore original directory
        os.chdir(original_cwd)


# Define test cases: (filename, expected_class_name)
TEST_CASES = [
    # Ring tests
    ("ring1.yaml", "Ring"),
    ("ring2.yaml", "Ring"),
    # Helix tests (complex with nested objects)
    ("helix1.yaml", "Helix"),
    ("helix2.yaml", "Helix"),
    ("helix3.yaml", "Helix"),
    # InnerCurrentLead tests
    ("inner_lead.yaml", "InnerCurrentLead"),
    ("inner.yaml", "InnerCurrentLead"),
    ("lead1.yaml", "InnerCurrentLead"),
    # Probe tests
    ("probe_ref1.yaml", "Probe"),
    ("probe_ref2.yaml", "Probe"),
    # Insert tests (references helices, rings, currentleads)
    ("insert1.yaml", "Insert"),
    # MSite tests (references inserts)
    ("msite1.yaml", "MSite"),
    # Bitter tests
    ("bitter1.yaml", "Bitter"),
    # Bitters tests
    ("bitters1.yaml", "Bitters"),
    # Supra tests
    ("supra1.yaml", "Supra"),
    # Supras tests
    ("supras1.yaml", "Supras"),
    # ModelAxi tests
    ("modelaxi1.yaml", "ModelAxi"),
    # Model3D tests
    ("model3d1.yaml", "Model3D"),
    # Shape tests
    ("shape1.yaml", "Shape"),
    # Contour2D tests
    ("contour2d1.yaml", "Contour2D"),
    # CoolingSlit tests (with nested Contour2D)
    ("coolingslit1.yaml", "CoolingSlit"),
    # Tierod tests (with nested Contour2D)
    ("tierod1.yaml", "Tierod"),
    # Chamfer tests
    ("chamfer1.yaml", "Chamfer"),
    # Groove tests
    ("groove1.yaml", "Groove"),
]


@pytest.mark.parametrize("filename,class_name", TEST_CASES)
def test_yaml_file(filename: str, class_name: str):
    """Test YAML to JSON to YAML conversion for geometry files."""
    tests_dir = repo_root / "python_magnetgeo" / "tests.cfg"
    yaml_file = tests_dir / filename

    # Skip if file doesn't exist
    if not yaml_file.exists():
        pytest.skip(f"File not found: {yaml_file}")

    # Run the test
    result = run_yaml_file_test(yaml_file, class_name, show_full=False)

    # Handle skipped tests (empty files)
    if result is None:
        pytest.skip("Empty file")

    # Assert test passed
    assert result, f"Test failed for {filename}"


def main():
    """Run all tests (for standalone script execution)."""
    print("YAML-JSON Conversion Test Suite")
    print("Using native python_magnetgeo methods: yaml.load(), to_json(), to_yaml()")

    tests_dir = repo_root / "python_magnetgeo" / "tests.cfg"

    results = []

    # Run tests
    for filename, class_name in TEST_CASES:
        yaml_file = tests_dir / filename
        result = run_yaml_file_test(yaml_file, class_name, show_full=False)
        if result is not None:  # None means skipped
            results.append((f"{class_name}: {filename}", result))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)

    return all(p for _, p in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
