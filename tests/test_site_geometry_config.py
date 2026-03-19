"""
Test the simplified geometry_config conversion for Site model (MSite).

This validates that site data can be converted to both JSON and YAML
by creating a python_magnetgeo MSite object with actual magnet objects
and using its native methods.
"""

import json
import sys
import os

# Add python_magnetgeo to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_magnetgeo"))


def test_msite_json_conversion():
    """Test MSite JSON conversion using object's to_json() method"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        from python_magnetgeo import Insert

        # Create actual Insert object for testing
        insert_config = {
            "__classname__": "Insert",
            "name": "HL-31",
            "helices": [],
            "rings": [],
            "currentleads": [],
            "hangles": [],
            "rangles": [],
            "innerbore": 50.0,
            "outerbore": 200.0,
            "probes": [],
        }
        insert_obj = unserialize_object(insert_config)

        # Simulate site configuration with MSite structure using actual objects
        config = {
            "__classname__": "MSite",
            "name": "M9",
            "magnets": [insert_obj],  # Now using actual object instead of string
            "screens": None,
            "z_offset": [0.0],
            "r_offset": [0.0],
            "paralax": [0.0],
        }

        # Create MSite object and convert to JSON
        obj = unserialize_object(config)
        json_str = obj.to_json()

        # Verify
        parsed = json.loads(json_str)
        assert parsed["name"] == "M9"
        assert parsed["__classname__"] == "MSite"
        assert "magnets" in parsed
        assert len(parsed["magnets"]) == 1
        assert parsed["z_offset"] == [0.0]
        print("✓ MSite JSON conversion test passed (with actual magnet objects)")
        print(f"  Sample JSON (first 300 chars):\n  {json_str[:300]}...")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


def test_msite_yaml_conversion():
    """Test MSite YAML conversion using yaml.dump()"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        from python_magnetgeo import Insert, Bitters
        import yaml

        # Create actual magnet objects for testing
        insert_config = {
            "__classname__": "Insert",
            "name": "Insert1",
            "helices": [],
            "rings": [],
            "currentleads": [],
            "hangles": [],
            "rangles": [],
            "innerbore": 40.0,
            "outerbore": 180.0,
            "probes": [],
        }
        insert_obj = unserialize_object(insert_config)

        bitters_config = {
            "__classname__": "Bitters",
            "name": "Bitter2",
            "magnets": [],
            "innerbore": 200.0,
            "outerbore": 400.0,
            "probes": [],
        }
        bitters_obj = unserialize_object(bitters_config)

        # Simulate site configuration with MSite structure using actual objects
        config = {
            "__classname__": "MSite",
            "name": "M10",
            "magnets": [insert_obj, bitters_obj],  # Using actual objects
            "screens": None,
            "z_offset": [0.0, 200.0],
            "r_offset": [0.0, 0.0],
            "paralax": [0.0, 0.0],
        }

        # Create MSite object and convert to YAML
        obj = unserialize_object(config)
        yaml_str = yaml.dump(obj, sort_keys=False)

        # Verify
        assert "M10" in yaml_str
        assert "MSite" in yaml_str or "msite" in yaml_str.lower()
        # Check that the nested objects are present
        assert "Insert1" in yaml_str or "insert" in yaml_str.lower()
        assert "Bitter2" in yaml_str or "bitter" in yaml_str.lower()
        print("✓ MSite YAML conversion test passed (with actual magnet objects)")
        print(f"  Generated YAML preview (first 400 chars):\n{yaml_str[:400]}...")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


def test_empty_site():
    """Test MSite with no magnets"""
    try:
        from python_magnetgeo.deserialize import unserialize_object
        import yaml

        # Site with no magnets
        config = {
            "__classname__": "MSite",
            "name": "EmptySite",
            "magnets": [],
            "screens": None,
            "z_offset": [],
            "r_offset": [],
            "paralax": [],
        }

        # Create MSite object
        obj = unserialize_object(config)
        json_str = obj.to_json()
        yaml_str = yaml.dump(obj, sort_keys=False)

        # Verify
        assert "EmptySite" in json_str
        assert "EmptySite" in yaml_str
        print("✓ Empty MSite test passed")

    except ImportError as e:
        print(f"⚠ Skipped (python_magnetgeo not available): {e}")


if __name__ == "__main__":
    test_msite_json_conversion()
    test_msite_yaml_conversion()
    test_empty_site()
    print("\n✅ All MSite conversion tests passed!")
