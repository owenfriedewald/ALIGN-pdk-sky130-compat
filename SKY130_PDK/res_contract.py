"""Routing-rule contract for the Sky130 resistor generator."""


def resistor_routing_rules(pdk):
    """Return resistor pitches and widths from authoritative metal layers."""

    rules = {}
    for layer in ("M1", "M2", "M3"):
        entry = pdk.get(layer, {})
        pitch = int(entry.get("Pitch", 0))
        width = int(entry.get("Width", 0))
        if pitch <= 0 or width <= 0 or width >= pitch:
            raise ValueError(
                f"invalid resistor routing geometry for {layer}: "
                f"pitch={pitch}, width={width}"
            )
        rules[layer] = {"pitch": pitch, "width": width}
    return rules
