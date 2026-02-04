import yaml
import json
from typing import Any, Dict

# Import python_magnetgeo classes to register YAML constructors
# This is required for yaml.load() to recognize custom tags like !<Ring>, !<Helix>, etc.
_MAGNETGEO_AVAILABLE = False
try:
    # Use lazy loading pattern for python_magnetgeo
    import python_magnetgeo as pmg

    # Register all YAML constructors using lazy loading
    # This triggers import and registration of all geometry classes
    pmg.verify_class_registration()

    _MAGNETGEO_AVAILABLE = True

except ImportError as e:
    # python_magnetgeo not available at all
    import warnings

    warnings.warn(
        f"python_magnetgeo not available: {e}. YAML loading for magnetgeo objects will fail."
    )


class TaggedDict(dict):
    def __init__(self, tag: str, value: Dict):
        # Remove !< and > from tag if present
        tag = tag.replace("!<", "").replace(">", "")
        self.tag = f"!<{tag}>"
        # Recursively process nested tagged dictionaries
        processed_value = self._process_value(value)
        super().__init__(processed_value)

    @staticmethod
    def _process_value(value: Any) -> Any:
        if isinstance(value, dict):
            if "__tag__" in value and "__value__" in value:
                return TaggedDict(value["__tag__"], value["__value__"])
            return {k: TaggedDict._process_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [TaggedDict._process_value(v) for v in value]
        return value


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle Enum types (convert to their value)
        from enum import Enum

        if isinstance(obj, Enum):
            return obj.value

        # Handle python_magnetgeo objects (they inherit from YAMLObjectBase, not yaml.YAMLObject)
        if _MAGNETGEO_AVAILABLE and hasattr(obj, "yaml_tag") and hasattr(obj, "__dict__"):
            # Get object data (excluding private attributes)
            data = {}
            for k, v in obj.__dict__.items():
                if not k.startswith("_"):
                    # Convert Enum values to their primitive values
                    if isinstance(v, Enum):
                        data[k] = v.value
                    else:
                        data[k] = v
            # Store both the tag and the data
            return {"__tag__": f"!<{obj.yaml_tag}>", "__value__": data}
        if isinstance(obj, yaml.YAMLObject):
            # Store both the tag and the data
            return {"__tag__": obj.yaml_tag, "__value__": obj.__dict__}
        if isinstance(obj, TaggedDict):
            return {"__tag__": obj.tag, "__value__": dict(obj)}
        return super().default(obj)


def json_to_yaml(json_str: str) -> str:
    def decode_tagged_dict(d: Dict[str, Any]) -> Any:
        if isinstance(d, dict):
            if "__tag__" in d and "__value__" in d:
                # Recursively process nested tagged dictionaries
                return TaggedDict(d["__tag__"], d["__value__"])
            return {k: decode_tagged_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [decode_tagged_dict(v) for v in d]
        return d

    # Custom presenter for TaggedDict
    def tagged_dict_presenter(dumper, data):
        return dumper.represent_mapping(data.tag, dict(data))

    # Register the presenter
    yaml.add_representer(TaggedDict, tagged_dict_presenter)

    # Parse JSON and decode tagged values
    json_data = json.loads(json_str)
    decoded_data = decode_tagged_dict(json_data)

    # Convert back to YAML
    return yaml.dump(decoded_data, sort_keys=False).replace("%3C", "<").replace("%3E", ">")


def yaml_to_json(yaml_str: str, base_dir: str = None) -> str:
    """
    Convert YAML string to JSON string, preserving custom tags.

    This function loads YAML content (including python_magnetgeo objects with
    custom tags like !<Ring>, !<Helix>, etc.) and converts it to JSON format
    while preserving type information via __tag__ and __value__ fields.

    IMPORTANT: When loading YAML files that contain string references to other
    YAML files (e.g., modelaxi: "file_name"), those files will be loaded from
    the base_dir. If base_dir is not provided, uses current working directory.

    Args:
        yaml_str: YAML string to convert
        base_dir: Base directory for resolving file references in YAML.
                  If None, uses current working directory. This is critical
                  for loading YAML files with references like:
                  modelaxi: "modelaxi_file"  # loads modelaxi_file.yaml
                  shape: "shape_file"        # loads shape_file.yaml

    Returns:
        JSON string representation with tag preservation

    Raises:
        yaml.YAMLError: If YAML parsing fails
        TypeError: If object cannot be JSON-serialized
        FileNotFoundError: If referenced YAML files cannot be found
    """
    import os

    # Load YAML with custom tags
    # Note: This requires python_magnetgeo classes to be imported first
    # so their YAML constructors are registered

    # Change to base_dir if provided to resolve file references correctly
    original_dir = os.getcwd()
    try:
        if base_dir:
            os.chdir(base_dir)

        data = yaml.load(yaml_str, Loader=yaml.FullLoader)

        # Note: The old code called data.update() if it existed, but this method
        # is no longer present in the latest python_magnetgeo refactored classes.
        # The objects are now fully initialized during construction via from_dict()
        # so no post-load update is needed.

        # Convert to JSON with tag preservation
        return json.dumps(data, cls=CustomEncoder, indent=4)
    finally:
        # Always restore original directory
        os.chdir(original_dir)
