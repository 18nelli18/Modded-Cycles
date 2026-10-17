"""Note 112 : comparer deux noyaux sur l'EMAC natif patche de DigiEmu.

Installer son runtime Unicorn patche, puis fournir --digiemu (sources),
--baseline et --candidate (donnees generees). Pas de modele EMAC Python.
Cette preuve ne simule ni les interruptions audio ni les caches physiques.
"""
import argparse
import json
import pathlib
import random
import struct
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--digiemu', required=True)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--cases', type=int, default=512)
    parser.add_argument('--dirty-extensions',action='store_true')
    parser.add_argument('--instructions',action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(pathlib.Path(args.digiemu).resolve()))
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, m68k_const as mk
    from emu.unicorn_compat import evaluate

    def cpu():
        machine = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        machine.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        return machine

    assert evaluate(factory=cpu)['compatible'], 'runtime Unicorn non compatible'
    root = pathlib.Path(__file__).resolve().parents[2]
    symbols = json.loads((root / 'firmware/wizard-catalogue.json').read_text(
        encoding='utf-8'))['variants']['0']['wizard']['symbols']
    symbols = {key: int(value, 16) for key, value in symbols.items()}
    kernels = [];counts=[0,0];totals={False:[0,0],True:[0,0]}
    stack, stop, buffer, setup = 0x93008000, 0x9300f000, 0x93070000, 0x9300c000
    for path in (args.baseline, args.candidate):
        data = json.loads(pathlib.Path(path).read_text(encoding='utf-8').split(
            '=', 1)[1].strip().rstrip(';'))
        machine = cpu()
        machine.mem_map(0x40000000, 0x02400000)
        machine.mem_map(0x93000000, 0x100000)
        machine.mem_write(data['at'], bytes.fromhex(data['hex']))
        machine.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        if args.instructions:
            index=len(kernels)
            def counter(uc,pc,size,user):counts[user]+=1
            machine.hook_add(UC_HOOK_CODE,counter,user_data=index,begin=data['at'],end=data['at']+data['code_size']-1)
        kernels.append((machine, data['at'],data.get('mode_address')))

    def call(machine, address, *params):
        machine.mem_write(stack, struct.pack('>' + 'I' * (1 + len(params)),
                                           stop, *params))
        machine.reg_write(mk.UC_M68K_REG_A7, stack)
        machine.emu_start(address, stop, count=100000)
        assert machine.reg_read(mk.UC_M68K_REG_PC) == stop

    random_source = random.Random(126)
    for case in range(args.cases):
        lane = case % 6
        coefficient = (4095, 3538, 2048, 64, 1)[case % 5]
        resonance = 0 if case % 2 == 0 else 4096
        incoming = (0xa0, 0xb0, 0x80, 0x20, 0xfa0)[case % 5]
        states = [random_source.randrange(-(1 << 27), 1 << 27) for _ in range(4)]
        samples = [random_source.randrange(-0x70000000, 0x70000000)
                   for _ in range(32)]
        results = []
        for index,(machine, entry, probe) in enumerate(kernels):
            if args.dirty_extensions and index==1:
                machine.mem_write(setup+0x100,bytes.fromhex("a93c000000b0203c12345678a10070ffab00af004e75"))
                call(machine,setup+0x100)
            for key, value in (('gflt_f', coefficient), ('gflt_q', resonance),
                               ('gflt_mk', 4096)):
                machine.mem_write(symbols[key] + lane * 4, struct.pack('>I', value))
            for pole, value in enumerate(states):
                machine.mem_write(symbols['gflt_y1'] + 28 * pole + lane * 4,
                                  struct.pack('>i', value))
            # MOVE.L #mode,D0 ; MOVE.L D0,MACSR ; RTS, execute par le runtime.
            machine.mem_write(setup, bytes.fromhex('203c') + struct.pack(
                '>I', incoming) + bytes.fromhex('a900a9804e75'))
            call(machine, setup)
            actual_mode=machine.reg_read(mk.UC_M68K_REG_D0)
            machine.mem_write(buffer, struct.pack('>32i', *samples))
            counts[index]=0
            call(machine, entry, buffer, lane)
            totals[bool(resonance)][index]+=counts[index]
            if probe:assert struct.unpack('>I',bytes(machine.mem_read(probe+lane*4,4)))[0]==actual_mode,(case,lane,'capture MACSR')
            results.append((bytes(machine.mem_read(buffer, 128)), tuple(
                bytes(machine.mem_read(symbols['gflt_y1'] + 28 * pole + lane * 4, 4))
                for pole in range(4))))
        assert results[0] == results[1], (case, lane, coefficient, resonance, incoming)
    print('PASS EMAC natif DigiEmu :', args.cases,
          'blocs, six pistes, modes entrants et samples/etats exacts')
    if args.instructions:
        for resonance,values in totals.items():print('INSTRUCTIONS noyau resonance',int(resonance),values)
    print('LIMITES : noyau seul ; pas de deadline, cache ou validation hardware')


if __name__ == '__main__':
    main()
