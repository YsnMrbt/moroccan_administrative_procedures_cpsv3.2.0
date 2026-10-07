#!/usr/bin/env python3
"""
Morocco CPSV-AP 3.2.0 SHACL Validator Engine
============================================
Validates RDF instances (Turtle or RDF/XML) against the official
European Commission SEMIC CPSV-AP 3.2.0 SHACL shapes specification.
"""

import os
import sys
import time
import argparse
from typing import Optional, List, Dict, Any, Union
from rdflib import Graph, Namespace, RDF
import pyshacl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL_SHAPES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "official_cpsv_ap_3.2.0_shapes.ttl")
LEGACY_SHAPES = os.path.join(BASE_DIR, "src", "validation", "official_cpsv_ap_3.2.0_shapes.ttl")
DEFAULT_SHAPES_PATH = LOCAL_SHAPES if os.path.exists(LOCAL_SHAPES) else LEGACY_SHAPES

# Standard SHACL Namespaces
SH = Namespace("http://www.w3.org/ns/shacl#")

class ValidationResult:
    """Represents structured results from a SHACL validation execution."""
    def __init__(self, conforms: bool, violations_count: int, raw_text: str, violations: List[Dict[str, Any]], execution_time: float):
        self.conforms = conforms
        self.violations_count = violations_count
        self.raw_text = raw_text
        self.violations = violations
        self.execution_time = execution_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conforms": self.conforms,
            "violations_count": self.violations_count,
            "execution_time_seconds": round(self.execution_time, 3),
            "violations": self.violations,
            "status": "PASS" if self.conforms else "FAIL"
        }

    def __repr__(self) -> str:
        status = "CONFORMING (PASS)" if self.conforms else f"NON-CONFORMING ({self.violations_count} VIOLATIONS)"
        return f"<ValidationResult status={status} time={self.execution_time:.2f}s>"


class MoroccoCPSVValidator:
    """
    High-performance, local SHACL validator for Moroccan Public Services.
    Enforces official SEMIC CPSV-AP 3.2.0 specifications.
    """
    def __init__(self, shapes_path: str = DEFAULT_SHAPES_PATH):
        self.shapes_path = shapes_path
        if not os.path.exists(self.shapes_path):
            raise FileNotFoundError(f"SHACL shapes file not found: {self.shapes_path}")
        
        # Pre-load shapes graph into memory for ultra-fast repeated validation
        self._shapes_graph: Optional[Graph] = None

    def _get_shapes_graph(self) -> Graph:
        if self._shapes_graph is None:
            g = Graph()
            g.parse(self.shapes_path, format="turtle")
            self._shapes_graph = g
        return self._shapes_graph

    def validate(self, rdf_input: Union[str, Graph], rdf_format: str = "turtle") -> ValidationResult:
        """
        Validate an RDF string, file path, or rdflib.Graph against the CPSV-AP 3.2.0 shapes.
        
        :param rdf_input: File path (str), raw RDF string (str), or rdflib Graph object.
        :param rdf_format: 'turtle', 'xml' (rdf/xml), or 'json-ld'.
        :return: ValidationResult object.
        """
        t0 = time.time()
        
        # Load candidate data graph
        if isinstance(rdf_input, Graph):
            data_graph = rdf_input
        elif isinstance(rdf_input, str):
            data_graph = Graph()
            if os.path.isfile(rdf_input):
                fmt = "xml" if rdf_input.endswith((".rdf", ".xml")) else "turtle"
                data_graph.parse(rdf_input, format=fmt)
            else:
                data_graph.parse(data=rdf_input, format=rdf_format)
        else:
            raise TypeError("rdf_input must be a file path, RDF string, or rdflib.Graph")

        # Execute SHACL validation with RDFS inference enabled
        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=data_graph,
            shacl_graph=self.shapes_path,
            inference="rdfs",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True
        )
        elapsed = time.time() - t0

        # Parse detailed violations from results_graph
        violations = []
        if not conforms and results_graph is not None:
            for report in results_graph.subjects(RDF.type, SH.ValidationReport):
                for result in results_graph.objects(report, SH.result):
                    focus_node = results_graph.value(result, SH.focusNode)
                    result_path = results_graph.value(result, SH.resultPath)
                    message = results_graph.value(result, SH.resultMessage)
                    severity = results_graph.value(result, SH.resultSeverity)
                    source_constraint = results_graph.value(result, SH.sourceConstraintComponent)

                    violations.append({
                        "focus_node": str(focus_node) if focus_node else "Unknown",
                        "path": str(result_path) if result_path else "Unknown",
                        "message": str(message) if message else "Constraint violation",
                        "severity": str(severity).split("#")[-1] if severity else "Violation",
                        "constraint": str(source_constraint).split("#")[-1] if source_constraint else "Unknown"
                    })

        violations_count = len(violations) if not conforms else 0
        return ValidationResult(
            conforms=conforms,
            violations_count=violations_count,
            raw_text=results_text,
            violations=violations,
            execution_time=elapsed
        )


def validate_rdf(rdf_input: Union[str, Graph], rdf_format: str = "turtle") -> ValidationResult:
    """Convenience helper function to run validation."""
    validator = MoroccoCPSVValidator()
    return validator.validate(rdf_input, rdf_format=rdf_format)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Morocco CPSV-AP 3.2.0 SHACL Validator")
    parser.add_argument("target", help="Path to RDF file or Turtle snippet to validate")
    parser.add_argument("--shapes", default=DEFAULT_SHAPES_PATH, help="Path to custom SHACL shapes file")
    args = parser.parse_args()

    validator = MoroccoCPSVValidator(shapes_path=args.shapes)
    print(f"Validating {args.target} against official SEMIC shapes...")
    res = validator.validate(args.target)

    print("\n" + "=" * 55)
    print(f"RESULT: {'PASS (Conforms)' if res.conforms else 'FAIL (Non-conforming)'}")
    print(f"Violations: {res.violations_count} | Duration: {res.execution_time:.2f}s")
    print("=" * 55)

    if not res.conforms:
        for idx, v in enumerate(res.violations, 1):
            print(f"\n[{idx}] Focus Node: {v['focus_node']}")
            print(f"    Path:       {v['path']}")
            print(f"    Message:    {v['message']}")
            print(f"    Constraint: {v['constraint']}")
        sys.exit(1)
    else:
        print("Dataset is 100% compliant with CPSV-AP 3.2.0 European standards.")
        sys.exit(0)
