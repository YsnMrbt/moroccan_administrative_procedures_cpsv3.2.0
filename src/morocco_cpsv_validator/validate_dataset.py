#!/usr/bin/env python3
"""
Official CPSV-AP 3.2.0 SHACL Dataset Validator
Validates Turtle (.ttl) or RDF/XML (.rdf) against official SEMIC shapes.
"""

import os
import sys
import time
import argparse
from rdflib import Graph
import pyshacl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_TTL = os.path.join(BASE_DIR, "output", "procedures_administratives_cpsv.ttl")
LOCAL_SHAPES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "official_cpsv_ap_3.2.0_shapes.ttl")
LEGACY_SHAPES = os.path.join(BASE_DIR, "src", "validation", "official_cpsv_ap_3.2.0_shapes.ttl")
DEFAULT_SHAPES = LOCAL_SHAPES if os.path.exists(LOCAL_SHAPES) else LEGACY_SHAPES

def validate_file(file_path, shapes_path=DEFAULT_SHAPES):
    if not os.path.exists(file_path):
        print(f"Error: Target file not found: {file_path}")
        return False
    if not os.path.exists(shapes_path):
        print(f"Error: Shapes file not found: {shapes_path}")
        return False

    fmt = "xml" if file_path.endswith(".rdf") or file_path.endswith(".xml") else "turtle"
    print(f"1. Loading data graph: {file_path} (format: {fmt})...")
    t0 = time.time()
    g = Graph()
    g.parse(file_path, format=fmt)
    t1 = time.time()
    print(f"   Parsed {len(g)} triples in {t1 - t0:.2f}s.")

    print(f"2. Validating against official SHACL shapes: {os.path.basename(shapes_path)}...")
    t2 = time.time()
    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=g,
        shacl_graph=shapes_path,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True
    )
    t3 = time.time()
    print(f"   Validation finished in {t3 - t2:.2f}s.")

    print("\n" + "=" * 40)
    print(f"CONFORMANCE STATUS: {'PASS (Conforms)' if conforms else 'FAIL (Non-conforming)'}")
    print("=" * 40)

    violations = results_text.count("Constraint Violation")
    print(f"Total Constraint Violations: {violations}\n")
    if not conforms:
        print(results_text[:2000])
    return conforms

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CPSV-AP 3.2.0 SHACL Validator")
    parser.add_argument("file", nargs="?", default=DEFAULT_TTL, help="Path to RDF file (.ttl or .rdf)")
    parser.add_argument("--shapes", default=DEFAULT_SHAPES, help="Path to SHACL shapes file")
    args = parser.parse_args()

    success = validate_file(args.file, args.shapes)
    sys.exit(0 if success else 1)
