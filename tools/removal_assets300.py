"""Compacter les plages effacees sans deplacer les adresses natives."""
from mtlib import aplib


def compact_zero_runs(section):
    data, ops = aplib.depack(section)
    writer = aplib._Writer()
    last = 1
    index = 0
    while index < len(ops):
        kind, pos, off, size = ops[index]
        if data[pos:pos + size] == bytes(size):
            end = pos + size
            index += 1
            while index < len(ops):
                _, next_pos, _, next_size = ops[index]
                if next_pos != end or data[next_pos:next_pos + next_size] != bytes(next_size):
                    break
                end += next_size
                index += 1
            if pos == 0 or data[pos - 1] != 0:
                writer.literal(0)
                pos += 1
            remaining = end - pos
            if remaining >= 2:
                writer.match(1, remaining, last)
                last = 1
            elif remaining:
                writer.literal(0)
            continue
        if kind == aplib.LITERAL:
            writer.literal(data[pos])
        else:
            writer.match(off, size, last)
            last = off
        index += 1
    writer.end()
    writer.o[:4] = (len(writer.o) - 8).to_bytes(4, 'big')
    writer.o[4:8] = (sum(writer.o[8:]) & 0xffffffff).to_bytes(4, 'big')
    result = bytes(writer.o)
    assert aplib.depack(result)[0] == data
    return result
