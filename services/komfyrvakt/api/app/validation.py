"""Schema validation for ingested log values against an EntityType's open field schema."""

TYPE_CHECKS = {
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
}


def validate_values(values: dict, fields_schema: dict) -> list[str]:
    """Returns a list of validation errors (empty = valid).

    Unknown fields are rejected; missing fields are allowed (fields are
    optional per DESIGN.md §2.3).
    """
    errors: list[str] = []
    for field, value in values.items():
        spec = fields_schema.get(field)
        if spec is None:
            errors.append(f"Unknown field '{field}' (not declared on the entity type)")
            continue
        expected = spec.get("type", "number")
        check = TYPE_CHECKS.get(expected)
        if check is None:
            errors.append(f"Field '{field}' has unsupported declared type '{expected}'")
        elif value is not None and not check(value):
            errors.append(f"Field '{field}' expected {expected}, got {type(value).__name__}")
    return errors


def redact(values: dict, fields_schema: dict) -> dict:
    """Sensitive fields never enter AI context or context snapshots."""
    return {
        k: ("[redacted]" if fields_schema.get(k, {}).get("sensitive") else v)
        for k, v in values.items()
    }
