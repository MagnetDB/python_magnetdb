import yaml
import json
from typing import Any, Dict


class TaggedDict(dict):
    def __init__(self, tag: str, value: Dict):
        super().__init__(value)
        self.tag = tag

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
                # Reconstruct tagged value
                return TaggedDict(d["__tag__"], d["__value__"])
            return {k: decode_tagged_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [decode_tagged_dict(v) for v in d]
        return d

    # Custom presenter for TaggedDict
    def tagged_dict_presenter(dumper, data):
        return dumper.represent_mapping(data.tag, data)

    # Register the presenter
    yaml.add_representer(TaggedDict, tagged_dict_presenter)

    # Parse JSON and decode tagged values
    json_data = json.loads(json_str)
    decoded_data = decode_tagged_dict(json_data)

    # Convert back to YAML
    return yaml.dump(decoded_data, sort_keys=False)


def yaml_to_json(yaml_str: str) -> str:
    # Load YAML with custom tags
    data = yaml.load(yaml_str, Loader=yaml.FullLoader)

    # Convert to JSON with tag preservation
    return json.dumps(data, cls=CustomEncoder, indent=4)

