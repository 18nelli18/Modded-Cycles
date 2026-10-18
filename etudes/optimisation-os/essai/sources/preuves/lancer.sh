#!/bin/sh
# Rejoue toutes les preuves des fichiers d'essai (4 cœurs : environ 1 h 30). Il faut le .syx officiel dans
# /home/user/Modded-Cycles/firmware/, unicorn et numpy, et les binutils m68k (preuve_compteur assemble sa fonction
# factice). OUT : dossier des deux .syx livrés.
OUT=${OUT:-/mnt/project-files/optimisation-os/essai}
cd "$(dirname "$0")" || exit 1
mkdir -p logs
python3 preuve_compteur.py --out "$OUT" > logs/compteur.log 2>&1 &
python3 preuve_gels.py --out "$OUT" > logs/gels.log 2>&1 &
for s in defaut envois dist glissements arret silence; do
  python3 preuve_audio.py $s --out "$OUT" > logs/audio_$s.log 2>&1 &
done
wait
for s in arret six envois dist apres; do
  for i in reference optimise; do
    python3 preuve_charge.py $s $i --out "$OUT" > logs/charge_${s}_$i.log 2>&1 &
  done
  wait
done
grep -H "TOUT OK\|ÉCHEC" logs/*.log
