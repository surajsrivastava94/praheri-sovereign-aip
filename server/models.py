"""Pydantic request bodies for the governance endpoints.

Lives in server/ — the engine stays frozen. Role is a demo control (analyst|mlro);
the server builds a governance.Actor from it and lets governance enforce the gate.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    role: str = "analyst"
    params: dict[str, Any] = Field(default_factory=dict)


class ApproveRequest(BaseModel):
    role: str = "mlro"
