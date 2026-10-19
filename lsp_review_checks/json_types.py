# A value parsed from a JSON file.
type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
