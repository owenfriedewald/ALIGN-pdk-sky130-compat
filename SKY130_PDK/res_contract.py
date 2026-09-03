"""Routing-rule contract for the Sky130 resistor generator."""


def resistor_routing_rules(pdk):
    """Return resistor pitches and widths from authoritative metal layers."""

    rules = {}
    for layer in ("M1", "M2", "M3"):
        # ALIGN passes its ``Pdk`` facade here, not the plain dictionary used
        # by the contract unit tests.  The facade deliberately exposes
        # mapping access through ``__getitem__`` but has no ``get`` method.
        entry = pdk[layer]
        pitch = int(entry.get("Pitch", 0))
        width = int(entry.get("Width", 0))
        if pitch <= 0 or width <= 0 or width >= pitch:
            raise ValueError(
                f"invalid resistor routing geometry for {layer}: "
                f"pitch={pitch}, width={width}"
            )
        rules[layer] = {"pitch": pitch, "width": width}
    return rules
