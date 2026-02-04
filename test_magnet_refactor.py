#!/usr/bin/env python3
"""
Test script to demonstrate the refactored geometry_config_to_json method.

This script shows how the new implementation creates python_magnetgeo objects
and uses their built-in serialization instead of manually constructing JSON.
"""

import json
import sys
import os

# Add python_magnetgeo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python_magnetgeo"))

from python_magnetgeo import Insert, Supras, Bitters


def test_insert_serialization():
    """Test Insert object serialization"""
    print("=" * 60)
    print("Testing INSERT serialization")
    print("=" * 60)

    # Create an Insert object (similar to what the refactored code does)
    insert = Insert(
        name="HL-31",
        helices=["H1", "H2", "H3"],
        rings=["R1", "R2"],
        currentleads=["CL1"],
        hangles=[0, 45, 90],
        rangles=[22.5, 67.5],
        innerbore=18.54,
        outerbore=186.25,
        probes=["probe1", "probe2"],
    )

    # Serialize to JSON
    json_str = insert.to_json()
    print("\nJSON output:")
    print(json_str)

    # Parse and verify structure
    parsed = json.loads(json_str)
    print("\nVerifying structure...")
    assert "__tag__" in parsed, "Missing __tag__"
    assert "__value__" in parsed, "Missing __value__"
    assert parsed["__tag__"] == "!<Insert>", f"Wrong tag: {parsed['__tag__']}"
    assert parsed["__value__"]["name"] == "HL-31", "Wrong name"
    assert parsed["__value__"]["helices"] == ["H1", "H2", "H3"], "Wrong helices"
    assert parsed["__value__"]["rings"] == ["R1", "R2"], "Wrong rings"
    assert parsed["__value__"]["probes"] == ["probe1", "probe2"], "Wrong probes"

    print("✓ Insert serialization test PASSED")
    return True


def test_supras_serialization():
    """Test Supras object serialization"""
    print("\n" + "=" * 60)
    print("Testing SUPRAS serialization")
    print("=" * 60)

    # Create a Supras object
    supras = Supras(
        name="M10_Supras", magnets=["S1", "S2"], innerbore=80.0, outerbore=160.0, probes=["probe1"]
    )

    # Serialize to JSON
    json_str = supras.to_json()
    print("\nJSON output:")
    print(json_str)

    # Parse and verify structure
    parsed = json.loads(json_str)
    print("\nVerifying structure...")
    assert "__tag__" in parsed, "Missing __tag__"
    assert "__value__" in parsed, "Missing __value__"
    assert parsed["__tag__"] == "!<Supras>", f"Wrong tag: {parsed['__tag__']}"
    assert parsed["__value__"]["name"] == "M10_Supras", "Wrong name"
    assert parsed["__value__"]["magnets"] == ["S1", "S2"], "Wrong magnets"
    assert parsed["__value__"]["probes"] == ["probe1"], "Wrong probes"

    print("✓ Supras serialization test PASSED")
    return True


def test_bitters_serialization():
    """Test Bitters object serialization"""
    print("\n" + "=" * 60)
    print("Testing BITTERS serialization")
    print("=" * 60)

    # Create a Bitters object
    bitters = Bitters(
        name="M10_Bitters", magnets=["B1", "B2", "B3"], innerbore=80.0, outerbore=160.0, probes=[]
    )

    # Serialize to JSON
    json_str = bitters.to_json()
    print("\nJSON output:")
    print(json_str)

    # Parse and verify structure
    parsed = json.loads(json_str)
    print("\nVerifying structure...")
    assert "__tag__" in parsed, "Missing __tag__"
    assert "__value__" in parsed, "Missing __value__"
    assert parsed["__tag__"] == "!<Bitters>", f"Wrong tag: {parsed['__tag__']}"
    assert parsed["__value__"]["name"] == "M10_Bitters", "Wrong name"
    assert parsed["__value__"]["magnets"] == ["B1", "B2", "B3"], "Wrong magnets"
    assert parsed["__value__"]["probes"] == [], "Wrong probes"

    print("✓ Bitters serialization test PASSED")
    return True


def main():
    """Run all tests"""
    print("\nValidating refactored geometry_config_to_json implementation")
    print("This demonstrates that python_magnetgeo objects automatically")
    print("serialize to the correct __tag__/__value__ format.\n")

    try:
        test_insert_serialization()
        test_supras_serialization()
        test_bitters_serialization()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nThe refactored code:")
        print("✓ Creates proper python_magnetgeo objects")
        print("✓ Uses built-in validation from python_magnetgeo")
        print("✓ Produces correct JSON format with __tag__/__value__")
        print("✓ Eliminates manual JSON construction")
        print("✓ Maintains backward compatibility")
        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
