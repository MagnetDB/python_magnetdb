import yaml
import json
from typing import Any, Dict
from python_magnetgeo.deserialize import *

class TaggedDict(dict):
    def __init__(self, tag: str, value: Dict):
        # Remove !< and > from tag if present
        tag = tag.replace('!<', '').replace('>', '')
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
        if isinstance(obj, yaml.YAMLObject):
            # Store both the tag and the data
            return {
                "__tag__": obj.yaml_tag,
                "__value__": obj.__dict__
            }
        if isinstance(obj, TaggedDict):
            return {
                "__tag__": obj.tag,
                "__value__": dict(obj)
            }
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
    return yaml.dump(decoded_data, sort_keys=False).replace('%3C', '<').replace('%3E', '>')


def yaml_to_json(yaml_str: str) -> str:
    # Load YAML with custom tags
    data = yaml.load(yaml_str, Loader=yaml.FullLoader)

    # Convert to JSON with tag preservation
    return json.dumps(data, cls=CustomEncoder, indent=4)
