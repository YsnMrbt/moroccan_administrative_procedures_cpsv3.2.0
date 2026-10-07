#!/usr/bin/env python3
"""
Morocco CPSV-AP 3.2.0 - Complete Dataset Distribution Synchronizer
==================================================================
Ensures the SQLite database (src/procedures_administratives_cpsv.db) remains the authoritative
single source of truth and exports 100% synchronized, clean, SHACL-compliant
distributions in Turtle (.ttl) and RDF/XML (.rdf) formats for:
  The Master National Catalog (output/procedures_administratives_cpsv.ttl, output/procedures_administratives_cpsv.rdf)
"""

import os
import sys
import sqlite3
import hashlib
from collections import defaultdict
from xml.sax.saxutils import escape

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DB_PATH = os.path.join(SRC_DIR, "procedures_administratives_cpsv.db")

MASTER_TTL = os.path.join(OUTPUT_DIR, "procedures_administratives_cpsv.ttl")
MASTER_RDF = os.path.join(OUTPUT_DIR, "procedures_administratives_cpsv.rdf")

PREFIXES = {
    "cpsv": "http://purl.org/vocab/cpsv#",
    "cv": "http://data.europa.eu/m8g/",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "schema": "http://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "org": "http://www.w3.org/ns/org#",
    "procedures_administratives_cpsv": "http://procedures_administratives_cpsv.ma/id/"
}

def sync_master_distributions():
    """Generates clean output/procedures_administratives_cpsv.ttl and output/procedures_administratives_cpsv.rdf from SQLite v_rdf_triples view."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure v_rdf_triples view is present
    sql_views_path = os.path.join(SRC_DIR, "sql", "03_rdf_views.sql")
    if os.path.exists(sql_views_path):
        with open(sql_views_path, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        conn.commit()

    print("1. Extracting active RDF triples from v_rdf_triples...")
    cursor.execute("SELECT subject, predicate, object, is_literal, datatype, lang FROM v_rdf_triples")
    triples = cursor.fetchall()
    print(f"   Extracted {len(triples):,} active triples from SQLite database.")

    # 1. Write clean Turtle
    print(f"2. Writing clean Master Turtle: {MASTER_TTL}...")
    with open(MASTER_TTL, 'w', encoding='utf-8') as ttl_file:
        for p_prefix, p_uri in PREFIXES.items():
            ttl_file.write(f"@prefix {p_prefix}: <{p_uri}> .\n")
        ttl_file.write("\n")

        for s, p, o, is_lit, dt, lang in triples:
            s_fmt = f"<{s}>"
            p_fmt = f"<{p}>"
            if is_lit:
                o_escaped = str(o).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                if lang:
                    o_fmt = f'"{o_escaped}"@{lang}'
                elif dt:
                    o_fmt = f'"{o_escaped}"^^<{dt}>'
                else:
                    o_fmt = f'"{o_escaped}"'
            else:
                o_fmt = f"<{o}>"
            ttl_file.write(f"{s_fmt} {p_fmt} {o_fmt} .\n")

    # 2. Write clean RDF/XML
    print(f"3. Writing clean Master RDF/XML: {MASTER_RDF}...")
    with open(MASTER_RDF, 'w', encoding='utf-8') as rdf_file:
        rdf_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        rdf_file.write('<rdf:RDF\n')
        rdf_file.write('   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n')
        rdf_file.write('   xmlns:cpsv="http://purl.org/vocab/cpsv#"\n')
        rdf_file.write('   xmlns:cv="http://data.europa.eu/m8g/"\n')
        rdf_file.write('   xmlns:dct="http://purl.org/dc/terms/"\n')
        rdf_file.write('   xmlns:foaf="http://xmlns.com/foaf/0.1/"\n')
        rdf_file.write('   xmlns:schema="http://schema.org/"\n')
        rdf_file.write('   xmlns:skos="http://www.w3.org/2004/02/skos/core#"\n')
        rdf_file.write('   xmlns:org="http://www.w3.org/ns/org#"\n')
        rdf_file.write('   xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"\n')
        rdf_file.write('   xmlns:procedures_administratives_cpsv="http://procedures_administratives_cpsv.ma/id/">\n\n')

        grouped = defaultdict(list)
        for s, p, o, is_lit, dt, lang in triples:
            grouped[s].append((p, o, is_lit, dt, lang))

        for s, p_list in grouped.items():
            rdf_file.write(f'  <rdf:Description rdf:about="{escape(s)}">\n')
            for p, o, is_lit, dt, lang in p_list:
                p_qname = p
                for prefix_name, prefix_uri in PREFIXES.items():
                    if p.startswith(prefix_uri):
                        p_qname = f"{prefix_name}:{p[len(prefix_uri):]}"
                        break
                if p == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                    p_qname = "rdf:type"

                if is_lit:
                    attrs = ""
                    if lang:
                        attrs += f' xml:lang="{lang}"'
                    if dt:
                        attrs += f' rdf:datatype="{escape(dt)}"'
                    rdf_file.write(f'    <{p_qname}{attrs}>{escape(str(o))}</{p_qname}>\n')
                else:
                    if p == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                        rdf_file.write(f'    <rdf:type rdf:resource="{escape(str(o))}"/>\n')
                    else:
                        rdf_file.write(f'    <{p_qname} rdf:resource="{escape(str(o))}"/>\n')
            rdf_file.write('  </rdf:Description>\n\n')

        rdf_file.write('</rdf:RDF>\n')

    conn.close()
    print("Master distributions synchronized successfully.")

def sync_curated_scenarios_from_db():
    """No-op kept for backwards compatibility."""
    pass

if __name__ == "__main__":
    sync_master_distributions()
