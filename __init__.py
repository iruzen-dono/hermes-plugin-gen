"""
Hermes Plugin Generator — Registration.
Wires schemas to handlers.
"""

from . import schemas, tools


def register(ctx):
    """Wire schemas to handlers and register tools."""
    ctx.register_tool(
        name="plugin_scaffold",
        toolset="hermes-plugin-gen",
        schema=schemas.PLUGIN_SCAFFOLD,
        handler=tools.plugin_scaffold,
    )
    ctx.register_tool(
        name="plugin_add_tool",
        toolset="hermes-plugin-gen",
        schema=schemas.PLUGIN_ADD_TOOL,
        handler=tools.plugin_add_tool,
    )
    ctx.register_tool(
        name="plugin_add_skill",
        toolset="hermes-plugin-gen",
        schema=schemas.PLUGIN_ADD_SKILL,
        handler=tools.plugin_add_skill,
    )
