"""Preuves des P-locks HARMONY via les routines natives OS 1.13 (notes/40).

Le banc contrôle seulement sélection UI, horloge et observateurs. Les buffers,
setters de trigs/locks, copier, sauvegarde complète/partielle et chargeur sont
ceux du firmware, exécutés aux adresses finales du JSON. Aucun dump exporté.
"""
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

from probe_chord_storage import Rig, BASE, B1, B2, SERIAL, PROJECT, require

UI, CLOCK = 0x92040000, 0x92041000
PLOCK_HOOKS = ((0x4005B9C6, 8), (0x4005BAD2, 6), (0x4005AA1A, 8), (0x40012274, 6), (0x4005B816, 2))
SLOT = 28


class PlockRig(Rig):
    def __init__(self, stock, patched, symbols):
        self.handlers = {}
        super().__init__(stock, patched, symbols)
        self.patched(True)
        self.stock_image, self.patched_image = stock, patched
        self.machine = 5
        self.stub(0x400CF9A8, lambda args: UI)
        self.stub(0x400CFD0E, lambda args: CLOCK)
        self.stub(0x4001E318, lambda args: self.machine)
        self.stub(0x400CF866, lambda args: PROJECT)
        self.stub(0x4000EB90, lambda args: PROJECT + 48)
        self.stub(0x40012412, lambda args: 0)
        self.stub(0x4007FAF4, lambda args: 0)
        self.uc.mem_map(0x80000000, 0x20000)
        self.bind(B1)

    def stub(self, address, handler):
        if address in self.handlers:
            self.handlers[address] = handler
            return
        self.handlers[address] = handler

        def hook(uc, pc, size, user):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
            uc.reg_write(mk.UC_M68K_REG_D0, self.handlers[address](args) & 0xFFFFFFFF)
            uc.reg_write(mk.UC_M68K_REG_PC, self.word(sp))
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        self.uc.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)

    def parameter_hooks(self, enabled):
        source = self.patched_image if enabled else self.stock_image
        for address, length in PLOCK_HOOKS:
            self.uc.mem_write(address, source[address - BASE:address - BASE + length])
        self.uc.ctl_flush_tb()

    def bind(self, raw, initialize=True):
        if initialize:
            self.call(0x400615E8, raw, 0)
        obj = PROJECT + 5192
        self.obj, self.raw, self.plock = obj, raw, obj + 640
        self.word(0x40FE4228, PROJECT)
        self.word(PROJECT + 48, 0x400FD8C0)
        self.word(0x40A7887C, raw)
        self.word(raw + 30706, 0)
        self.uc.mem_write(obj, bytes(732))
        for offset, table in ((0, 0x400FDA54), (44, 0x400FD8C0), (640, 0x400FDDF4)):
            self.word(obj + offset, table)
        for track in range(6):
            base = self.track(track)
            self.word(base, 0x400FF894)
            self.word(base + 44, self.plock)
            self.word(base + 56, track)
            self.word(base + 60, obj)
            queue = PROJECT + 83148 + 40 * track
            self.word(queue + 24, 0x92050000 + 0x1000 * track)
            self.word(queue + 32, 0x92050800 + 0x1000 * track)
        self.call(0x4000C5D0, obj, raw)
        self.call(0x4000C9C4, obj + 44, 64)
        for track in range(6):
            self.word(raw + 30682 + 4 * track, 0x80000000 | (48 << 21))

    def track(self, track):
        return PROJECT + 5192 + 112 + 88 * track

    def get(self, track, step, slot=SLOT):
        value = self.call(0x4000DA2A, self.plock, track, step, slot)
        return value - 2**32 if value >= 2**31 else value

    def set(self, track, step, slot, value):
        require(self.call(0x4000DECE, self.plock, track, step, slot, value) & 0xFF,
                "Le setter natif refuse le lock")

    def live(self, enabled, step=0, track=0):
        self.word(0x40A78874, int(enabled))
        self.word(0x40A7883C, 0)
        self.uc.mem_write(UI + 359, bytes([int(enabled)]))
        self.word(CLOCK + 0x48 + 4 * track, step)

    def pad(self, number, down):
        event = 0x92042000
        self.uc.mem_write(event, b"\xa5" * 32)
        self.call(0x40074072, event, number, int(down), 100, 123, 0)
        require(self.call("ck_ui_pad", 0, event) & 255, "Pad valide non consommé")


def _observer_checks(stock, patched, symbols):
    """L'événement réel alimente le miroir sérialisé, y compris sa suppression.

    La liste d'observateurs reste contrôlée par le banc : on conserve les douze
    octets émis par le setter, puis on les remet au callback natif après retour.
    Le dynamic_cast, le writer partiel et son repli complet restent exécutés.
    """
    rig = PlockRig(stock, patched, symbols)
    rig.call(0x4005BA0A, SERIAL, B1, 0)
    events = []

    def notify(args):
        if args[1] and rig.word(args[1]) == 0x400FDB0C:
            events.append(rig.bytes(args[1], 12))
        return 0

    rig.handlers[0x400D0F6C] = notify

    def mirror(track, slot):
        require(len(events) == 1, "Setter sans événement P-lock unique")
        require(struct.unpack(">II", events[0][4:]) == (slot, track),
                "Événement P-lock annonce un autre slot ou une autre piste")
        rig.uc.mem_write(0x92045000, events[0])
        rig.call(0x4000E0BE, rig.plock, SERIAL + 4336, 0x92045000)
        events.clear()

    def roundtrip():
        expected = rig.bytes(B1 + 4332, 26310)
        rig.call(0x4005B894, B2, SERIAL, 0)
        require(rig.bytes(B2 + 4332, 26310) == expected,
                "Le miroir observateur perd HARMONY ou altère un lock natif")

    for track in range(6):
        for slot in (0, 11, 12, 22, SLOT):
            for step in (0, 7, 31, 32, 63):
                value = (step + track) % 7 if slot == SLOT else 5000 + step
                rig.set(track, step, slot, value)
                mirror(track, slot)
    roundtrip()
    # Le dernier effacement d'une lane déclenche le repli natif vers le writer
    # complet. Les autres lanes, dont COLOR fractionnaire, doivent survivre.
    for track in range(6):
        for step in (0, 7, 31, 32, 63):
            rig.call(0x4000DCEC, rig.plock, track, step, SLOT)
            mirror(track, SLOT)
    roundtrip()
    print("ok P-lock : 180 événements réels, observateur miroir natif, ajout et suppression HARMONY sans altérer les autres locks", flush=True)


def _attack_recording_checks(stock, patched, symbols):
    """Vrais gestes et relais, puis recorder natif à la frontière de transport.

    Les appels de sortie sont collectés puis remis au recorder avec un pas
    choisi par le banc ; l'horloge et la file inter-tâches ne sont pas émulées.
    """
    rig = PlockRig(stock, patched, symbols)
    view, notes, event = 0x92060000, 0x92061000, 0x92062000
    reference = PlockRig(stock, patched, symbols)
    reference.parameter_hooks(False)
    for offset, pointer in ((148, notes), (152, notes), (156, notes + 0xa00)):
        rig.word(view + offset, pointer)
    held, events = set(), []
    rig.stub(0x4007FAF4, lambda args: int(args[0] in held))
    rig.stub(0x40015AC4, lambda args: 97)
    rig.stub(0x40075F3C, lambda args: 0)
    rig.stub(0x40016E90, lambda args: 0)

    def capture(kind, count):
        def handler(args):
            events.append((kind, args[:count]))
            return 0
        return handler

    rig.stub(0x4008171E, capture("on", 7))
    rig.stub(0x4008145E, capture("off", 3))

    def record(step):
        for kind, args in events:
            if kind == "on":
                rig.call(0x40012158, PROJECT, args[0], args[1], args[2], 0,
                         step, 0, 0, 0xFFFFFFFF)

    held.add(16)
    rig.live(True, 0)
    rig.call(0x4007238C, event, 16, 1, 123, 127)
    rig.call("ck_ui_key", view, event)
    record(0)
    require(len(events) == 1 and events[0][0] == "on", "TRIG initial sans note")
    for step, pad, down, modifier in ((1, 1, True, 1), (2, 4, True, 4),
                                      (3, 4, False, -1), (4, 1, False, -1)):
        rig.live(True, step)
        # Une nouvelle note suit le remplacement de locks stock ; le geste
        # de relâchement, sans note ni lock HARMONY, laisse le pas intact.
        for candidate in (rig, reference):
            candidate.call(0x40017BB0, candidate.track(0), step, 1)
            candidate.set(0, step, 11, 32 * 256 + 173)
            candidate.set(0, step, 12, 7 * 256 + 19)
        events.clear()
        rig.pad(pad, down)
        require([kind for kind, _ in events] == (["off", "on"] if down else []),
                "L'attaque ou le relâchement de pad émet des notes inattendues")
        record(step)
        if down:
            reference.call(0x40012158, PROJECT, 0, 48, 97, 0, step, 0, 0, 0xFFFFFFFF)
        require(bool(rig.call(0x40015C20, rig.track(0), step) & 255) == down,
                "L'attaque enregistrée n'est pas un trig, ou le relâchement en crée un")
        require(rig.get(0, step) == modifier and all(
                    rig.get(0, step, slot) == reference.get(0, step, slot) for slot in (11, 12)),
                f"Recorder pas {step}: HARMONY/COLOR/SHAPE = "
                f"{[rig.get(0, step, slot) for slot in (SLOT, 11, 12)]}")
    # Après le relâchement des pads, un nouveau TRIG repart de son extension.
    events.clear()
    rig.call(0x4007238C, event, 16, 1, 123, 127)
    rig.call("ck_ui_key", view, event)
    record(5)
    require(rig.get(0, 5) == 0, "Nouveau TRIG conserve le dernier pad dans sa prise")
    held.remove(16)
    rig.call(0x4007238C, event, 16, 0, 123, 127)
    rig.call("ck_ui_key", view, event)
    events.clear()
    rig.live(True, 6)
    before = rig.bytes(rig.raw, 30720)
    rig.pad(6, True)
    require(not events and rig.bytes(rig.raw, 30720) == before,
            "Préparation sans TRIG modifie la prise ou crée une note")
    held.add(16)
    rig.call(0x4007238C, event, 16, 1, 123, 127)
    rig.call("ck_ui_key", view, event)
    record(7)
    require(rig.get(0, 7) == 6, "Prochain TRIG perd son pad préparé dans le recorder")
    for step in (8, 9):
        events.clear()
        rig.call(0x4007238C, event, 16, 1, 123, 127)
        rig.call("ck_ui_key", view, event)
        record(step)
        require([kind for kind, _ in events] == ["off", "on"] and rig.get(0, step) == 6,
                f"T tenu perd sa transformation sur l'attaque enregistrée au pas {step}")
    events.clear()
    rig.pad(6, False)
    require(not events and rig.get(0, 6) == -1, "Relâchement de préparation écrit un retour")
    rig.call(0x4007238C, event, 16, 1, 123, 127)
    rig.call("ck_ui_key", view, event)
    record(10)
    require(rig.get(0, 10) == 0, "Le premier TRIG après relâchement garde la transformation")
    rig.call(0x4005BA0A, SERIAL, B1, 0)
    rig.call(0x4005B894, B2, SERIAL, 0)
    rig.bind(B2, initialize=False)
    require([bool(rig.call(0x40015C20, rig.track(0), s) & 255) for s in range(5)]
            == [True, True, True, False, False], "Save/load perd les attaques enregistrées")
    require([rig.get(0, s) for s in range(11)] == [0, 1, 4, -1, -1, 0, -1, 6, 6, 6, 0],
            "Save/load perd les attaques ou ajoute un retour au relâchement")
    print("ok attaques T→recorder : préparation sans lock, chaque TRIG avec HARMONY tant que T est tenu, retour EXT et save/load conservés", flush=True)


def run_plock_checks(stock, patched, symbols):
    rig = PlockRig(stock, patched, symbols)
    # Toutes les valeurs stock restent identiques, y compris les entrées
    # rejetées ; le seul nouvel identifiant est 33 pour les six pistes audio.
    rig.parameter_hooks(False)
    baseline = {(track, slot): rig.call(0x4005AA1A, track, slot)
                for track in range(8) for slot in range(36)}
    rig.parameter_hooks(True)
    for (track, slot), value in baseline.items():
        actual = rig.call(0x4005AA1A, track, slot)
        require(actual == (SLOT if track < 6 and slot == 33 else value),
                f"Décodage modifié hors HARMONY : {track}/{slot}")
    print("ok P-lock : mapping natif conservé, seule extension ID33 → slot28, bornes audio/FX", flush=True)
    rig.bind(B2)
    empty_locks = rig.bytes(B2 + 4332, 26310)
    scratch = SERIAL + 16000
    for identifier, track in ((33, 6), (33, 255), (34, 0), (255, 0)):
        rig.uc.mem_write(scratch, b"\xff" * 10400)
        rig.uc.mem_write(scratch, bytes([identifier, track]) + struct.pack(">H", 1))
        rig.call(0x4005B766, B2 + 4332, scratch)
        require(rig.bytes(B2 + 4332, 26310) == empty_locks,
                "Le chargeur accepte une nouvelle lane sur FX/piste ou ID invalide")
    # Une lane ID33 existante ne contient pas son ancien numéro de slot RAM.
    # Construire ces octets indépendamment du nouveau writer prouve que les
    # prises de la version slot23 migrent vers 28 sans atteindre Attack.
    rig.uc.mem_write(scratch, b"\xff" * 10400)
    for track in range(6):
        lane = scratch + 130 * track
        rig.uc.mem_write(lane, bytes([33, track]))
        for step, modifier in ((0, 0), (7, track + 1), (63, 6 - track)):
            rig.uc.mem_write(lane + 2 + 2 * step, struct.pack(">H", modifier))
    rig.call(0x4005B766, B2 + 4332, scratch)
    require(all(rig.get(track, step) == modifier
                for track in range(6)
                for step, modifier in ((0, 0), (7, track + 1), (63, 6 - track))),
            "Une ancienne lane ID33 perd ses valeurs dans le nouveau slot")
    require(all(rig.get(track, step, slot) == -1
                for track in range(6) for step in range(64) for slot in range(23, 28)),
            "La migration ID33 écrase un paramètre de Model-TG")
    print("ok P-lock : anciennes lanes ID33 chargées au slot28, réserves Model-TG23..27 intactes", flush=True)
    rig.bind(B1)

    for track in range(6):
        for step in (0, 7, 31, 32, 63):
            rig.set(track, step, 11, 32 * 256 + 173)
            rig.set(track, step, 12, 7 * 256 + 19)
            rig.set(track, step, 22, 12000 + step)
            rig.set(track, step, 0, 5000 + step)
    rig.parameter_hooks(False)
    rig.call(0x4005BA0A, SERIAL, B1, 0)
    old_save = rig.bytes(SERIAL, 14800)
    rig.parameter_hooks(True)
    rig.call(0x4005BA0A, SERIAL, B1, 0)
    require(rig.bytes(SERIAL, 14800) == old_save,
            "Une sauvegarde sans nouveaux locks diffère du firmware stock")
    old_locks = rig.bytes(B1 + 4332, 26310)
    for track in range(6):
        for step, modifier in ((0, 1), (7, 6), (31, 3), (32, 0), (63, 5)):
            rig.set(track, step, SLOT, modifier)
    original = rig.bytes(B1 + 4332, 26310)
    rig.call(0x4005BA0A, SERIAL, B1, 0)
    rig.parameter_hooks(False)
    rig.call(0x4005B894, B2, SERIAL, 0)
    require(rig.bytes(B2 + 4332, 26310) == old_locks,
            "Retour au firmware stock : HARMONY n'est pas ignoré proprement")
    rig.parameter_hooks(True)
    rig.call(0x4005B894, B2, SERIAL, 0)
    require(rig.bytes(B2 + 4332, 26310) == original,
            "Sauvegarde/chargement perd les locks natifs ou HARMONY")
    rig.call(0x4008F1F0, B1, B2, 30710)
    require(rig.bytes(B1 + 4332, 26310) == original, "Copie pattern perd HARMONY")
    print("ok P-lock : ancien pattern identique ; six pistes/64 pas après save/load/copy ; retour OS stock ignore seulement HARMONY", flush=True)

    # Le writer partiel met à jour une lane existante sans dupliquer ID33.
    rig.set(2, 9, SLOT, 4)
    rig.call(0x4005BA90, SERIAL + 4336, B1 + 4332, 0, SLOT, 2)
    rig.call(0x4005B894, B2, SERIAL, 0)
    rig.bind(B2, initialize=False)
    require(rig.get(2, 9) == 4, "Writer partiel perd HARMONY")
    rig.call(0x4000DCEC, rig.plock, 2, 9, SLOT)
    require(rig.get(2, 9) == -1, "Effacement lock HARMONY refusé")
    rig.call(0x400164F2, rig.track(2), 7)
    require(all(rig.get(2, 7, slot) == -1 for slot in range(33)),
            "Effacement de tous les locks laisse HARMONY")
    print("ok P-lock : writer partiel, effacement individuel et effacement natif de tous les locks", flush=True)

    rig.bind(B1)
    rig.live(False, 3)
    rig.call("ck_plock_gesture", 0, 4)
    require(rig.get(0, 3) == -1, "Geste hors enregistrement écrit un lock")
    for track in range(6):
        for modifier in range(7):
            step = modifier + 8
            rig.live(True, step, track)
            rig.call("ck_plock_gesture", track, modifier)
            require(rig.get(track, step) == modifier, "Geste live non enregistré")
            require(rig.call(0x40015C7C, rig.track(track), step) & 0xFF,
                    "Pas vide non transformé en lock-only natif")
            require(not rig.call(0x40015C20, rig.track(track), step) & 0xFF,
                    "Geste sur un accord tenu redéclenche une note")
    print("ok P-lock live : sept états et six pistes ; retour zéro écrit, pas vides lock-only sans note", flush=True)

    # Le pas de note lui-même reçoit un snapshot, même si le pad est pressé
    # avant la touche. Cette preuve appelle le vrai recorder et son hook final.
    rig.call(0x40012158, PROJECT, 0, 48, 100, 0, 4, 0, 0, 0xFFFFFFFF)
    require(rig.get(0, 4) == 0, "Nouvelle note sans pad conserve une ancienne extension")
    require(rig.call(0x40015C20, rig.track(0), 4) & 0xFF, "Le hook enlève la note native")
    for step, pad, down, expected in ((16, 1, True, -1), (17, 4, True, -1),
                                     (18, 4, False, -1), (19, 1, False, -1)):
        rig.live(True, step)
        rig.pad(pad, down)
        require(rig.get(0, step) == expected,
                "Le vrai chemin pad press/release perd l'appui ou enregistre un retour")
    rig.live(False)
    rig.pad(6, True)
    rig.call(0x40012158, PROJECT, 0, 50, 100, 0, 20, 0, 0, 0xFFFFFFFF)
    require(rig.get(0, 20) == 0, "Pad préparé fuit dans la capture d'une note hors UI")
    rig.pad(6, False)
    rig.call(0x40012158, PROJECT, 0, 50, 100, 0, 20, 0, 0, 0xFFFFFFFF)
    require(rig.get(0, 20) == 0, "Pad préparé relâché fuit dans la capture d'une note")
    rig.call("ck_ui_clear_modifiers", 0, rig.call("ck_ui_header"))
    rig.call(0x40012158, PROJECT, 0, 50, 100, 0, 20, 0, 0, 0xFFFFFFFF)
    require(rig.get(0, 20) == 0, "Nouvelle prise à EXT conserve un ancien lock")
    rig.live(False)
    rig.uc.mem_write(UI + 357, b"\1")
    require(rig.call("ck_plock_grid", 1, 6) == 0,
            "Grille sans pas tenu consomme le pad")
    rig.word(UI + 348, 1 << 31)
    rig.word(UI + 352, (1 << 2) | (1 << 31))
    require(rig.call("ck_plock_grid", 1, 6) == 1, "Held TRIG+T rejeté")
    require([rig.get(1, step) for step in (2, 31, 63)] == [6, 6, 6],
            "Masque held TRIG 64 bits mal interprété")
    rig.call("ck_plock_grid", 1, 6)
    require([rig.get(1, step) for step in (2, 31, 63)] == [0, 0, 0],
            "Second appui sur le même pad ne remet pas EXT")
    rig.call("ck_plock_grid", 1, 6)
    rig.uc.mem_write(UI + 389, b"\1")
    require(rig.call("ck_plock_grid", 1, 3) == 0, "Grille secondaire modifiée")
    rig.uc.mem_write(UI + 389, b"\0")
    rig.machine = 0
    require(rig.call("ck_plock_grid", 1, 3) == 0, "Autre machine écrit HARMONY")
    require(rig.get(1, 2) == 6, "Geste rejeté modifie le lock")
    print("ok P-lock : préparations sans lock, snapshot note/EXT, held TRIG+T répété, modes protégés", flush=True)
    rig.bind(B2)
    for slot in range(13):
        for track in range(6):
            rig.set(track, 0, slot, 100 + slot)
    rig.set(0, 0, 13, 123)
    for track in range(6):
        rig.set(track, 0, SLOT, track + 1)
    # La sérialisation native limite à 79 lanes puis garde une sentinelle.
    # La nouvelle voie partage cette limite : aucune extension du buffer et
    # aucun écrasement de l'en-tête quand la capacité native est épuisée.
    outputs = []
    for patched_hooks in (False, True):
        rig.parameter_hooks(patched_hooks)
        rig.uc.mem_write(scratch, b"\xa5" * 10416)
        rig.call(0x4005B95C, scratch + 8, B2 + 4332, 0)
        require(rig.bytes(scratch, 8) == b"\xa5" * 8
                and rig.bytes(scratch + 10408, 8) == b"\xa5" * 8,
                "Capacité native dépassée : sortie du buffer de lanes")
        outputs.append(rig.bytes(scratch + 8, 10400))
    require(outputs[0] == outputs[1] and outputs[1][79 * 130:79 * 130 + 2] == b"\xff\xff",
            "Limite de capacité native modifiée")
    print("ok P-lock : IDs/pistes invalides ignorés ; capacité native saturée conservée sans débordement", flush=True)
    _observer_checks(stock, patched, symbols)
    _attack_recording_checks(stock, patched, symbols)
    return rig
