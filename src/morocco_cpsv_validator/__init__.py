"""
Morocco CPSV Validator Package
Official European Commission SEMIC CPSV-AP 3.2.0 SHACL Validator for Moroccan Public Services.
"""

from .validator import MoroccoCPSVValidator, ValidationResult, validate_rdf

__all__ = ["MoroccoCPSVValidator", "ValidationResult", "validate_rdf"]
