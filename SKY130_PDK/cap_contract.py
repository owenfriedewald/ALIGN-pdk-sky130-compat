"""Static connectivity contract for generated Sky130 MIM capacitors."""


def _positive_area_overlap(left, right):
    return (
        min(left[2], right[2]) > max(left[0], right[0])
        and min(left[3], right[3]) > max(left[1], right[1])
    )


def _shapes(terminals, *, layer=None, net_name=...):
    result = []
    for terminal in terminals:
        if layer is not None and terminal.get("layer") != layer:
            continue
        if net_name is not ... and terminal.get("netName") != net_name:
            continue
        result.append(terminal)
    return result


def _connected_component(start, shapes):
    reached = list(start)
    pending = list(start)
    while pending:
        current = pending.pop()
        for candidate in shapes:
            if candidate in reached:
                continue
            if _positive_area_overlap(current["rect"], candidate["rect"]):
                reached.append(candidate)
                pending.append(candidate)
    return reached


def validate_cap_terminal_topology(terminals, *, m4_pitch=None, m4_offset=0):
    """Reject MIM primitives whose streamed device topology is inconsistent.

    The compatibility PDK implements CAPM over the ALIGN M4 layer (official
    Sky130 met3).  M4 is the bottom electrode; CAPM is the top electrode and
    reaches the MINUS routing terminal through CapMIMContact and M5.  CAPM and
    its device contact are streamed device layers, not independent ALIGN
    routing nets.
    """

    plus_m4 = _shapes(terminals, layer="M4", net_name="PLUS")
    minus_m4 = _shapes(terminals, layer="M4", net_name="MINUS")
    device_m4 = _shapes(terminals, layer="M4", net_name=None)
    minus_m5 = _shapes(terminals, layer="M5", net_name="MINUS")
    capm = _shapes(terminals, layer="CapMIMLayer")
    contacts = _shapes(terminals, layer="CapMIMContact")

    if not any("pin" in shape.get("netType", "") for shape in plus_m4):
        raise ValueError("MIM capacitor requires a routable PLUS pin on M4")
    if not any("pin" in shape.get("netType", "") for shape in minus_m4):
        raise ValueError("MIM capacitor requires a routable MINUS pin on M4")
    if not minus_m5:
        raise ValueError("MIM capacitor requires a MINUS M5 top-plate strap")
    if not capm or not contacts:
        raise ValueError("MIM capacitor requires CAPM and CapMIMContact geometry")

    if m4_pitch is not None:
        for pin in plus_m4 + minus_m4:
            center = (pin["rect"][1] + pin["rect"][3]) // 2
            if (center - m4_offset) % m4_pitch:
                raise ValueError("MIM capacitor M4 routing pin is off grid")

    if any(shape.get("netName") is not None for shape in capm + contacts):
        raise ValueError(
            "CAPM device geometry must not be represented as an independent routing net"
        )

    if any(
        _positive_area_overlap(plus["rect"], minus["rect"])
        for plus in plus_m4
        for minus in minus_m4
    ):
        raise ValueError("MIM capacitor PLUS and MINUS M4 conductors overlap")

    if not device_m4:
        raise ValueError("MIM capacitor requires unnamed M4 bottom-plate geometry")
    if any(
        _positive_area_overlap(device["rect"], minus["rect"])
        for device in device_m4
        for minus in minus_m4
    ):
        raise ValueError("MIM capacitor bottom-plate geometry overlaps MINUS M4")

    plus_component = _connected_component(plus_m4, plus_m4 + device_m4)
    if not any(shape in plus_component for shape in device_m4):
        raise ValueError("MIM capacitor PLUS pin does not reach bottom-plate geometry")
    if not any(
        shape in plus_component
        and _positive_area_overlap(shape["rect"], device["rect"])
        for shape in device_m4
        for device in capm
    ):
        raise ValueError("MIM capacitor PLUS access chain does not reach the CAPM overlap")

    for contact in contacts:
        if not any(
            _positive_area_overlap(contact["rect"], device["rect"])
            for device in capm
        ):
            raise ValueError("MIM contact does not overlap CAPM")
        if not any(
            _positive_area_overlap(contact["rect"], strap["rect"])
            for strap in minus_m5
        ):
            raise ValueError("MIM contact does not overlap the MINUS M5 strap")
