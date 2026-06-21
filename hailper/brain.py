from __future__ import annotations

from .models import Email

SYSTEM_PROMPT = (
    "Tu es l'assistant vocal d'une personne âgée, malvoyante et malentendante. "
    "Tu l'aides à écouter de la musique sur YouTube, à gérer ses favoris, à "
    "écouter le résumé de ses mails, et à contrôler son ordinateur. Réponds "
    "TOUJOURS en français, en phrases très courtes et simples, car tes réponses "
    "seront lues à voix haute. Utilise les outils pour agir. N'invente jamais le "
    "contenu d'un mail : utilise les outils de mail. "
    "Pour le volume (« plus fort », « moins fort »), utilise system_volume : il "
    "règle le volume général, donc ta voix aussi. "
    "Pour éteindre ou redémarrer l'ordinateur, appelle power_control : cela "
    "demande une confirmation. Quand il répond « oui » à une confirmation, "
    "appelle confirm ; quand il répond « non », appelle cancel. "
    "Si une demande n'est pas claire, demande gentiment de répéter."
)


def build_tools() -> list[dict]:
    return [
        {
            "name": "play_music",
            "description": "Chercher et jouer une musique ou un style sur YouTube.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Ce qu'il veut écouter"}},
                "required": ["query"],
            },
        },
        {
            "name": "control_playback",
            "description": "Contrôler la lecture en cours.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["pause", "resume", "stop", "next"],
                    }
                },
                "required": ["action"],
            },
        },
        {"name": "add_favorite", "description": "Ajouter la musique en cours aux favoris.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "remove_favorite", "description": "Retirer la musique en cours des favoris.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "list_favorites", "description": "Énoncer la liste des favoris.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "play_favorites", "description": "Jouer les musiques favorites.",
         "input_schema": {"type": "object", "properties": {}}},
        {
            "name": "read_recent_emails",
            "description": "Résumer les derniers mails reçus.",
            "input_schema": {
                "type": "object",
                "properties": {"count": {"type": "integer", "description": "Nombre de mails"}},
            },
        },
        {
            "name": "read_email_full",
            "description": "Lire en entier un mail du dernier récap, par son numéro.",
            "input_schema": {
                "type": "object",
                "properties": {"index": {"type": "integer"}},
                "required": ["index"],
            },
        },
        {
            "name": "get_datetime",
            "description": "Donner l'heure et la date actuelles.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "system_volume",
            "description": "Monter ou baisser le volume général (musique ET voix).",
            "input_schema": {
                "type": "object",
                "properties": {"action": {"type": "string", "enum": ["up", "down"]}},
                "required": ["action"],
            },
        },
        {
            "name": "power_control",
            "description": "Éteindre ou redémarrer l'ordinateur. Demande TOUJOURS confirmation.",
            "input_schema": {
                "type": "object",
                "properties": {"action": {"type": "string", "enum": ["shutdown", "reboot"]}},
                "required": ["action"],
            },
        },
        {"name": "confirm", "description": "Confirmer l'action en attente (quand il dit oui).",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "cancel", "description": "Annuler l'action en attente (quand il dit non).",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "restart_assistant", "description": "Redémarrer l'assistant vocal lui-même.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "get_weather", "description": "Donner la météo.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "say", "description": "Répondre simplement à voix haute (aide, confirmation).",
         "input_schema": {"type": "object", "properties": {"text": {"type": "string"}},
                          "required": ["text"]}},
    ]


def summarize_emails(client, emails: list[Email], model: str = "claude-haiku-4-5-20251001") -> str:
    listing = "\n".join(
        f"{e.index}. De {e.sender} — {e.subject} : {e.body[:500]}" for e in emails
    )
    resp = client.messages.create(
        model=model,
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": (
                "Voici les derniers mails. Fais un résumé court à lire à voix haute "
                "à une personne âgée : pour chaque mail, dis le numéro, l'expéditeur "
                "et l'essentiel en une phrase. Sois bref et clair.\n\n" + listing
            ),
        }],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


class Brain:
    def __init__(self, client, actions, model: str, system_prompt: str = SYSTEM_PROMPT):
        self.client = client
        self.actions = actions
        self.model = model
        # Le system prompt et les outils ne pèsent que quelques centaines de
        # tokens, bien en dessous du seuil de cache de 4096 tokens : le prompt
        # caching ne s'appliquerait pas. On garde donc un simple string.
        self.system = system_prompt
        self.tools = build_tools()
        self.history: list[dict] = []

    MAX_HISTORY = 16

    def _trim_history(self) -> None:
        # Le spec demande un contexte conversationnel court. On borne
        # l'historique en gardant la fin, mais en redémarrant sur un vrai tour
        # utilisateur (pas un tool_result) pour que la structure de messages
        # reste valide pour l'API.
        if len(self.history) <= self.MAX_HISTORY:
            return
        start = len(self.history) - self.MAX_HISTORY
        while start < len(self.history):
            msg = self.history[start]
            if msg["role"] == "user" and isinstance(msg["content"], str):
                break
            start += 1
        self.history = self.history[start:]

    def handle(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        while True:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system,
                tools=self.tools,
                messages=self.history,
            )
            self.history.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                reply = "".join(
                    b.text for b in resp.content if getattr(b, "type", None) == "text"
                ).strip()
                self._trim_history()
                return reply
            tool_results = []
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use":
                    result = self._dispatch(block.name, dict(block.input))
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    )
            self.history.append({"role": "user", "content": tool_results})

    def _dispatch(self, name: str, args: dict) -> str:
        fn = getattr(self.actions, name, None)
        if fn is None:
            return f"Outil inconnu : {name}"
        try:
            return fn(**args)
        except Exception as exc:  # never break the loop on a tool error
            return f"Erreur en exécutant {name} : {exc}"
