#!/usr/bin/env bash
# Hailper — installation sur Linux Mint / Ubuntu (le PC de papy).
#
#   git clone https://github.com/pandarvis/hailper.git ~/hailper
#   bash ~/hailper/deploy/install.sh
#
# Le script est idempotent : on peut le relancer sans risque.
set -euo pipefail

# Dossier du dépôt = parent du dossier de ce script.
REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
CONFIG_DIR="$HOME/.hailper"
VOICE_DIR="$CONFIG_DIR/voices"
VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium"
VOICE="fr_FR-siwis-medium.onnx"

echo "==> Dépôt : $REPO_DIR"
if [ "$REPO_DIR" != "$HOME/hailper" ]; then
  echo "    ATTENTION : le service systemd attend le dépôt dans ~/hailper."
  echo "    Clone-le plutôt dans ~/hailper, ou adapte deploy/hailper.service."
fi

echo "==> Python : $(python3 --version)"
echo "==> Dépendances système (le mot de passe sudo va être demandé)"
sudo apt-get update
sudo apt-get install -y mpv alsa-utils git python3-venv python3-pip wget

echo "==> Environnement Python (.venv) + installation du projet"
cd "$REPO_DIR"
python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -e .

echo "==> Voix française Piper"
mkdir -p "$VOICE_DIR"
if [ ! -f "$VOICE_DIR/$VOICE" ]; then
  wget -q -O "$VOICE_DIR/$VOICE" "$VOICE_BASE/$VOICE"
  wget -q -O "$VOICE_DIR/$VOICE.json" "$VOICE_BASE/$VOICE.json"
  echo "    voix téléchargée dans $VOICE_DIR"
else
  echo "    voix déjà présente, conservée"
fi

echo "==> Fichier de configuration"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
  cp "$REPO_DIR/config.example.toml" "$CONFIG_DIR/config.toml"
  sed -i "s|^tts_voice = .*|tts_voice = \"$VOICE_DIR/$VOICE\"|" "$CONFIG_DIR/config.toml"
  echo "    $CONFIG_DIR/config.toml créé (À COMPLÉTER : clé Anthropic + Orange)"
else
  echo "    config.toml déjà présent, laissé tel quel"
fi

echo "==> Accès à la touche Espace (groupe input)"
sudo usermod -aG input "$USER"

echo "==> Service systemd utilisateur"
mkdir -p "$HOME/.config/systemd/user"
cp "$REPO_DIR/deploy/hailper.service" "$HOME/.config/systemd/user/"
chmod +x "$REPO_DIR/deploy/update-ytdlp.sh"
systemctl --user daemon-reload

cat <<EOF

============================================================
 Installation terminée. Il reste 3 étapes :

 1. Éditer  $CONFIG_DIR/config.toml  et renseigner :
      [secrets]
      anthropic_api_key   = "sk-ant-..."      # compte Anthropic dédié
      orange_email        = "prenom.nom@orange.fr"
      orange_app_password = "..."             # mot de passe "applications" Orange

 2. Se DÉCONNECTER puis RECONNECTER une fois (groupe 'input').

 3. Démarrer le service :
      systemctl --user enable --now hailper
      loginctl enable-linger $USER       # démarrage au boot sans session
      journalctl --user -u hailper -f    # suivre les logs

 Test sans micro (commandes tapées au clavier) :
      cd $REPO_DIR && ./.venv/bin/python -m hailper.main --text
============================================================
EOF
