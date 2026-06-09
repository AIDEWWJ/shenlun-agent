from collections.abc import Mapping


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return ""


def render_prompt_template(template: str, variables: Mapping[str, object]) -> str:
    normalized = {key: (value if value is not None else "") for key, value in variables.items()}
    return template.format_map(_SafeFormatDict(normalized))
