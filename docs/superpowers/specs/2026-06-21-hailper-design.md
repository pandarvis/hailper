# Hailper — Assistant vocal pour grand-père malvoyant et malentendant

**Date :** 2026-06-21
**Statut :** Conception validée (en attente de relecture utilisateur)

## 1. Contexte et objectif

Mon grand-père est atteint de DMLA (quasi aveugle, vision centrale perdue) et
malentendant. Il ne peut plus utiliser une interface graphique ni YouTube. Sa
passion : écouter de la musique. Il aime aussi être tenu au courant de ses
mails (boîte `messagerie.orange.fr`).

**Objectif :** un assistant **100 % vocal** qui tourne sur son PC Linux Mint.
Il appuie sur **un bouton physique**, parle, et l'assistant agit puis lui répond
**à voix haute**. Aucun écran, aucune souris, aucun navigateur.

### Principes de conception (déficience double : vue + audition)

- **Voix-first** : tout passe par la parole en entrée et en sortie.
- **Aucun silence sans explication** : chaque état produit un repère sonore ou
  une phrase parlée. Il ne doit jamais se retrouver « perdu ».
- **Voix de sortie forte et lente**, claire.
- **Robustesse > richesse fonctionnelle** : peu de fonctions, mais qui
  marchent toujours.
- **Un seul service payant** : l'API Anthropic. Tout le reste est local et
  gratuit.

## 2. Matériel cible

**Lenovo V110** — Intel Core i3-6006U (2 cœurs / 4 threads, 2 GHz, 2016),
4 Go DDR4, SSD, **Linux Mint 22.3 XFCE**.

Contrainte principale : **4 Go de RAM** et CPU modeste. La machine est **quasi
dédiée** à cet usage (assistant + musique + internet, rien d'autre), donc on
peut mobiliser la RAM et optimiser pour ce seul programme. Le choix de **ne pas
utiliser de navigateur** (musique via `mpv`) économise énormément de mémoire.

## 3. Périmètre de la v1

**Inclus :**
- Recherche et lecture de musique YouTube (audio seul, sans navigateur).
- Contrôle de lecture : pause/reprise, stop, suivant, volume.
- **Favoris vocaux** : ajouter la musique en cours, lister, jouer, retirer.
- **Récap des mails** orange.fr (lecture seule) : résumé des derniers mails,
  lecture intégrale d'un mail au choix.

**Hors périmètre v1 (volontairement — YAGNI) :**
- Envoi / réponse aux mails, marquage, suppression.
- Météo, rappels, heure, autres commandes.
- Playlists avancées, multi-utilisateur, interface graphique.

## 4. Architecture

Boucle vocale composée de briques indépendantes, chacune avec une
responsabilité unique et une interface claire.

```
[Bouton] -> [Reco vocale] -> [Cerveau Haiku] -> [Action] -> [Voix] -> (retour veille)
                                   |
                  +----------------+----------------+
                  |        |          |             |
              [Musique] [Favoris]  [Mails]      [Réponse parlée]
```

### 4.1 Briques

1. **Déclencheur (`trigger`)** — détecte l'appui sur un **bouton physique** et
   lance un cycle d'écoute (joue un *bip* « j'écoute »).
   - v1 par défaut : la **touche Espace** (grande, facile à trouver au toucher),
     capturée globalement via `evdev` (Linux). La machine étant dédiée au bot,
     monopoliser Espace ne pose pas de problème. La touche reste **configurable**.
     Un bouton USB ou une télécommande peut être substitué plus tard **sans
     changer le code**, car l'entrée est abstraite derrière une interface.

2. **Reconnaissance vocale (`stt`)** — enregistre le micro jusqu'au silence
   (détection d'activité vocale) puis transcrit en texte français.
   - Implémentation : **`faster-whisper`**, modèle **`base`** (quantif. int8),
     **chargé une seule fois au démarrage et résident en RAM**. Repli **`tiny`**
     configurable si la RAM ou la latence pose problème.
   - Exposé derrière une interface `transcribe(audio) -> str` pour rester
     remplaçable.

3. **Cerveau (`brain`)** — reçoit le texte + un *system prompt* décrivant les
   outils disponibles ; **Claude Haiku** renvoie soit un appel d'outil, soit une
   réponse parlée.
   - SDK : `anthropic` (Python). Modèle : **`claude-haiku-4-5-20251001`**.
   - **Tool use** + **prompt caching** sur le system prompt (réduit coût/latence).
   - Conserve un **court contexte conversationnel** (dernières interactions) pour
     gérer les suites (« plus fort », « non, la suivante »).
   - Outils exposés :
     - `play_music(query)` — chercher et jouer
     - `control_playback(action)` — pause / reprise / stop / suivant / volume +/-
     - `add_favorite()` / `remove_favorite()` / `list_favorites()` / `play_favorites()`
     - `read_recent_emails(count)` — résumé des derniers mails
     - `read_email_full(index)` — lecture intégrale d'un mail
     - `say(text)` — réponse parlée simple (aide, confirmation…)

4. **Lecteur musique (`music`)** — pilote **`mpv`** lancé en arrière-plan,
   contrôlé via son **socket IPC JSON** (`--input-ipc-server`). Résolution des
   vidéos via **`yt-dlp`** (audio seul, sans pub, sans navigateur).
   - Recherche : `yt-dlp ytsearch1:<requête>` → URL audio → `mpv`.
   - **Mise à jour automatique de `yt-dlp`** (au démarrage et/ou en cas d'échec),
     car YouTube casse régulièrement les anciennes versions.

5. **Favoris (`favorites`)** — fichier local `~/.hailper/favorites.json` :
   liste de `{title, video_id, added_at}`. Ajouter la piste en cours, lister
   (lu à voix haute), jouer, retirer.

6. **Lecteur de mails (`mail`)** — `imaplib` SSL vers **`imap.orange.fr:993`**.
   Récupère les N derniers mails (en-têtes + corps, HTML nettoyé), les passe à
   **Haiku** pour un résumé parlé concis en français. **Lecture seule.**
   - Identifiants depuis la config (**« mot de passe pour applications »** Orange).

7. **Voix de sortie (`tts`)** — **Piper** (local), voix française, **débit lent
   et volume élevé**. Plus des **repères sonores** (earcons WAV) : « j'écoute »,
   « je réfléchis », « c'est fait », « erreur ».

8. **Chef d'orchestre (`main`)** — machine à états
   `veille -> écoute -> réflexion -> action -> parole -> veille`. **Lancé au
   démarrage** (service systemd utilisateur), **redémarre en cas de crash**,
   journalise dans un fichier.

### 4.2 Configuration

Un seul fichier de config (`~/.hailper/config.toml`) :
clé API Anthropic, identifiants Orange (IMAP), taille du modèle Whisper, touche
de déclenchement, volume, voix Piper. Un `config.example.toml` est fourni.

## 5. Flux d'une commande

1. Appui bouton → *bip* « j'écoute »
2. Enregistrement micro jusqu'au silence
3. `faster-whisper` → texte français
4. *bip* « je réfléchis » ; Claude Haiku (contexte + outils) → appel d'outil
5. Exécution de l'outil (musique / favoris / mails…)
6. Piper énonce la confirmation ou la réponse ; *bip* « c'est fait »
7. Retour en veille

### Exemples de commandes
- « Mets de la musique des années 2000 »
- « Ajoute ça à mes favoris » / « Mets mes favoris »
- « Plus fort » / « Pause » / « Chanson suivante »
- « Résume-moi mes derniers mails » / « Lis-moi le mail numéro 2 »

## 6. Gestion d'erreurs

Règle d'or : **aucun silence sans explication**. Chaque échec produit un message
parlé clair en français + un earcon « erreur ».

- Reco vide / incomprise → « Je n'ai pas compris, réappuie et réessaie. »
- Pas d'internet → message parlé explicite.
- Musique introuvable / `yt-dlp` en échec → message + tentative de mise à jour.
- IMAP indisponible / identifiants invalides → message parlé.
- Timeouts partout : le système ne reste jamais bloqué en silence.

## 7. Pile technique

- **Python 3.11+**, environnement virtuel dédié.
- Dépendances : `anthropic`, `faster-whisper`, capture micro
  (`sounddevice`/`pyaudio` + VAD `webrtcvad`), `piper-tts` (ou binaire Piper),
  `mpv` + contrôle IPC (`python-mpv` ou socket brut), `yt-dlp`, `imaplib`
  (stdlib).
- **Cible : Linux Mint** (XFCE). `evdev`, `mpv`, lecture audio sont spécifiques
  Linux. Le développement peut se faire sur une autre OS via le **mode texte**.

### Structure projet proposée

```
hailper/
  hailper/
    __init__.py
    main.py          # orchestrateur / machine à états
    config.py        # chargement de la config
    trigger.py       # écoute du bouton / touche
    stt.py           # reconnaissance vocale (interface remplaçable)
    tts.py           # Piper + earcons
    brain.py         # Claude Haiku + définition/dispatch des outils
    music.py         # lecteur mpv / yt-dlp
    favorites.py     # stockage des favoris
    mail.py          # lecteur IMAP orange
    audio.py         # enregistrement micro + lecture audio
  sounds/            # earcons (WAV)
  tests/
  pyproject.toml
  config.example.toml
  README.md
```

## 8. Mode test (développement)

- `--text` : taper les commandes au clavier au lieu de parler.
- Option pour **afficher** la sortie TTS au lieu de la jouer.
- Permet de développer et déboguer le **cerveau, la musique, les mails** sans
  micro ni haut-parleurs, y compris hors Linux.

## 9. Stratégie de test

- Tests unitaires : stockage des favoris, parsing/résumé des mails (IMAP et
  Claude mockés), dispatch des intentions (outils mockés), chargement config.
- Tests bout-en-bout en **mode texte**.
- Checklist de test vocal manuel (sur la machine cible).

## 10. Coût

Seul l'API Anthropic est facturé. Chaque commande = un petit appel Haiku
(system prompt mis en cache). Les résumés de mails sont un peu plus gros.
Ordre de grandeur réaliste : **quelques centimes par jour**.

## 11. Prérequis (côté installateur)

1. Une **clé API Anthropic**.
2. Le **« mot de passe pour applications »** Orange + accès IMAP activé.
3. Déclencheur : **touche Espace** par défaut (aucun matériel supplémentaire).
4. Sortie audio : **haut-parleurs externes** (déjà présents — bien, il entend mal).
5. Entrée audio : **micro intégré du portable** en v1. ⚠️ Fortement recommandé :
   un **micro USB (~15 €) ou un casque-micro** posé près de lui — le micro
   interne est lointain et dégrade nettement la reconnaissance d'une voix âgée
   et douce. Amélioration conseillée, non bloquante.

## 12. Risques et parades

- **`yt-dlp` cassé par YouTube** → mise à jour automatique intégrée.
- **Latence Whisper sur 4 Go** → modèle `base` résident en RAM ; repli `tiny` ;
  l'architecture remplaçable autorise un passage cloud ultérieur si besoin.
- **Précision reco / voix âgée en français** → à tester sur la machine cible ;
  leviers `tiny`/`base` puis cloud.
- **Micro intégré (qualité d'entrée)** → principal risque UX ; parade : micro
  USB / casque-micro recommandé (cf. prérequis).
- **Friction config IMAP Orange** → documentée dans les prérequis.

## 13. Développement et validation

Le développement se fera sur une **autre machine que la cible** (matériel et
OS différents). Conséquence sur la conception :

- Le **mode texte** (§8) permet de développer/tester le cerveau, la musique et
  les mails sans micro ni Linux.
- Les briques **spécifiques Linux** (capture Espace via `evdev`, `mpv`, `piper`,
  lecture audio) sont **isolées derrière des interfaces** et ne seront validées
  de bout en bout qu'**au déploiement sur le Lenovo V110**.
- Les tests sur la machine de développement **ne reflètent pas** la latence ni
  la qualité audio réelles : une **phase de réglage sur la machine cible** est
  prévue (modèle Whisper, volume/débit de la voix, seuils de silence du micro).
