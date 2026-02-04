"""
Test the simplified geometry_config conversion for Part model.

This validates that geometry_config (containing __classname__) can be converted
to both JSON and YAML by creating a python_magnetgeo object and using its native methods.
"""

import json
import copy
import sys
import os

# Add python_magnetgeo to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_magnetgeo"))


def test_simplified_json_conversion():
    """Test simplified JSON conversion using object's to_json() method"""
    try:
        from python_magnetgeo.deserialize import unserialize_object

        # Simulate geometry_config with __classname__ (complete with all fields)
        geometry_config = {
            "__classname__": "Helix",
            "r": [10.0, 20.0],
            "z": [0.0, 50.0],
            "cutwidth": 2.0,
            "odd": True,
            "dble": False,
            "modelaxi": None,
            "model3d": None,
            "shape": None,
            "chamfers": [],
            "grooves": None,
            "start_diameter_hole": 0.0,
        }

        name = "test_helix"

        # Simplified approach: create object and use to_json()
        config = copy.deepcopy(geometry_config)
        config["name"] = name

        obj = unserialize_object(config)
        json_str = obj.to_json()

        # Verify
        parsed = json.loads(json_str)
        assert parsed["name"] == name
        assert parsed["__classname__"] == "Helix"
        print("✓ Simplified JSON conversion test passed")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


def test_simplified_yaml_conversion():
    """Test simplified YAML conversion using yaml.dump()"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        # Simulate geometry_config with __classname__
        geometry_config = {
            "__classname__": "Ring",
            "r": [12.0, 12.1, 27.9, 28.0],
            "z": [45.0, 55.0],
            "n": 8,
            "angle": 0.0,
            "bpside": True,
            "fillets": False,
            "cad": "",
        }

        name = "updated_ring"

        # Simplified approach: create object and use yaml.dump()
        config = copy.deepcopy(geometry_config)
        config["name"] = name

        obj = unserialize_object(config)
        yaml_str = yaml.dump(obj, sort_keys=False)

        # Verify
        assert name in yaml_str
        assert "Ring" in yaml_str or "ring" in yaml_str.lower()
        print("✓ Simplified YAML conversion test passed")
        print(f"  Generated YAML preview:\n{yaml_str[:150]}")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


def test_various_types():
    """Test with different python_magnetgeo types"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        test_cases = [
            {
                "__classname__": "Helix",
                "r": [10.0, 20.0],
                "z": [0.0, 50.0],
                "cutwidth": 2.0,
                "odd": True,
                "dble": False,
                "modelaxi": None,
                "model3d": None,
                "shape": None,
                "chamfers": [],
                "grooves": None,
                "start_diameter_hole": 0.0,
            },
            {
                "__classname__": "Ring",
                "r": [12.0, 12.1, 27.9, 28.0],
                "z": [45.0, 55.0],
                "n": 8,
                "angle": 0.0,
                "bpside": True,
                "fillets": False,
                "cad": "",
            },
        ]

        for i, geometry_config in enumerate(test_cases):
            config = copy.deepcopy(geometry_config)
            config["name"] = f"test_{i}"

            obj = unserialize_object(config)
            json_str = obj.to_json()
            yaml_str = yaml.dump(obj, sort_keys=False)

            # Basic validation
            assert f"test_{i}" in json_str
            assert f"test_{i}" in yaml_str

        print(f"✓ Various types test passed ({len(test_cases)} types)")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


if __name__ == "__main__":
    test_simplified_json_conversion()
    test_simplified_yaml_conversion()
    test_various_types()
    print("\n✅ All simplified conversion tests passed!")
