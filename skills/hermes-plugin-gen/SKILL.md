---
name: hermes-plugin-gen
description: "Generate and extend Hermes plugins from descriptions."
version: 1.0.0
author: Iruzen & Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [plugin-generation, scaffolding, development, tooling]
    category: software-development
    related_skills: [plugin-creator, skill-creator, hermes-agent]
---

# Plugin Generator Skill

Génère, étend et maintient des plugins Hermes à partir de descriptions en langage naturel. Utilise les outils du plugin `hermes-plugin-gen` pour scafolder la structure complète.

## Quand l'utiliser

- L'utilisateur dit "crée un plugin qui fait X"
- L'utilisateur dit "ajoute un outil Y à mon plugin Z"
- L'utilisateur veut bundle une skill avec son plugin
- Tu dois créer un nouveau plugin Hermes bien structuré

## Procédure

### Créer un nouveau plugin

1. **Comprendre le besoin** — pose les questions clés :
   - Quels outils le plugin expose-t-il ?
   - Quels paramètres chaque outil prend-il ?
   - A-t-il besoin de variables d'environnement (API keys) ?
   - Doit-il avoir des hooks lifecycle ?
   - Faut-il une skill embarquée ?

2. **Appeler `plugin_scaffold`** avec les infos collectées :
   - `name` : nom du plugin (en minuscules, tirets)
   - `description` : une ligne
   - `tools` : liste des outils avec leurs paramètres
   - `requires_env` : si besoin d'API keys
   - `with_skill` : true si skill embarquée souhaitée

3. **Vérifier la sortie** :
   - Tous les fichiers sont créés dans `~/.hermes/plugins/<name>/`
   - Les schemas sont bien formatés
   - Les handlers ont des TODO à remplacer

4. **Compléter l'implémentation** :
   - Remplir la vraie logique dans `tools.py`
   - Améliorer les descriptions dans `schemas.py`
   - Tester avec `hermes plugins enable <name>` puis un redémarrage

5. **Proposer à l'utilisateur** : "Ton plugin est prêt, je peux :
   - L'activer maintenant
   - Y ajouter d'autres outils
   - Le publier sur GitHub"

### Ajouter un outil à un plugin existant

1. Appelle `plugin_add_tool` avec le nom du plugin et la description du nouvel outil
2. Vérifie que les fichiers ont bien été modifiés
3. Complète l'implémentation du handler dans `tools.py`

### Bundler une skill avec un plugin

1. Appelle `plugin_add_skill` avec le nom du plugin et le contenu SKILL.md
2. Vérifie que `__init__.py` a bien le registre des skills

## Pitfalls

- **plugin_scaffold refuse d'écraser** un plugin existant — supprime-le manuellement ou change de nom
- **Les handlers générés contiennent des TODO** — toujours les compléter avant d'activer le plugin
- **plugin_add_tool** modifie les fichiers existants mais ne change pas les TODO déjà présents
- **Les noms de plugins** doivent être en minuscules avec tirets (max 64 chars)
- **Toujours demander** les API keys nécessaires avant de générer — ne pas deviner
- Après `plugin_add_tool`, vérifie que l'indentation du `__init__.py` est correcte

## Exemple

Utilisateur : "crée un plugin qui check les prix du Bitcoin"

```json
{
  "name": "bitcoin-price",
  "description": "Check le prix du Bitcoin et envoie des alertes Telegram",
  "tools": [
    {
      "name": "get_btc_price",
      "description": "Récupère le prix actuel du BTC en USD",
      "params": []
    },
    {
      "name": "set_alert",
      "description": "Configure une alerte de prix",
      "params": [
        {"name": "target_price", "type": "number", "description": "Prix cible en USD", "required": true}
      ]
    }
  ],
  "requires_env": [
    {"name": "COINBASE_API_KEY", "description": "Clé API Coinbase"}
  ]
}
```

1. Appelle `plugin_scaffold` avec ces données
2. Va dans `~/.hermes/plugins/bitcoin-price/tools.py` et complète l'implémentation
3. Dis à l'utilisateur : "Plugin créé ! J'ai besoin que tu configures COINBASE_API_KEY dans .env, ensuite on active avec `hermes plugins enable bitcoin-price`"
