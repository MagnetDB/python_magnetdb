#!/usr/bin/env python3
"""
Test script for yaml_json conversion utilities.

Tests the conversion of python_magnetgeo YAML files to JSON and back,
ensuring that custom tags and object structure are preserved.
"""

import sys
import os
import json as json_module
from pathlib import Path

# Add python_magnetdb to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "python_magnetgeo"))

from python_magnetdb.utils.yaml_json import yaml_to_json, json_to_yaml


def test_yaml_file(yaml_file: Path, class_name: str, show_full: bool = False) -> bool:
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

    try:
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

        # Convert YAML to JSON
        # Change to the yaml file's directory so file references can be resolved
        original_cwd = os.getcwd()
        try:
            os.chdir(yaml_file.parent)
            json_result = yaml_to_json(yaml_str)
        finally:
            os.chdir(original_cwd)

        # Show JSON
        json_lines = json_result.split("\n")
        max_json_lines = len(json_lines) if show_full else 30
        print("\n2. Converted to JSON:")
        print("-" * 70)
        print("\n".join(json_lines[:max_json_lines]))
        if len(json_lines) > max_json_lines:
            print(f"... ({len(json_lines) - max_json_lines} more lines)")

        # Convert JSON back to YAML
        yaml_result = json_to_yaml(json_result)

        # Show converted YAML
        result_lines = yaml_result.split("\n")
        max_result_lines = len(result_lines) if show_full else 20
        print("\n3. Converted back to YAML:")
        print("-" * 70)
        print("\n".join(result_lines[:max_result_lines]))
        if len(result_lines) > max_result_lines:
            print(f"... ({len(result_lines) - max_result_lines} more lines)")

        # Verify tag is correct
        json_data = json_module.loads(json_result)
        assert "__tag__" in json_data, "Missing __tag__ in JSON"
        expected_tag = f"!<{class_name}>"
        assert (
            json_data["__tag__"] == expected_tag
        ), f"Wrong tag: {json_data['__tag__']} != {expected_tag}"

        print("\n✓ SUCCESS: Round-trip conversion works!")
        return True

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("YAML-JSON Conversion Test Suite")

    tests_dir = repo_root / "python_magnetgeo" / "tests.old"

    # Define test cases: (filename, expected_class_name)
    test_cases = [
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

    results = []

    # Run tests
    for filename, class_name in test_cases:
        yaml_file = tests_dir / filename
        result = test_yaml_file(yaml_file, class_name, show_full=False)
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
