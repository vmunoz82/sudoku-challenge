# Disable pylint's "your name is too short" warning.
# pylint: disable=C0103
from typing import List, Tuple

from amaranth import Signal, Module, Elaboratable
from amaranth.build import Platform
from amaranth.asserts import Assume, Assert, Cover
from amaranth.sim import Simulator, Passive, Delay, Settle

from util import main

# one-hot decoder, 9 bits, starting from 1, not 0
def decoder(m, s, n):
    with m.Switch(n):
        for i in range(1, 10):
            with m.Case(i):
                m.d.comb += s.eq(1 << (i - 1))
        with m.Default():
            m.d.comb += s.eq(0)  # If no case matches


class Sudoku(Elaboratable):
    def __init__(self):
        # Auxs
        self.idxs = []
        self.inputs = []

        # Inputs
        for x in "ABCDEFGHI":
            for y in "123456789":
                self.__dict__[x + y] = Signal(range(1, 10), name=x + y)
                self.__dict__["d" + x + y] = Signal(9, name="d" + x + y)
                self.idxs.append(x + y)
                self.inputs.append(self.__dict__[x + y])

        # Outputs
        self.rows = Signal()  # are the 9 rows correct?
        self.cols = Signal()  # are the 9 cols correct?
        self.zones = Signal()  # are the 9 zones correct?
        self.sudoku = Signal()  # are the rows, cols and zones correct?

    def elaborate(self, _: Platform) -> Module:
        m = Module()

        # one one-hot decoder from each cell
        for i, v in enumerate(self.idxs):
            decoder(m, self.__dict__["d" + v], self.__dict__[v])

        # rows, cols and zones definitions
        grid = (
            ("rA", ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")),
            ("rB", ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9")),
            ("rC", ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9")),
            ("rD", ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9")),
            ("rE", ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9")),
            ("rF", ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9")),
            ("rG", ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9")),
            ("rH", ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9")),
            ("rI", ("I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9")),
            ("c1", ("A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1", "I1")),
            ("c2", ("A2", "B2", "C2", "D2", "E2", "F2", "G2", "H2", "I2")),
            ("c3", ("A3", "B3", "C3", "D3", "E3", "F3", "G3", "H3", "I3")),
            ("c4", ("A4", "B4", "C4", "D4", "E4", "F4", "G4", "H4", "I4")),
            ("c5", ("A5", "B5", "C5", "D5", "E5", "F5", "G5", "H5", "I5")),
            ("c6", ("A6", "B6", "C6", "D6", "E6", "F6", "G6", "H6", "I6")),
            ("c7", ("A7", "B7", "C7", "D7", "E7", "F7", "G7", "H7", "I7")),
            ("c8", ("A8", "B8", "C8", "D8", "E8", "F8", "G8", "H8", "I8")),
            ("c9", ("A9", "B9", "C9", "D9", "E9", "F9", "G9", "H9", "I9")),
            ("z1", ("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3")),
            ("z2", ("A4", "A5", "A6", "B4", "B5", "B6", "C4", "C5", "C6")),
            ("z3", ("A7", "A8", "A9", "B7", "B8", "B9", "C7", "C8", "C9")),
            ("z4", ("D1", "D2", "D3", "E1", "E2", "E3", "F1", "F2", "F3")),
            ("z5", ("D4", "D5", "D6", "E4", "E5", "E6", "F4", "F5", "F6")),
            ("z6", ("D7", "D8", "D9", "E7", "E8", "E9", "F7", "F8", "F9")),
            ("z7", ("G1", "G2", "G3", "H1", "H2", "H3", "I1", "I2", "I3")),
            ("z8", ("G4", "G5", "G6", "H4", "H5", "H6", "I4", "I5", "I6")),
            ("z9", ("G7", "G8", "G9", "H7", "H8", "H9", "I7", "I8", "I9")),
        )

        for v in grid:
            name = v[0]
            cells = v[1]
            cond = self.__dict__["d" + cells[0]]
            for c in cells[1:]:
                cond |= self.__dict__["d" + c]
            self.__dict__[name] = Signal(9, name=name)
            # print("cond"+name, cond)
            m.d.comb += self.__dict__[name].eq(cond)

        m.d.comb += self.rows.eq(
            (self.rA == 0b111_111_111) & (self.rB == 0b111_111_111) & (self.rC == 0b111_111_111)
            & (self.rD == 0b111_111_111) & (self.rE == 0b111_111_111) & (self.rF == 0b111_111_111)
            & (self.rG == 0b111_111_111) & (self.rH == 0b111_111_111) & (self.rI == 0b111_111_111)
        )

        m.d.comb += self.cols.eq(
            (self.c1 == 0b111_111_111) & (self.c2 == 0b111_111_111) & (self.c3 == 0b111_111_111)
            & (self.c4 == 0b111_111_111) & (self.c5 == 0b111_111_111) & (self.c6 == 0b111_111_111)
            & (self.c7 == 0b111_111_111) & (self.c8 == 0b111_111_111) & (self.c9 == 0b111_111_111)
        )

        m.d.comb += self.zones.eq(
            (self.z1 == 0b111_111_111) & (self.z2 == 0b111_111_111) & (self.z3 == 0b111_111_111)
            & (self.z4 == 0b111_111_111) & (self.z5 == 0b111_111_111) & (self.z6 == 0b111_111_111)
            & (self.z7 == 0b111_111_111) & (self.z8 == 0b111_111_111) & (self.z9 == 0b111_111_111)
        )

        m.d.comb += self.sudoku.eq(self.cols & self.rows & self.zones)

        return m

    @classmethod
    def formal(cls, userdata=None) -> Tuple[Module, List[Signal]]:
        m = Module()
        m.submodules.s = s = cls()

        for i, v in enumerate(s.idxs):
            if userdata[i] >= 1 and userdata[i] <= 9:
                m.d.comb += Assume(s.__dict__[v] == userdata[i])

        m.d.comb += Cover(s.sudoku)

        return m, s.inputs

    @classmethod
    def sim(cls, userdata=None):
        s = cls()
        sim = Simulator(s)

        def process():
            yield Delay(1e-9)
            for i, v in enumerate(s.idxs):
                if userdata[i] >= 1 and userdata[i] <= 9:
                    yield s.__dict__[v].eq(userdata[i])
            yield Settle()
            yield Delay(1e-9)

        sim.add_process(process)
        with sim.write_vcd("sudoku.vcd", "sudoku.gtkw"):
            sim.run()

import sys, re

import amaranth.cli

if __name__ == "__main__" and len(sys.argv)>2:
    if sys.argv[1] == "sim" or sys.argv[1] == "gen":
        sudoku = list(
            map(int, re.sub("[^1-9]", "0", re.sub("\n|\r|\t| |\||-|\+", "", sys.argv[2])))
        )
    main(Sudoku, filename="sudoku.il", userdata=sudoku)
