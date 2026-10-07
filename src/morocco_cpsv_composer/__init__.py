"""
Morocco CPSV Composer Package
=============================
Authoring, registry management, and CPSV-AP 3.2.0 RDF graph builder
for Moroccan public services.
"""

from .registry import MoroccoRegistry
from .builder import ProcedureComposer

__all__ = ["MoroccoRegistry", "ProcedureComposer"]
