import yaml
import json
from typing import Any, Dict

# Import python_magnetgeo classes to register YAML constructors
# This is required for yaml.load() to recognize custom tags like !<Ring>, !<Helix>, etc.
_MAGNETGEO_AVAILABLE = False
try:
    # Import python_magnetgeo to access its class list
    import python_magnetgeo

    # Get the list of geometry classes from python_magnetgeo's __all__
    # Filter to only include actual geometry classes (exclude utilities and base classes)
    excluded_names = {
        "load",
        "loadObject",
        "list_registered_classes",
        "verify_class_registration",
        "YAMLObjectBase",
        "SerializableMixin",
        "ValidationError",
        "ValidationWarning",
        "GeometryValidator",
    }

    geometry_classes = [name for name in python_magnetgeo.__all__ if name not in excluded_names]

    # Import each geometry class to trigger YAML constructor registration
    _imported_classes = []
    for class_name in geometry_classes:
        try:
            exec(f"from python_magnetgeo import {class_name}")
            _imported_classes.append(class_name)
        except (ImportError, AttributeError):
            # Class not available in this version, skip it
            pass

    # Consider magnetgeo available if we successfully imported at least some core classes
    _MAGNETGEO_AVAILABLE = len(_imported_classes) > 0

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


def yaml_to_json(yaml_str: str) -> str:
    """
    Convert YAML string to JSON string, preserving custom tags.

    This function loads YAML content (including python_magnetgeo objects with
    custom tags like !<Ring>, !<Helix>, etc.) and converts it to JSON format
    while preserving type information via __tag__ and __value__ fields.

    Args:
        yaml_str: YAML string to convert

    Returns:
        JSON string representation with tag preservation

    Raises:
        yaml.YAMLError: If YAML parsing fails
        TypeError: If object cannot be JSON-serialized
    """
    # Load YAML with custom tags
    # Note: This requires python_magnetgeo classes to be imported first
    # so their YAML constructors are registered
    data = yaml.load(yaml_str, Loader=yaml.FullLoader)

    # Note: The old code called data.update() if it existed, but this method
    # is no longer present in the latest python_magnetgeo refactored classes.
    # The objects are now fully initialized during construction via from_dict()
    # so no post-load update is needed.

    # Convert to JSON with tag preservation
    return json.dumps(data, cls=CustomEncoder, indent=4)
