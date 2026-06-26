from __future__ import annotations

__all__ = ["AgentCompanyRegistry", "AgentLoop", "AgentRoleSpec", "SessionIndex", "ToolRegistry", "build_default_agent_company", "build_runtime"]


def build_runtime(*args, **kwargs):
    from .loop import build_runtime as _build_runtime

    return _build_runtime(*args, **kwargs)


def __getattr__(name):
    if name == "AgentCompanyRegistry":
        from .agent_company import AgentCompanyRegistry

        return AgentCompanyRegistry
    if name == "AgentRoleSpec":
        from .agent_company import AgentRoleSpec

        return AgentRoleSpec
    if name == "build_default_agent_company":
        from .agent_company import build_default_agent_company

        return build_default_agent_company
    if name == "AgentLoop":
        from .loop import AgentLoop

        return AgentLoop
    if name == "SessionIndex":
        from .session_index import SessionIndex

        return SessionIndex
    if name == "ToolRegistry":
        from .tools import ToolRegistry

        return ToolRegistry
    raise AttributeError(name)
