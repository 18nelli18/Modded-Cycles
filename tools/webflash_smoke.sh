#!/usr/bin/env bash
# Smoke test navigateur du flasher web (docs/flasher/) avec jsdom : charge la
# vraie page + ses scripts, verifie qu'il n'y a AUCUNE erreur JS au chargement
# (regression des collisions de variables entre scripts), que "Activer le MIDI"
# donne un retour clair, et que construire puis envoyer fonctionne.
#
# jsdom est installe dans un dossier temporaire (npm), rien n'est ajoute au depot.
# Necessite node, npm et le reseau (registry.npmjs.org).
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "node est requis"; exit 1; }
command -v npm >/dev/null || { echo "npm est requis"; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

python3 tools/webbuild_synth.py "$tmp" >/dev/null       # fabrique synth.syx + meta.json
( cd "$tmp" && npm init -y >/dev/null 2>&1 && npm install jsdom >/dev/null 2>&1 )
NODE_PATH="$tmp/node_modules" node tools/webflash_smoke.js "$tmp"
