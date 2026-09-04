import math
from align.primitive.default.canvas import DefaultCanvas
from align.cell_fabric.generators import *
from align.cell_fabric.grid import *

from .cap_contract import (
    highest_grid_track_with_positive_overlap,
    horizontal_pin_placement_grid_constraint,
    routing_track_blockage_rects,
    validate_cap_terminal_topology,
)

import logging
logger = logging.getLogger(__name__)

class CapGenerator(DefaultCanvas):

    def __init__(self, pdk):
        super().__init__(pdk)

        # The generated capacitor's PLUS and MINUS access pins lie on M4.
        # ALIGN's ordinary placement lattice is finer than the M4 routing
        # lattice, so a legal primitive can otherwise be translated until both
        # pins become inaccessible to the router.  Propagate the native ALIGN
        # placement-grid contract through hierarchy instead of compensating in
        # a circuit-specific netlist or after streamout.
        self.metadata = getattr(self, "metadata", {})
        self.metadata["constraints"] = [
            horizontal_pin_placement_grid_constraint(
                pitch=self.pdk["M4"]["Pitch"],
                routing_offset=self.pdk["M4"]["Offset"],
            )
        ]
 
        self.m3n = self.addGen( Wire( 'm3n', 'CapMIMLayer', 'v',
                                     clg=UncoloredCenterLineGrid( pitch=self.pdk['M3']['Pitch'], width=self.pdk['M3']['Width']),
                                     spg=EnclosureGrid(pitch=self.pdk['M2']['Pitch'], stoppoint=self.pdk['V2']['VencA_H'] + self.pdk['M2']['Width']//2, check=False)))
        
        self.m5_offset = self.pdk['CapMIMLayer']['Enclosure'] + self.pdk['CapMIMContact']['Enclosure'] + self.pdk['CapMIMContact']['WidthX']//2
        self.m5n = self.addGen(Wire( 'm5n', 'M5', 'v',
                                     clg=UncoloredCenterLineGrid( pitch=2*self.pdk['Cap']['m5Width'], width=self.pdk['Cap']['m5Width'], offset=self.m5_offset),
                                     spg=EnclosureGrid(pitch=self.pdk['M4']['Pitch']//2, stoppoint=self.pdk['CapMIMContact']['Enclosure'], offset=0, check=False)))

        self.Cboundary = self.addGen( Region( 'Cboundary', 'Cboundary', h_grid=self.m2.clg, v_grid=self.m1.clg))


        clg_mim = UncoloredCenterLineGrid( pitch=2, width=2)

        self.CapMIMC = self.addGen( Region( 'CapMIMC', 'CapMIMContact', h_grid=clg_mim, v_grid=clg_mim))

        self.v4_x = self.addGen( Via( 'v4_x', 'V4',
                                        h_clg=self.m4.clg, v_clg=self.m5n.clg,
                                        WidthX=self.v4.WidthX, WidthY=self.v4.WidthY,
                                        h_ext=self.v4.h_ext, v_ext=self.v4.v_ext))

    def addCap( self, length, width):
        x_length = int(length)
        y_length = int(width)

        m1_p = self.pdk['M1']['Pitch']
        m2_p = self.pdk['M2']['Pitch']

        m4n_xwidth = x_length + 2*self.pdk['CapMIMLayer']['Enclosure']
        required_unrelated_m4_clearance = (
            self.pdk['CapMIMLayer']['UnrelatedMetalSpacing']
            + self.pdk['Cap']['unrelatedMetalMargin']
        )
        native_unrelated_m4_clearance = (
            self.pdk['M4']['Pitch'] - self.pdk['M4']['Width']//2
        )
        mim_y_offset = (
            required_unrelated_m4_clearance - native_unrelated_m4_clearance
        )
        if mim_y_offset < 0 or mim_y_offset % 2:
            raise ValueError(
                "MIM capacitor clearance offset must be a nonnegative even value"
            )
        # The broad M4 rectangle is the physical bottom plate.  Its center is
        # determined by device dimensions rather than the routing grid, so it
        # must remain device geometry rather than a block pin.
        m4n = Wire( 'm4n', 'M4', 'v',
                                     clg=UncoloredCenterLineGrid( pitch=2*m4n_xwidth, width=m4n_xwidth, offset=m4n_xwidth//2),
                                     spg=EnclosureGrid(pitch=y_length, stoppoint=self.pdk['CapMIMLayer']['Enclosure'], offset=mim_y_offset, check=False))
        mimcap = Wire( 'mim', 'CapMIMLayer', 'v',
                                     clg=UncoloredCenterLineGrid( pitch=2*x_length, width=x_length, offset=x_length//2+self.pdk['CapMIMLayer']['Enclosure']),
                                     spg=EnclosureGrid(pitch=y_length, stoppoint=0, offset=mim_y_offset, check=False))


        x_number = math.ceil(m4n_xwidth/m1_p)
        # Put the MINUS access on the highest legal M4 track that still has
        # positive-area overlap with the dimension-derived bottom plate.  The
        # previous ceil expression selected the first track *above* the plate
        # for the minimum legal 1-um-square CAPM, leaving a physical open.
        bottom_plate_top = (
            mim_y_offset + y_length + self.pdk['CapMIMLayer']['Enclosure']
        )
        y_number_m4 = highest_grid_track_with_positive_overlap(
            bottom_plate_top,
            pitch=self.pdk['M4']['Pitch'],
            width=self.pdk['M4']['Width'],
            offset=self.pdk['M4']['Offset'],
        )
        if y_number_m4 <= -1:
            raise ValueError("MIM capacitor cannot separate PLUS and MINUS access tracks")
        y_number = math.ceil((y_number_m4*self.pdk['M4']['Pitch'])/m2_p)

        logger.debug( f"Number of wires {x_number} {y_number}")

        # A Sky130 CAPM-over-M4 capacitor has distinct bottom-plate and
        # top-plate conductors.  Keep the dimension-derived plate unnamed in
        # ALIGN's routing model; the explicit contract below proves its
        # physical overlap with the grid-aligned MINUS pin.
        self.addWire( m4n, None, 0, (0, -1), (1, 1))
        # CAPM is a device-definition layer, not an ALIGN routing conductor.
        # Its electrical association is established physically by the
        # CapMIMContact shape into the PLUS M5 access strap.  Giving CAPM a
        # routing net name creates a false open because the contact is a
        # streamed device region rather than an ALIGN routing-stack via.
        self.addWire( mimcap, None, 0, (0, -1), (1, 1))
        self.addWire( self.m5n, 'PLUS', 0, (-3, 1), (2, 1))
        self.addVia( self.v4_x, 'PLUS', 0, -1)
        gridx0= (self.m5_offset - self.pdk['CapMIMContact']['WidthX']//2)//2
        gridx1= gridx0 + self.pdk['CapMIMContact']['WidthX']//2
        contact_y_offset = mim_y_offset//2
        self.addRegion(
            self.CapMIMC,
            None,
            gridx0,
            150 + contact_y_offset,
            gridx1,
            250 + contact_y_offset,
        )
        gridx2 = math.floor(m4n_xwidth/self.pdk['M3']['Pitch'])
        # ALIGN binds the first two-terminal capacitor node to PLUS.  Magic's
        # official Sky130 MIM extraction presents the CAPM top plate first, so
        # PLUS must reach CAPM and MINUS must reach the broad M4 bottom plate.
        self.addWire( self.m4, 'MINUS', y_number_m4, (-1, -1), (gridx2, 1), netType = 'pin')
        self.addWire( self.m4, 'PLUS', -1, (-1, -1), (gridx2, 1), netType = 'pin')

        # Give both terminals an explicit M3/V3 access point.  M4 is
        # horizontal, so a routing halo on that layer must not be the only
        # possible entrance to the terminal.  Track 2 lies outside the CAPM
        # device rectangle for the minimum legal capacitor while remaining
        # inside both wide M4 pins.
        access_x_track = 2
        plus_m4_track = -1
        plus_m3_stop = (
            plus_m4_track * self.pdk['M4']['Pitch'] // self.pdk['M2']['Pitch']
        )
        minus_m3_stop = (
            y_number_m4 * self.pdk['M4']['Pitch'] // self.pdk['M2']['Pitch']
        )
        self.addWire(
            self.m3, 'PLUS', access_x_track,
            (plus_m3_stop - 1, -1), (plus_m3_stop + 1, 1), netType='pin'
        )
        self.addVia(self.v3, 'PLUS', access_x_track, plus_m4_track)
        self.addWire(
            self.m3, 'MINUS', access_x_track,
            (minus_m3_stop - 1, -1), (minus_m3_stop + 1, 1), netType='pin'
        )
        self.addVia(self.v3, 'MINUS', access_x_track, y_number_m4)
 
        self.addRegion( self.boundary, 'Boundary', -2, -6,
                        x_number+1,
                        y_number+3)

        # CAPM requires substantially more clearance to unrelated M4
        # (official Sky130 metal3) than the ordinary M4 routing rule.  Encode
        # that physical contract as routing-only M4 obstructions.  The
        # obstructions are consumed by LEF/routing and must not be emitted as
        # physical GDS geometry.
        clearance = required_unrelated_m4_clearance
        capm = next(t for t in self.terminals if t["layer"] == "CapMIMLayer")
        bottom_plate = next(
            t
            for t in self.terminals
            if t["layer"] == "M4"
            and t.get("netName") is None
            and t.get("netType") != "blockage"
            and t["rect"][0] <= capm["rect"][0]
            and t["rect"][1] <= capm["rect"][1]
            and t["rect"][2] >= capm["rect"][2]
            and t["rect"][3] >= capm["rect"][3]
        )
        boundary = next(t for t in self.terminals if t["layer"] == "Boundary")

        # Shift by whole placement-grid pitches so the CAPM halo stays inside
        # the primitive boundary on every side without disturbing pin grids.
        device_terminals = [
            terminal
            for terminal in self.terminals
            if terminal["layer"] != "Boundary"
        ]
        min_x = min(terminal["rect"][0] for terminal in device_terminals)
        min_y = min(terminal["rect"][1] for terminal in device_terminals)
        shift_x_need = max(clearance - capm["rect"][0], -min_x, 0)
        shift_y_need = max(clearance - capm["rect"][1], -min_y, 0)
        shift_x = math.ceil(shift_x_need / m1_p) * m1_p
        # M4 pins are horizontal, so vertical translation must preserve both
        # the M4 routing grid and the M2 placement grid.  In this PDK the M4
        # pitch is an integer multiple of the M2 pitch.
        m4_pitch = self.pdk['M4']['Pitch']
        if m4_pitch % m2_p:
            raise ValueError("MIM capacitor M4 pitch must align to the M2 grid")
        shift_y = math.ceil(shift_y_need / m4_pitch) * m4_pitch
        if shift_x or shift_y:
            for terminal in self.terminals:
                terminal["rect"] = [
                    terminal["rect"][0] + shift_x,
                    terminal["rect"][1] + shift_y,
                    terminal["rect"][2] + shift_x,
                    terminal["rect"][3] + shift_y,
                ]

        capm_rect = capm["rect"]
        plate_rect = bottom_plate["rect"]
        halo = [
            capm_rect[0] - clearance,
            capm_rect[1] - clearance,
            capm_rect[2] + clearance,
            capm_rect[3] + clearance,
        ]
        conductive_m4_rects = [
            terminal["rect"]
            for terminal in self.terminals
            if terminal["layer"] == "M4"
            and terminal.get("netType") != "blockage"
        ]
        blockage_rects = routing_track_blockage_rects(
            halo,
            conductive_m4_rects,
            pitch=self.pdk['M4']['Pitch'],
            width=self.pdk['M4']['Width'],
            offset=self.pdk['M4']['Offset'],
        )
        for rect in blockage_rects:
            if rect[0] < rect[2] and rect[1] < rect[3]:
                self.transform_and_add(
                    {
                        "layer": "M4",
                        "netName": None,
                        "netType": "blockage",
                        "rect": rect,
                    }
                )

        boundary_width = math.ceil(
            max(boundary["rect"][2], halo[2]) / m1_p
        ) * m1_p
        boundary_height = math.ceil(
            max(boundary["rect"][3], halo[3]) / m2_p
        ) * m2_p
        boundary["rect"] = [0, 0, boundary_width, boundary_height]

        validate_cap_terminal_topology(
            self.terminals,
            m4_pitch=self.pdk['M4']['Pitch'],
            m4_offset=self.pdk['M4']['Offset'],
            unrelated_m4_spacing=required_unrelated_m4_clearance,
            require_routing_halo=True,
            m4_width=self.pdk['M4']['Width'],
            require_lower_metal_access=True,
            v3_m3_end_enclosure=self.pdk['V3']['VencA_L'],
        )

        #self.addRegion( self.Cboundary, 'Cboundary', None,
        #                    -1, -1,
        #                    last_x_track  + x * grid_cell_x_pitch + 1 + p,
        #                    last_y1_track + y * grid_cell_y_pitch + 1)

        logger.debug( f"Computed Boundary: {self.terminals[-1]} {self.terminals[-1]['rect'][2]} {self.terminals[-1]['rect'][2]%80}")
