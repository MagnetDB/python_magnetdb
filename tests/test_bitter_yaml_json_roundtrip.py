"""
Test YAML → Object → JSON → Object → YAML round-trip for Bitter objects.

This test validates that:
1. YAML files with nested objects (Bitter with ModelAxi) can be loaded
2. Objects can be serialized to JSON
3. JSON can be deserialized back to objects
4. Objects can be serialized to YAML with proper tags
"""

import json
import yaml
import sys
import os
from pathlib import Path

# Add python_magnetgeo to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_magnetgeo"))

from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.ModelAxi import ModelAxi
from python_magnetgeo import deserialize


def test_bitter_yaml_to_json_to_yaml_roundtrip():
    """
    Test the complete round-trip conversion:
    YAML file → Object → JSON → Object → YAML string
    
    Steps:
    1. Load Bitter from YAML file (with nested ModelAxi)
    2. Convert object to JSON using to_json()
    3. Parse JSON and create object from dictionary using from_json()
    4. Convert object to YAML using to_yaml()
    5. Verify YAML has proper tags (!<Bitter> and !<ModelAxi>)
    """
    
    # Step 1: Load Bitter from YAML file
    yaml_file = Path(__file__).parent.parent / "python_magnetgeo" / "tests.cfg" / "bitter1.yaml"
    
    assert yaml_file.exists(), f"Test YAML file not found: {yaml_file}"
    
    with open(yaml_file, "r") as f:
        yaml_content = f.read()
    
    print("\n" + "=" * 70)
    print("Step 1: Original YAML from file")
    print("=" * 70)
    print(yaml_content)
    
    # Load the YAML into a Bitter object
    bitter_obj_1 = yaml.load(yaml_content, Loader=yaml.FullLoader)
    assert isinstance(bitter_obj_1, Bitter), f"Expected Bitter object, got {type(bitter_obj_1)}"
    assert hasattr(bitter_obj_1, "modelaxi"), "Bitter object should have modelaxi attribute"
    assert isinstance(bitter_obj_1.modelaxi, ModelAxi), f"Expected ModelAxi, got {type(bitter_obj_1.modelaxi)}"
    
    print("\n✓ Successfully loaded Bitter object with nested ModelAxi")
    
    # Step 2: Convert object to JSON
    json_str = bitter_obj_1.to_json()
    
    print("\n" + "=" * 70)
    print("Step 2: JSON representation")
    print("=" * 70)
    print(json_str)
    
    # Verify JSON structure
    json_data = json.loads(json_str)
    assert "__classname__" in json_data, "JSON should contain __classname__ field"
    assert json_data["__classname__"] == "Bitter", "Wrong class name in JSON"
    assert "modelaxi" in json_data, "JSON should contain modelaxi field"
    assert isinstance(json_data["modelaxi"], dict), "modelaxi should be a dictionary"
    assert json_data["modelaxi"]["__classname__"] == "ModelAxi", "Nested object should have __classname__"
    
    print("\n✓ JSON has correct structure with __classname__ fields")
    
    # Step 3: Create object from JSON
    bitter_obj_2 = json.loads(json_str, object_hook=deserialize.unserialize_object)
    
    assert isinstance(bitter_obj_2, Bitter), f"Expected Bitter object, got {type(bitter_obj_2)}"
    assert hasattr(bitter_obj_2, "modelaxi"), "Recreated Bitter should have modelaxi"
    assert isinstance(bitter_obj_2.modelaxi, ModelAxi), f"Expected ModelAxi, got {type(bitter_obj_2.modelaxi)}"
    
    # Verify attributes match
    assert bitter_obj_2.name == bitter_obj_1.name, "Name mismatch"
    assert bitter_obj_2.r == bitter_obj_1.r, "r mismatch"
    assert bitter_obj_2.z == bitter_obj_1.z, "z mismatch"
    assert bitter_obj_2.modelaxi.name == bitter_obj_1.modelaxi.name, "ModelAxi name mismatch"
    assert bitter_obj_2.modelaxi.h == bitter_obj_1.modelaxi.h, "ModelAxi h mismatch"
    
    print("\n✓ Successfully recreated Bitter object from JSON")
    
    # Step 4: Convert object to YAML
    yaml_str = bitter_obj_2.to_yaml()
    
    print("\n" + "=" * 70)
    print("Step 3: YAML representation (from recreated object)")
    print("=" * 70)
    print(yaml_str)
    
    # Step 5: Verify YAML has proper tags
    assert "!<Bitter>" in yaml_str, "YAML should contain !<Bitter> tag"
    assert "!<ModelAxi>" in yaml_str, "YAML should contain !<ModelAxi> tag for nested object"
    assert "__classname__" not in yaml_str, "YAML should not contain __classname__ field"
    
    # Load the YAML to verify it's valid
    bitter_obj_3 = yaml.load(yaml_str, Loader=yaml.FullLoader)
    assert isinstance(bitter_obj_3, Bitter), "Round-trip YAML should load to Bitter object"
    assert isinstance(bitter_obj_3.modelaxi, ModelAxi), "Nested object should be ModelAxi"
    
    # Verify final object matches original
    assert bitter_obj_3.name == bitter_obj_1.name, "Final name mismatch"
    assert bitter_obj_3.r == bitter_obj_1.r, "Final r mismatch"
    assert bitter_obj_3.z == bitter_obj_1.z, "Final z mismatch"
    assert bitter_obj_3.modelaxi.name == bitter_obj_1.modelaxi.name, "Final ModelAxi name mismatch"
    assert bitter_obj_3.modelaxi.h == bitter_obj_1.modelaxi.h, "Final ModelAxi h mismatch"
    
    print("\n✓ YAML has correct tags (!<Bitter> and !<ModelAxi>)")
    print("\n" + "=" * 70)
    print("✓ COMPLETE ROUND-TRIP SUCCESS")
    print("=" * 70)
    print("YAML → Object → JSON → Object → YAML conversion works correctly!")
    print("- YAML uses tags: !<Bitter>, !<ModelAxi>")
    print("- JSON uses __classname__ fields")
    print("- All nested objects preserved correctly")


if __name__ == "__main__":
    test_bitter_yaml_to_json_to_yaml_roundtrip()
