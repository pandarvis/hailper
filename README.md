# Hailper

Assistant vocal pour une personne malvoyante et malentendante : écoute de la musique YouTube sans navigateur, gestion de favoris vocaux, récapitulatif des mails Orange, déclenchement par la touche Espace, réponses lues à voix haute par le système.

---

## Fonctionnement

1. L'utilisateur appuie sur la **touche Espace** (capturée directement via `evdev`, sans interface graphique).
2. Un bip de confirmation retentit, puis Hailper **enregistre la commande vocale** et la transcrit localement avec **Whisper**.
3. La transcription est envoyée au **cerveau Claude Haiku** (API Anthropic), qui choisit l'action à effectuer.
4. L'action est exécutée (lecture YouTube via `yt-dlp` + `mpv`, gestion des favoris, lecture des mails via IMAP, contrôle du volume…).
5. La réponse est lue à voix haute par **Piper TTS**, en français.

Seul service payant : **l'API Anthropic** (Claude Haiku, coût très faible à l'usage).

---

## Développement (sur n'importe quel OS, mode texte)

Ces étapes permettent de travailler et de lancer les tests sans micro ni haut-parleur.

### Prérequis

- Python 3.11 ou supérieur
- Clé API Anthropic (variable d'environnement `ANTHROPIC_API_KEY`)

### Installation de l'environnement

```bash
python -m venv .venv
# Linux / macOS :
source .venv/bin/activate
# Windows :
.venv\Scripts\activate

pip install -e ".[dev]"
```

### Lancer les tests

```bash
pytest
```

### Lancer en mode texte (sans micro ni voix)

Ce mode remplace le micro par le clavier et la synthèse vocale par du texte dans le terminal.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Linux / macOS
# Windows : set ANTHROPIC_API_KEY=sk-ant-...

python -m hailper.main --text --config config.example.toml
```

On tape ensuite les commandes au clavier (par exemple : `Mets de la musique des années 2000`), et les réponses s'affichent dans le terminal.

---

## Installation sur la machine cible (Linux Mint)

### 1. Dépendances système

```bash
sudo apt install mpv alsa-utils
```

(Piper TTS n'est **pas** installé via `apt` : il vient avec les dépendances Python du projet — paquet `piper-tts` — installé à l'étape 3. Seul le modèle de voix se télécharge à part, voir ci-dessous.)

### 2. Voix Piper française

Télécharger le modèle `fr_FR-siwis-medium` (fichiers `.onnx` et `.onnx.json`) depuis le dépôt Hugging Face **rhasspy/piper-voices**, puis les placer dans un dossier de votre choix, par exemple `~/.local/share/piper-voices/`.

Dans `~/.hailper/config.toml`, sous la section `[audio]`, renseigner le chemin complet vers le fichier `.onnx` :

```toml
[audio]
tts_voice = "/home/VotreNom/.local/share/piper-voices/fr_FR-siwis-medium.onnx"
```

### 3. Cloner le dépôt et créer l'environnement Python

```bash
cd ~
git clone <url-du-depot> hailper
cd hailper
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Créer le fichier de configuration

```bash
mkdir -p ~/.hailper
cp ~/hailper/config.example.toml ~/.hailper/config.toml
```

Éditer `~/.hailper/config.toml` et renseigner au minimum (en respectant les sections du fichier) :

- `anthropic_api_key` (section `[secrets]`) : votre clé API Anthropic.
- `orange_email` (section `[secrets]`) : votre adresse Orange (`prenom.nom@orange.fr`).
- `orange_app_password` (section `[secrets]`) : le **mot de passe pour applications** Orange (à générer depuis l'espace client Orange — différent du mot de passe de connexion habituel). Serveur IMAP : `imap.orange.fr:993` (déjà renseigné dans la section `[mail]`).
- `tts_voice` (section `[audio]`) : chemin vers le fichier `.onnx` Piper (voir étape 2).

### 5. Accès à la touche Espace (groupe `input`)

Pour capturer la touche Espace sans être root :

```bash
sudo usermod -aG input $USER
```

Se déconnecter puis se reconnecter pour que le changement de groupe prenne effet.

### 6. Earcons (sons de confirmation)

Les sons courts de retour (bips de démarrage, d'erreur…) sont déjà inclus dans le dossier `sounds/` du dépôt. Aucune action supplémentaire n'est nécessaire.

### 7. Installer et démarrer le service systemd

```bash
mkdir -p ~/.config/systemd/user
cp ~/hailper/deploy/hailper.service ~/.config/systemd/user/
chmod +x ~/hailper/deploy/update-ytdlp.sh
systemctl --user enable --now hailper
loginctl enable-linger $USER   # démarrer au boot sans ouverture de session
```

Suivre les logs en temps réel :

```bash
journalctl --user -u hailper -f
```

À chaque démarrage du service, `yt-dlp` est automatiquement mis à jour (YouTube casse régulièrement les anciennes versions).

---

## Commandes vocales

Exemples de commandes que l'on peut prononcer après avoir appuyé sur la touche Espace :

| Commande | Effet |
|---|---|
| « Mets de la musique des années 2000 » | Lance une recherche YouTube et joue le résultat |
| « Ajoute ça à mes favoris » | Enregistre la chanson en cours dans les favoris |
| « Mets mes favoris » | Joue les favoris dans l'ordre où ils ont été ajoutés |
| « Plus fort » | Augmente le volume |
| « Moins fort » | Diminue le volume |
| « Pause » | Met la lecture en pause (ou la reprend) |
| « Chanson suivante » | Passe au morceau suivant |
| « Résume-moi mes derniers mails » | Lit un résumé des derniers mails Orange |
| « Lis-moi le mail numéro 2 » | Lit le contenu complet du deuxième mail |

---

## Réglages

Ces paramètres dans `~/.hailper/config.toml` permettent d'ajuster le comportement :

- **`whisper_model`** : modèle de reconnaissance vocale. La valeur `base` offre un bon équilibre qualité/vitesse. Passer à `tiny` si la transcription est trop lente sur la machine cible.
- **`tts_rate`** : vitesse de la synthèse vocale (en mots par minute ou facteur selon la version de Piper). Une valeur plus petite donne une voix plus lente et plus claire — recommandé pour une meilleure compréhension.
- **Microphone** : pour de meilleurs résultats de reconnaissance vocale, un **micro USB** (casque ou micro de table) est fortement conseillé par rapport au micro intégré d'un ordinateur portable.

---

## Matériel cible

- **Ordinateur** : Lenovo V110
- **Processeur** : Intel Core i3-6006U
- **RAM** : 4 Go
- **Stockage** : SSD
- **Système d'exploitation** : Linux Mint 22.3 XFCE
