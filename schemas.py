"""Tool schemas for hermes-plugin-gen — what the LLM sees."""

PLUGIN_SCAFFOLD = {
    "name": "plugin_scaffold",
    "description": (
        "Create a complete Hermes Agent plugin from a description. "
        "Generates plugin.yaml, __init__.py, schemas.py, tools.py, "
        "and optionally env vars, hooks, and a bundled skill. "
        "Outputs paths of all created files. "
        "Use this when the user asks to create a new Hermes plugin "
        "from a natural language description."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Plugin name (lowercase, hyphens, e.g. 'my-weather')",
            },
            "description": {
                "type": "string",
                "description": "One-line description of what the plugin does",
            },
            "tools": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Tool name (snake_case)"},
                        "description": {"type": "string", "description": "What the tool does"},
                        "params": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string", "enum": ["string", "number", "boolean", "array", "object"]},
                                    "description": {"type": "string"},
                                    "required": {"type": "boolean"},
                                },
                                "required": ["name", "type", "description"],
                            },
                            "description": "List of parameters the tool accepts",
                        },
                    },
                    "required": ["name", "description"],
                },
                "description": "List of tools the plugin provides",
            },
            "requires_env": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
                "description": "Optional env vars the plugin needs (API keys, etc.)",
            },
            "has_hooks": {
                "type": "boolean",
                "description": "Whether the plugin needs lifecycle hooks (pre/post tool call)",
            },
            "with_skill": {
                "type": "boolean",
                "description": "Whether to bundle a skill with the plugin",
            },
            "author": {
                "type": "string",
                "description": "Author name (default: auto)",
            },
        },
        "required": ["name", "description", "tools"],
    },
}

PLUGIN_ADD_TOOL = {
    "name": "plugin_add_tool",
    "description": (
        "Add a new tool to an existing Hermes plugin. "
        "Updates plugin.yaml, schemas.py, tools.py, and __init__.py. "
        "Returns paths of all modified files."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "plugin_name": {
                "type": "string",
                "description": "Name of the existing plugin to modify",
            },
            "name": {
                "type": "string",
                "description": "New tool name (snake_case)",
            },
            "description": {
                "type": "string",
                "description": "What the tool does",
            },
            "params": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["string", "number", "boolean", "array", "object"]},
                        "description": {"type": "string"},
                        "required": {"type": "boolean"},
                    },
                    "required": ["name", "type", "description"],
                },
                "description": "Parameters the tool accepts",
            },
        },
        "required": ["plugin_name", "name", "description"],
    },
}

PLUGIN_ADD_SKILL = {
    "name": "plugin_add_skill",
    "description": (
        "Bundle a skill with an existing Hermes plugin. "
        "Creates the skills/<name>/SKILL.md and registers it in __init__.py."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "plugin_name": {
                "type": "string",
                "description": "Name of the existing plugin",
            },
            "skill_name": {
                "type": "string",
                "description": "Skill name (lowercase, hyphens)",
            },
            "skill_description": {
                "type": "string",
                "description": "One-line description (max 60 chars)",
            },
            "skill_content": {
                "type": "string",
                "description": "Full SKILL.md markdown content (YAML frontmatter + body)",
            },
        },
        "required": ["plugin_name", "skill_name", "skill_description", "skill_content"],
    },
}
