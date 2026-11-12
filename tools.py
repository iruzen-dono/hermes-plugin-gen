"""
Hermes Plugin Generator — Tool handlers.
Scaffolds, extends, and patches Hermes plugins.

Generates production-quality Hermes plugin code matching the
official conventions documented at:
  https://hermes-agent.nousresearch.com/docs/guides/build-a-hermes-plugin
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Templates ──────────────────────────────────────────────────────────────

PLUGIN_YAML_TPL = """\
name: {name}
kind: standalone
version: 0.1.0
description: "{description}"
author: {author}{env_block}
provides_tools:
{tools_list}
"""

INIT_PY_TPL = """\
\"\"\"{name} plugin — {description}\"\"\"

from pathlib import Path

from . import schemas, tools


def register(ctx):
{tools_registration}{hooks_block}{skill_block}
"""

SCHEMAS_PY_TPL = """\
\"\"\"Tool schemas for {name} plugin.\"\"\"

{schema_defs}
"""

TOOLS_PY_TPL = """\
\"\"\"Tool handlers for {name} plugin.\"\"\"

import json
import logging
import os

logger = logging.getLogger(__name__)

{check_fn_block}

{tool_fns}
"""

TOOL_FN_TPL = """\
def {fn_name}(args: dict, **kwargs) -> str:
    \"\"\"{description}\"\"\"
    {params_extract}

    try:
        # TODO: implement {name}
        # {hint}
        result = {{"status": "ok", "tool": "{name}"}}
        return json.dumps(result)
    except Exception as e:
        logger.exception("{name} failed")
        return json.dumps({{"error": str(e)}})

"""

CHECK_FN_TPL = """\
def check_requirements() -> bool:
    \"\"\"Check if required env vars are set.\"\"\"
    return all(os.getenv(var) for var in _REQUIRED_ENV_VARS)


_REQUIRED_ENV_VARS = [{env_vars_list}]

"""

SCHEMA_TPL = """\
{schema_var} = {{
    "name": "{name}",
    "description": "{description}",
    "parameters": {{
        "type": "object",
        "properties": {{
{params_block}
        }},
        "required": [{required_list}],
    }},
}}
"""

SKILL_MD_TPL = """\
---
name: {name}
description: "{description}"
version: 0.1.0
author: {author}
---

# {label} Skill

## When to Use

Use this skill when working with the {name} plugin.

## Procedure

Refer to the plugin's tool descriptions and follow standard practices.

## Prerequisites

- The `{name}` plugin must be enabled: `hermes plugins enable {name}`
"""


# ── Utility functions ──────────────────────────────────────────────────────

def _normalize_name(raw: str) -> str:
    """Normalize plugin/tool name to lowercase-hyphen."""
    return raw.strip().lower().replace(" ", "-").replace("_", "-")


def _snake(name: str) -> str:
    """Convert to snake_case."""
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _pascal(name: str) -> str:
    """Convert to PascalCase."""
    return "".join(w.capitalize() for w in name.replace("-", " ").replace("_", " ").split())


def _ensure_skill_frontmatter(content: str, name: str, description: str) -> str:
    """Make sure the SKILL.md carries `name` and `description` in its frontmatter.

    ``plugin_add_skill`` declares ``skill_description`` as a required parameter,
    so a description the caller sent must actually reach the written file.
    Existing frontmatter is preserved; keys already present are left untouched.
    """
    if not description:
        return content

    description_line = f"description: {json.dumps(description)}"

    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end == -1:
            # Opening fence never closed: the file is already malformed, and
            # stacking a second frontmatter on top would make it worse.
            return content
        frontmatter = content[3:end]
        if "description:" in frontmatter:
            return content
        extra = ""
        if "name:" not in frontmatter:
            extra += f"\nname: {json.dumps(name)}"
        extra += f"\n{description_line}"
        return "---" + frontmatter.rstrip() + extra + content[end:]

    return f'---\nname: {json.dumps(name)}\n{description_line}\n---\n\n{content}'


def _guess_emoji(name: str) -> str:
    """Guess a reasonable emoji for a tool based on its name."""
    emoji_map = {
        "search": "🔍", "find": "🔍", "lookup": "📖",
        "get": "📥", "fetch": "📥", "retrieve": "📥", "download": "⬇️",
        "create": "➕", "make": "🛠️", "build": "🏗️", "generate": "⚡",
        "update": "📝", "edit": "✏️", "patch": "🔧", "modify": "✏️",
        "delete": "🗑️", "remove": "🗑️", "clean": "🧹",
        "send": "📤", "push": "📤", "upload": "⬆️",
        "list": "📋", "show": "👁️", "status": "📊", "info": "ℹ️",
        "run": "▶️", "execute": "▶️", "start": "🚀", "stop": "⏹️",
        "check": "✅", "verify": "✅", "validate": "✅", "test": "🧪",
        "convert": "🔄", "transform": "🔄", "parse": "📄",
        "analyze": "📊", "scan": "🔬", "inspect": "🔎",
        "chat": "💬", "ask": "🤔", "summarize": "📝",
        "ping": "🏓", "echo": "🔊", "hello": "👋",
        "config": "⚙️", "settings": "⚙️", "setup": "🔧",
        "alert": "🔔", "notify": "🔔", "watch": "👀",
        "export": "📤", "import": "📥", "sync": "🔄",
        "lock": "🔒", "unlock": "🔓", "auth": "🔑",
        "weather": "🌤️", "time": "🕐", "date": "📅",
        "calc": "🧮", "math": "🧮",
        "help": "❓", "guide": "📖",
    }
    for key, emoji in emoji_map.items():
        if key in name.lower():
            return emoji
    return "🔧"  # default: wrench


def _get_plugins_dir() -> Path:
    """Get user plugins directory (profile-aware)."""
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    return hermes_home / "plugins"


def _resolve_plugin_path(name: str) -> Path | None:
    """Find a plugin directory by name."""
    plugins_dir = _get_plugins_dir()
    for candidate in [name, _normalize_name(name)]:
        p = plugins_dir / candidate
        if p.exists() and (p / "plugin.yaml").exists():
            return p
    return None


def _make_env_block(requires_env: list[dict]) -> str:
    """Build the requires_env section for plugin.yaml with proper format."""
    if not requires_env:
        return ""
    lines = ["", "requires_env:"]
    for ev in requires_env:
        ev_name = ev.get("name", "").strip()
        ev_desc = ev.get("description", ev_name)
        has_secret = any(
            kw in ev_name.lower() for kw in ["key", "token", "secret", "password", "api_key", "apikey"]
        )
        lines.append(f'  - name: {ev_name}')
        lines.append(f'    description: "{ev_desc}"')
        lines.append(f'    prompt: "{ev_desc}"')
        lines.append(f'    password: {"true" if has_secret else "false"}')
    return "\n".join(lines)


def _make_tools_list(tools: list[dict]) -> str:
    """Build the provides_tools list for plugin.yaml."""
    return "\n".join(f"  - {_normalize_name(t['name'])}" for t in tools)


def _make_check_fn_block(requires_env: list[dict]) -> tuple[str, list[str], list[str]]:
    """
    Generate check_fn block based on requires_env entries.
    Returns (check_fn_code_block, required_env_vars, tool_names_with_env).
    All tools get the same check_fn when env vars are required.
    """
    if not requires_env:
        return "", [], []

    env_var_names = [ev["name"] for ev in requires_env if ev.get("name")]
    if not env_var_names:
        return "", [], []

    env_vars_list = ", ".join(f'"{v}"' for v in env_var_names)
    code = CHECK_FN_TPL.format(env_vars_list=env_vars_list)
    return code, env_var_names, []  # all tools share the check_fn


def _make_register_tool_lines(tools: list[dict], has_env_vars: bool,
                               env_tool_names: list[str]) -> str:
    """Generate the register_tool() calls with proper params. No leading indent — caller applies it."""
    lines = []
    for t in tools:
        t_name = _snake(t["name"])
        norm_name = _normalize_name(t["name"])
        var_name = t_name.upper()
        emoji = _guess_emoji(t_name)
        desc = t.get("description", "").replace('"', "'")

        has_check = has_env_vars  # all tools share check_requirements when env vars exist
        lines.append('ctx.register_tool(')
        lines.append(f'    name="{norm_name}",')
        lines.append(f'    toolset="{norm_name.split("-")[0] if "-" in norm_name else norm_name}",')
        lines.append(f'    schema=schemas.{var_name},')
        lines.append(f'    handler=tools.{t_name},')
        if has_check:
            lines.append('    check_fn=tools.check_requirements,')
        lines.append(f'    description="{desc}",')
        lines.append(f'    emoji="{emoji}",')
        lines.append('    is_async=False,')
        lines.append(')')
    return "\n".join(lines)


# ── Tool handlers (plugin generator's own tools) ──────────────────────────

def plugin_scaffold(args: dict, **kwargs) -> str:
    """Create a complete plugin directory from description."""
    try:
        name = _normalize_name(args.get("name", ""))
        if not name:
            return json.dumps({"error": "Plugin name is required"})
        if len(name) > 64:
            return json.dumps({"error": "Plugin name too long (max 64 chars)"})

        description = args.get("description", "")
        tools = args.get("tools", [])
        requires_env = args.get("requires_env", [])
        has_hooks = args.get("has_hooks", False)
        with_skill = args.get("with_skill", False)
        author = args.get("author", "Hermes Agent")

        plugins_dir = _get_plugins_dir()
        plugin_path = plugins_dir / name

        if plugin_path.exists():
            return json.dumps({
                "error": f"Plugin '{name}' already exists at {plugin_path}",
                "path": str(plugin_path),
            })

        plugin_path.mkdir(parents=True, exist_ok=True)
        created_files = []

        # ── 1. plugin.yaml ──
        plugin_yaml = PLUGIN_YAML_TPL.format(
            name=name,
            description=description,
            author=author,
            env_block=_make_env_block(requires_env),
            tools_list=_make_tools_list(tools),
        )
        (plugin_path / "plugin.yaml").write_text(plugin_yaml, encoding="utf-8")
        created_files.append(str(plugin_path / "plugin.yaml"))

        # ── 2. schemas.py ──
        schema_defs = []
        for t in tools:
            t_name = _snake(t["name"])
            var_name = t_name.upper()
            params = t.get("params", [])
            params_block = "\n".join(
                f'            "{p["name"]}": {{\n'
                f'                "type": "{p["type"]}",\n'
                f'                "description": "{p["description"]}",\n'
                f'            }},'
                for p in params
            )
            required_list = ", ".join(f'"{p["name"]}"' for p in params if p.get("required"))
            schema_defs.append(SCHEMA_TPL.format(
                schema_var=var_name,
                name=_normalize_name(t["name"]),
                description=t.get("description", ""),
                params_block=params_block,
                required_list=required_list,
            ))
        schemas_content = SCHEMAS_PY_TPL.format(
            name=name,
            schema_defs="\n".join(schema_defs),
        )
        (plugin_path / "schemas.py").write_text(schemas_content, encoding="utf-8")
        created_files.append(str(plugin_path / "schemas.py"))

        # ── 3. tools.py ──
        check_fn_code, env_vars, env_tool_names = _make_check_fn_block(requires_env)

        tool_fns = []
        for t in tools:
            t_name = _snake(t["name"])
            params = t.get("params", [])
            hint_parts = []
            if params:
                extracts = []
                for p in params:
                    pn = p["name"]
                    if p["type"] == "string":
                        extracts.append(f'{pn} = args.get("{pn}", "")')
                    else:
                        extracts.append(f'{pn} = args.get("{pn}", 0)')
                params_extract = "\n    ".join(extracts)
                hint_parts.append(f"Parameters: {', '.join(p['name'] for p in params)}")
            else:
                params_extract = "pass"
                hint_parts.append("No parameters")

            if t_name in env_tool_names:
                hint_parts.append("Requires env vars set")

            hint = " — ".join(hint_parts)

            tool_fns.append(TOOL_FN_TPL.format(
                fn_name=t_name,
                description=t.get("description", ""),
                name=t_name,
                params_extract=params_extract,
                hint=hint,
            ))

        tools_content = TOOLS_PY_TPL.format(
            name=name,
            check_fn_block=check_fn_code,
            tool_fns="".join(tool_fns),
        )
        (plugin_path / "tools.py").write_text(tools_content, encoding="utf-8")
        created_files.append(str(plugin_path / "tools.py"))

        # ── 4. __init__.py ──
        tools_reg = _make_register_tool_lines(tools, bool(env_vars), env_tool_names)
        tools_reg_indented = "\n".join(
            "    " + line if line.strip() else line
            for line in tools_reg.split("\n")
        )

        hooks_block = ""
        if has_hooks:
            hooks_block = """
    # Lifecycle hooks
    ctx.register_hook("pre_tool_call", tools.pre_tool_call_hook)
    ctx.register_hook("post_tool_call", tools.post_tool_call_hook)
"""

        skill_reg_block = ""
        if with_skill:
            skill_reg_block = """

    # Bundle skills
    skills_dir = Path(__file__).parent / "skills"
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)
"""

        init_content = INIT_PY_TPL.format(
            name=name,
            description=description,
            tools_registration=tools_reg_indented,
            hooks_block=hooks_block,
            skill_block=skill_reg_block,
        )
        (plugin_path / "__init__.py").write_text(init_content, encoding="utf-8")
        created_files.append(str(plugin_path / "__init__.py"))

        # ── 5. Skill (optional) ──
        if with_skill:
            skill_dir = plugin_path / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_md = SKILL_MD_TPL.format(
                name=name,
                description=description,
                author=author,
                label=_pascal(name),
            )
            (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
            created_files.append(str(skill_dir / "SKILL.md"))

        return json.dumps({
            "status": "created",
            "plugin_name": name,
            "path": str(plugin_path),
            "files": created_files,
            "tools": [_normalize_name(t["name"]) for t in tools],
            "kind": "standalone",
            "next_steps": (
                f"1. Enable the plugin: hermes plugins enable {name}\\n"
                f"2. Set env vars if any: edit $HERMES_HOME/.env\\n"
                f"3. Restart Hermes or start a new session\\n"
                f"4. Test: ask the agent to use your new tools"
            ),
        })
    except Exception as e:
        logger.exception("plugin_scaffold failed")
        return json.dumps({"error": f"Scaffold failed: {e!s}"})


def plugin_add_tool(args: dict, **kwargs) -> str:
    """Add a tool to an existing plugin."""
    try:
        plugin_name = _normalize_name(args.get("plugin_name", ""))
        tool_name = _snake(args.get("name", ""))
        tool_description = args.get("description", "")
        params = args.get("params", [])

        if not plugin_name or not tool_name:
            return json.dumps({"error": "plugin_name and name are required"})

        plugin_path = _resolve_plugin_path(plugin_name)
        if not plugin_path:
            return json.dumps({"error": f"Plugin '{plugin_name}' not found"})

        schemas_path = plugin_path / "schemas.py"
        tools_path = plugin_path / "tools.py"
        init_path = plugin_path / "__init__.py"
        yaml_path = plugin_path / "plugin.yaml"

        for p in [schemas_path, tools_path, init_path, yaml_path]:
            if not p.exists():
                return json.dumps({"error": f"Missing file: {p.name}"})

        # ── 1. Update schemas.py ──
        var_name = tool_name.upper()
        params_block = "\n".join(
            f'            "{p["name"]}": {{\n'
            f'                "type": "{p["type"]}",\n'
            f'                "description": "{p["description"]}",\n'
            f'            }},'
            for p in params
        )
        required_list = ", ".join(f'"{p["name"]}"' for p in params if p.get("required"))
        new_schema = SCHEMA_TPL.format(
            schema_var=var_name,
            name=_normalize_name(tool_name),
            description=tool_description,
            params_block=params_block,
            required_list=required_list,
        )

        existing_schemas = schemas_path.read_text(encoding="utf-8")
        if existing_schemas.rstrip().endswith('"""') and '"""' in existing_schemas.split("import")[-1] if "import" in existing_schemas else '"""' in existing_schemas:
            # Empty schemas (just docstring)
            insert_pos = existing_schemas.rfind('"""')
            if insert_pos > len(existing_schemas) // 2:
                # It's the closing docstring
                new_content = existing_schemas[:insert_pos] + "\n" + new_schema + '"""'
            else:
                new_content = existing_schemas.rstrip() + "\n\n" + new_schema
        else:
            new_content = existing_schemas.rstrip() + "\n\n" + new_schema
        schemas_path.write_text(new_content, encoding="utf-8")

        # ── 2. Update tools.py ──
        if params:
            p_lines = []
            for p in params:
                pn = p["name"]
                if p["type"] == "string":
                    p_lines.append(f'{pn} = args.get("{pn}", "")')
                else:
                    p_lines.append(f'{pn} = args.get("{pn}", 0)')
            params_extract = "\n    ".join(p_lines)
        else:
            params_extract = "pass"

        new_tool_fn = TOOL_FN_TPL.format(
            fn_name=tool_name,
            description=tool_description,
            name=tool_name,
            params_extract=params_extract,
            hint=f"Added via plugin_add_tool — parameters: {', '.join(p['name'] for p in params) if params else 'none'}",
        )
        existing_tools = tools_path.read_text(encoding="utf-8")
        tools_path.write_text(existing_tools.rstrip() + "\n\n" + new_tool_fn, encoding="utf-8")

        # ── 3. Update __init__.py ──
        norm_name = _normalize_name(tool_name)
        emoji = _guess_emoji(tool_name)
        desc_escaped = tool_description.replace('"', "'")
        reg_line = (
            f'    ctx.register_tool(\n'
            f'        name="{norm_name}",\n'
            f'        toolset="{plugin_name}",\n'
            f'        schema=schemas.{var_name},\n'
            f'        handler=tools.{tool_name},\n'
            f'        description="{desc_escaped}",\n'
            f'        emoji="{emoji}",\n'
            f'        is_async=False,\n'
            f'    )'
        )
        existing_init = init_path.read_text(encoding="utf-8")
        if "def register(ctx):" in existing_init:
            lines = existing_init.split("\n")
            insert_idx = None
            # Find last register_tool and insert after it
            for i in range(len(lines) - 1, -1, -1):
                stripped = lines[i].strip()
                if stripped == ")" and i > 0 and "register_tool" in lines[i-1]:
                    insert_idx = i + 1
                    break
            if insert_idx is None:
                for i, line in enumerate(lines):
                    if "def register(ctx):" in line:
                        insert_idx = i + 1
                        break
            if insert_idx is not None:
                lines.insert(insert_idx, reg_line)
                init_path.write_text("\n".join(lines), encoding="utf-8")

        # ── 4. Update plugin.yaml ──
        existing_yaml = yaml_path.read_text(encoding="utf-8")
        if f"  - {norm_name}" not in existing_yaml:
            if "provides_tools:" in existing_yaml:
                lines = existing_yaml.split("\n")
                for i, line in enumerate(lines):
                    if line.strip() == "provides_tools:":
                        lines.insert(i + 1, f"  - {norm_name}")
                        break
                yaml_path.write_text("\n".join(lines), encoding="utf-8")

        return json.dumps({
            "status": "tool_added",
            "plugin": plugin_name,
            "tool": norm_name,
            "files_modified": [str(schemas_path), str(tools_path), str(init_path)],
        })
    except Exception as e:
        logger.exception("plugin_add_tool failed")
        return json.dumps({"error": f"Add tool failed: {e!s}"})


def plugin_add_skill(args: dict, **kwargs) -> str:
    """Bundle a skill with an existing plugin."""
    try:
        plugin_name = _normalize_name(args.get("plugin_name", ""))
        skill_name = _normalize_name(args.get("skill_name", ""))
        skill_description = args.get("skill_description", "")
        skill_content = args.get("skill_content", "")

        if not plugin_name or not skill_name:
            return json.dumps({"error": "plugin_name and skill_name are required"})
        if not skill_content.strip():
            return json.dumps({"error": "skill_content is required"})

        plugin_path = _resolve_plugin_path(plugin_name)
        if not plugin_path:
            return json.dumps({"error": f"Plugin '{plugin_name}' not found"})

        # Create skill directory
        skill_dir = plugin_path / "skills" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_md = _ensure_skill_frontmatter(skill_content, skill_name, skill_description)
        skill_path.write_text(skill_md, encoding="utf-8")

        # Update __init__.py
        init_path = plugin_path / "__init__.py"
        init_content = init_path.read_text(encoding="utf-8")

        if "ctx.register_skill" not in init_content:
            skill_reg_code = (
                "\n\n    # Bundle skills\n"
                "    skills_dir = Path(__file__).parent / \"skills\"\n"
                "    for child in sorted(skills_dir.iterdir()):\n"
                "        skill_md = child / \"SKILL.md\"\n"
                "        if child.is_dir() and skill_md.exists():\n"
                "            ctx.register_skill(child.name, skill_md)\n"
            )
            init_content = init_content.rstrip() + skill_reg_code
            init_path.write_text(init_content, encoding="utf-8")

        # Update plugin.yaml
        yaml_path = plugin_path / "plugin.yaml"
        yaml_content = yaml_path.read_text(encoding="utf-8")
        if "provides_skills:" not in yaml_content:
            yaml_content = yaml_content.rstrip() + f"\nprovides_skills:\n  - {skill_name}\n"
            yaml_path.write_text(yaml_content, encoding="utf-8")

        return json.dumps({
            "status": "skill_added",
            "plugin": plugin_name,
            "skill": skill_name,
            "skill_path": str(skill_path),
        })
    except Exception as e:
        logger.exception("plugin_add_skill failed")
        return json.dumps({"error": f"Add skill failed: {e!s}"})
