#!/usr/bin/env python3
"""
Test script for YAML/JSON round-trip conversion using python_magnetgeo's native methods.

This test validates that geometry objects can be:
1. Loaded from YAML files
2. Serialized to JSON using .to_json()
3. Deserialized from JSON back to objects
4. Serialized to YAML using yaml.dump()

This replaces the yaml_json.py utilities with python_magnetgeo's built-in functionality.
"""

import sys
import os
import json
import yaml
import tempfile
from pathlib import Path

# Add python_magnetdb to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "python_magnetgeo"))

import python_magnetgeo as pmg

# Register all YAML constructors for lazy loading
pmg.verify_class_registration()


def test_yaml_file(yaml_file: Path, class_name: str, show_full: bool = False) -> bool:
    """
    Generic test function for any YAML file using native python_magnetgeo methods.

    Args:
        yaml_file: Path to YAML file
        class_name: Expected class name (e.g., 'Ring', 'Helix')
        show_full: If True, show full output; otherwise truncate

    Returns:
        True if test passed, False otherwise, None if skipped
    """
    print("\n" + "=" * 70)
    print(f"Test: {class_name} - {yaml_file.name}")
    print("=" * 70)

    if not yaml_file.exists():
        print(f"⊘ SKIPPED: File not found: {yaml_file}")
        return None  # None means skipped, not failed

    try:
        # Step 1: Load YAML file into object
        print("\n1. Loading YAML file...")
        print("-" * 70)
        obj = pmg.load(str(yaml_file))
        
        # Verify class type
        actual_class = type(obj).__name__
        if actual_class != class_name:
            print(f"✗ Class mismatch: expected {class_name}, got {actual_class}")
            return False
        
        print(f"✓ Loaded {actual_class} object: {obj.name if hasattr(obj, 'name') else 'N/A'}")

        # Step 2: Convert object to JSON
        print("\n2. Converting to JSON using .to_json()...")
        print("-" * 70)
        json_str = obj.to_json()
        
        # Parse and verify JSON structure
        json_data = json.loads(json_str)
        if "__classname__" not in json_data:
            print("✗ Missing __classname__ in JSON")
            return False
        
        if json_data["__classname__"] != class_name:
            print(f"✗ Wrong __classname__: {json_data['__classname__']} != {class_name}")
            return False
        
        # Show JSON (truncated)
        json_lines = json_str.split("\n")
        max_json_lines = len(json_lines) if show_full else 30
        print("\n".join(json_lines[:max_json_lines]))
        if len(json_lines) > max_json_lines:
            print(f"... ({len(json_lines) - max_json_lines} more lines)")
        
        print(f"\n✓ JSON has correct __classname__: {json_data['__classname__']}")

        # Step 3: Load JSON back to object using temp file
        print("\n3. Loading JSON back to object...")
        print("-" * 70)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name
        
        try:
            # Use pmg.load() which can handle JSON files
            obj_from_json = pmg.load(tmp_path)
            
            # Verify class type
            restored_class = type(obj_from_json).__name__
            if restored_class != class_name:
                print(f"✗ Restored class mismatch: expected {class_name}, got {restored_class}")
                return False
            
            print(f"✓ Restored {restored_class} object from JSON")
            
        finally:
            os.unlink(tmp_path)

        # Step 4: Convert restored object to YAML
        print("\n4. Converting restored object to YAML...")
        print("-" * 70)
        yaml_str = yaml.dump(obj_from_json, default_flow_style=False)
        
        # Show YAML (truncated)
        yaml_lines = yaml_str.split("\n")
        max_yaml_lines = len(yaml_lines) if show_full else 20
        print("\n".join(yaml_lines[:max_yaml_lines]))
        if len(yaml_lines) > max_yaml_lines:
            print(f"... ({len(yaml_lines) - max_yaml_lines} more lines)")
        
        # Verify YAML has correct tag
        if f"!<{class_name}>" not in yaml_str:
            print(f"⚠ Warning: YAML tag !<{class_name}> not found in output")
        else:
            print(f"\n✓ YAML has correct tag: !<{class_name}>")

        print("\n✓ SUCCESS: Round-trip conversion works!")
        return True

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("YAML-JSON Round-Trip Test Suite (Native python_magnetgeo)")
    print("Using pmg.load(), .to_json(), and yaml.dump()")

    tests_dir = repo_root / "python_magnetgeo" / "tests.cfg"

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
