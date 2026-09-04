"""Static connectivity contract for generated Sky130 MIM capacitors."""


def horizontal_pin_placement_grid_constraint(*, pitch, routing_offset=0):
    """Return the ALIGN placement contract that preserves a horizontal pin grid.

    ``PlaceOnGrid(direction="H")`` constrains an instance's Y transform.  A
    horizontal routing pin whose native center is congruent to
    ``routing_offset`` remains on that routing grid when an unmirrored instance
    has translation offset zero, or when a vertically mirrored instance has
    translation offset ``2 * routing_offset``.  Keeping this construction in a
    pure helper makes the compatibility contract testable without importing an
    installed ALIGN package.
    """

    if not isinstance(pitch, int) or isinstance(pitch, bool) or pitch <= 0:
        raise ValueError("routing pitch must be a positive integer")
    if (
        not isinstance(routing_offset, int)
        or isinstance(routing_offset, bool)
        or not 0 <= routing_offset < pitch
    ):
        raise ValueError("routing offset must be an integer within the pitch")

    positive_offset = 0
    negative_offset = (2 * routing_offset) % pitch
    if positive_offset == negative_offset:
        ored_terms = [
            {"offsets": [positive_offset], "scalings": [1, -1]},
        ]
    else:
        ored_terms = [
            {"offsets": [positive_offset], "scalings": [1]},
            {"offsets": [negative_offset], "scalings": [-1]},
        ]
    return {
        "constraint": "PlaceOnGrid",
        "direction": "H",
        "pitch": pitch,
        "ored_terms": ored_terms,
    }


def highest_grid_track_with_positive_overlap(
    rect_top,
    *,
    pitch,
    width,
    offset=0,
):
    """Return the highest routing track whose wire overlaps a rectangle.

    Rectangle and wire coordinates are integral PDK database units.  Positive
    area overlap requires the wire's lower edge to be strictly below the
    rectangle top; merely touching the edge is not electrical connectivity.
    """

    if pitch <= 0 or width <= 0:
        raise ValueError("routing pitch and width must be positive")
    if width % 2:
        raise ValueError("routing width must be even")
    return (rect_top + width // 2 - offset - 1) // pitch


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


def _axis_gap(left, right, lower, upper):
    return max(left[lower] - right[upper], right[lower] - left[upper], 0)


def _contains(outer, inner):
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and outer[2] >= inner[2]
        and outer[3] >= inner[3]
    )


def routing_track_blockage_rects(
    halo,
    conductive_rects,
    *,
    pitch,
    width,
    offset=0,
):
    """Cover a horizontal-layer halo with legal-width routing obstructions.

    A broad rectangular obstruction on a unidirectional routing layer is
    interpreted by ALIGN's duplicate checker as a conductor with a nonstandard
    width.  More importantly, such a rectangle can overlap and seal a legal
    pin.  This helper instead blocks only the uncovered portions of each M4
    routing track.  Existing plate and pin metal remains available as the
    obstacle on its occupied interval, leaving named pins reachable through
    the orthogonal routing layer.
    """

    if len(halo) != 4 or halo[0] >= halo[2] or halo[1] >= halo[3]:
        raise ValueError("routing halo must be a nonempty rectangle")
    if pitch <= 0 or width <= 0 or width % 2:
        raise ValueError("routing pitch and even width must be positive")
    if not 0 <= offset < pitch:
        raise ValueError("routing offset must lie within the pitch")

    half_width = width // 2
    first_track = (halo[1] - half_width - offset) // pitch
    last_track = (halo[3] + half_width - offset - 1) // pitch
    result = []
    for track in range(first_track, last_track + 1):
        center = offset + track * pitch
        track_bottom = center - half_width
        track_top = center + half_width
        if min(track_top, halo[3]) <= max(track_bottom, halo[1]):
            continue

        intervals = []
        for rect in conductive_rects:
            if min(track_top, rect[3]) <= max(track_bottom, rect[1]):
                continue
            left = max(halo[0], rect[0])
            right = min(halo[2], rect[2])
            if left < right:
                intervals.append((left, right))
        intervals.sort()

        cursor = halo[0]
        for left, right in intervals:
            if left > cursor:
                result.append([cursor, track_bottom, left, track_top])
            cursor = max(cursor, right)
        if cursor < halo[2]:
            result.append([cursor, track_bottom, halo[2], track_top])
    return result


def validate_cap_terminal_topology(
    terminals,
    *,
    m4_pitch=None,
    m4_offset=0,
    unrelated_m4_spacing=None,
    require_routing_halo=False,
    m4_width=None,
    require_lower_metal_access=False,
    v3_m3_end_enclosure=None,
):
    """Reject MIM primitives whose streamed device topology is inconsistent.

    The compatibility PDK implements CAPM over the ALIGN M4 layer (official
    Sky130 met3).  M4 is the bottom electrode and reaches MINUS; CAPM is the
    top electrode and reaches PLUS through CapMIMContact and M5.  This agrees
    with the first-node/PLUS convention used by ALIGN and the terminal order
    emitted by official Magic Sky130 MIM extraction.  CAPM and
    its device contact are streamed device layers, not independent ALIGN
    routing nets.
    """

    plus_m4 = _shapes(terminals, layer="M4", net_name="PLUS")
    minus_m4 = _shapes(terminals, layer="M4", net_name="MINUS")
    device_m4 = [
        shape
        for shape in _shapes(terminals, layer="M4", net_name=None)
        if shape.get("netType") != "blockage"
    ]
    plus_m5 = _shapes(terminals, layer="M5", net_name="PLUS")
    capm = _shapes(terminals, layer="CapMIMLayer")
    contacts = _shapes(terminals, layer="CapMIMContact")
    m4_blockages = [
        shape
        for shape in _shapes(terminals, layer="M4")
        if shape.get("netType") == "blockage"
    ]

    if require_lower_metal_access:
        for net_name in ("PLUS", "MINUS"):
            m3_access = _shapes(terminals, layer="M3", net_name=net_name)
            v3_access = _shapes(terminals, layer="V3", net_name=net_name)
            m4_access = _shapes(terminals, layer="M4", net_name=net_name)
            if not m3_access or not v3_access:
                raise ValueError(
                    f"MIM capacitor {net_name} requires M3/V3 routing access"
                )
            if not any(
                _positive_area_overlap(via["rect"], lower["rect"])
                for via in v3_access
                for lower in m3_access
            ) or not any(
                _positive_area_overlap(via["rect"], upper["rect"])
                for via in v3_access
                for upper in m4_access
            ):
                raise ValueError(
                    f"MIM capacitor {net_name} M3/V3 access is disconnected"
                )
            if v3_m3_end_enclosure is not None and not any(
                lower["rect"][1]
                <= via["rect"][1] - v3_m3_end_enclosure
                and lower["rect"][3]
                >= via["rect"][3] + v3_m3_end_enclosure
                for via in v3_access
                for lower in m3_access
                if _positive_area_overlap(via["rect"], lower["rect"])
            ):
                raise ValueError(
                    f"MIM capacitor {net_name} M3/V3 end enclosure is insufficient"
                )

    if not any("pin" in shape.get("netType", "") for shape in plus_m4):
        raise ValueError("MIM capacitor requires a routable PLUS pin on M4")
    if not any("pin" in shape.get("netType", "") for shape in minus_m4):
        raise ValueError("MIM capacitor requires a routable MINUS pin on M4")
    if not plus_m5:
        raise ValueError("MIM capacitor requires a PLUS M5 top-plate strap")
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
        _positive_area_overlap(device["rect"], plus["rect"])
        for device in device_m4
        for plus in plus_m4
    ):
        raise ValueError("MIM capacitor bottom-plate geometry overlaps PLUS M4")

    if unrelated_m4_spacing is not None:
        for device in capm:
            for plus in plus_m4:
                x_gap = _axis_gap(device["rect"], plus["rect"], 0, 2)
                y_gap = _axis_gap(device["rect"], plus["rect"], 1, 3)
                if x_gap == 0 and y_gap < unrelated_m4_spacing:
                    raise ValueError(
                        "MIM capacitor CAPM clearance to unrelated PLUS M4 "
                        f"is {y_gap}, below required {unrelated_m4_spacing}"
                    )

    if require_routing_halo:
        if unrelated_m4_spacing is None:
            raise ValueError("MIM routing halo requires an unrelated-M4 spacing")
        plate_candidates = [
            shape
            for shape in device_m4
            if _contains(shape["rect"], capm[0]["rect"])
        ] if len(capm) == 1 else []
        if len(capm) != 1 or len(plate_candidates) != 1:
            raise ValueError(
                "MIM routing halo requires one CAPM and one overlapping bottom plate"
            )
        if not m4_blockages:
            raise ValueError("MIM capacitor requires routing-only M4 halo blockages")
        if m4_pitch is None or m4_width is None:
            raise ValueError("MIM routing halo requires M4 pitch and width")
        cap_rect = capm[0]["rect"]
        halo = [
            cap_rect[0] - unrelated_m4_spacing,
            cap_rect[1] - unrelated_m4_spacing,
            cap_rect[2] + unrelated_m4_spacing,
            cap_rect[3] + unrelated_m4_spacing,
        ]
        conductive_rects = [shape["rect"] for shape in device_m4 + plus_m4 + minus_m4]
        required_regions = routing_track_blockage_rects(
            halo,
            conductive_rects,
            pitch=m4_pitch,
            width=m4_width,
            offset=m4_offset,
        )
        for region in required_regions:
            if not any(
                _contains(blockage["rect"], region)
                for blockage in m4_blockages
            ):
                raise ValueError(
                    "MIM capacitor routing-only M4 halo does not cover "
                    f"required region {region}"
                )
        for blockage in m4_blockages:
            rect = blockage["rect"]
            if rect[3] - rect[1] != m4_width:
                raise ValueError("MIM capacitor M4 blockage has nonstandard width")
            if ((rect[1] + rect[3]) // 2 - m4_offset) % m4_pitch:
                raise ValueError("MIM capacitor M4 blockage is off grid")

        boundaries = _shapes(terminals, layer="Boundary")
        if len(boundaries) != 1 or not _contains(boundaries[0]["rect"], halo):
            raise ValueError("MIM capacitor boundary does not contain its routing halo")

    minus_component = _connected_component(minus_m4, minus_m4 + device_m4)
    if not any(shape in minus_component for shape in device_m4):
        raise ValueError("MIM capacitor MINUS pin does not reach bottom-plate geometry")
    if not any(
        shape in minus_component
        and _positive_area_overlap(shape["rect"], device["rect"])
        for shape in device_m4
        for device in capm
    ):
        raise ValueError("MIM capacitor MINUS access chain does not reach the CAPM overlap")

    for contact in contacts:
        if not any(
            _positive_area_overlap(contact["rect"], device["rect"])
            for device in capm
        ):
            raise ValueError("MIM contact does not overlap CAPM")
        if not any(
            _positive_area_overlap(contact["rect"], strap["rect"])
            for strap in plus_m5
        ):
            raise ValueError("MIM contact does not overlap the PLUS M5 strap")
