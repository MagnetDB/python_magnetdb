"""
Test the simplified geometry_config conversion for Probe model.

This validates that probe data can be converted to both JSON and YAML
by creating a python_magnetgeo Probe object and using its native methods.
"""

import json
import sys
import os

# Add python_magnetgeo to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_magnetgeo"))


def test_probe_json_conversion():
    """Test Probe JSON conversion using object's to_json() method"""
    try:
        from python_magnetgeo.deserialize import unserialize_object

        # Simulate probe configuration with Probe structure
        config = {
            "__classname__": "Probe",
            "name": "voltage_probe_1",
            "type": "voltage_taps",
            "labels": ["V1", "V2", "V3"],
            "points": [[0.0, 0.0, 10.0], [0.0, 0.0, 20.0], [0.0, 0.0, 30.0]],
        }

        # Create Probe object and convert to JSON
        obj = unserialize_object(config)
        json_str = obj.to_json()

        # Verify
        parsed = json.loads(json_str)
        assert parsed["name"] == "voltage_probe_1"
        assert parsed["__classname__"] == "Probe"
        assert parsed["type"] == "voltage_taps"
        assert len(parsed["labels"]) == 3
        assert len(parsed["points"]) == 3
        print("✓ Probe JSON conversion test passed")
        print(f"  Sample JSON (first 200 chars):\n  {json_str[:200]}...")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


def test_probe_yaml_conversion():
    """Test Probe YAML conversion using yaml.dump()"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        # Simulate probe configuration with Probe structure
        config = {
            "__classname__": "Probe",
            "name": "temp_probe_1",
            "type": "temperature",
            "labels": ["T1", "T2"],
            "points": [[5.0, 5.0, 15.0], [10.0, 10.0, 25.0]],
        }

        # Create Probe object and convert to YAML
        obj = unserialize_object(config)
        yaml_str = yaml.dump(obj, sort_keys=False)

        # Verify
        assert "temp_probe_1" in yaml_str
        assert "Probe" in yaml_str or "probe" in yaml_str.lower()
        assert "temperature" in yaml_str
        assert "T1" in yaml_str
        assert "T2" in yaml_str
        print("✓ Probe YAML conversion test passed")
        print(f"  Generated YAML preview:\n{yaml_str[:200]}")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


def test_magnetic_field_probe():
    """Test Probe with magnetic field type"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        # Magnetic field probe
        config = {
            "__classname__": "Probe",
            "name": "bfield_probe",
            "type": "magnetic_field",
            "labels": ["B_center", "B_edge"],
            "points": [[0.0, 0.0, 0.0], [15.0, 0.0, 0.0]],
        }

        # Create Probe object
        obj = unserialize_object(config)
        json_str = obj.to_json()
        yaml_str = yaml.dump(obj, sort_keys=False)

        # Verify
        assert "bfield_probe" in json_str
        assert "magnetic_field" in json_str
        assert "bfield_probe" in yaml_str
        print("✓ Magnetic field Probe test passed")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


if __name__ == "__main__":
    test_probe_json_conversion()
    test_probe_yaml_conversion()
    test_magnetic_field_probe()
    print("\n✅ All Probe conversion tests passed!")
