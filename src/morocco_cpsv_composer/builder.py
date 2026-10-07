#!/usr/bin/env python3
"""
Morocco CPSV Procedure Builder & RDF Graph Generator
===================================================
Converts structured Moroccan administrative procedure definitions into
fully compliant European Commission SEMIC CPSV-AP 3.2.0 RDF graphs.
"""

import os
import hashlib
import sqlite3
from typing import Dict, Any, Optional, Tuple
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD

from .registry import MoroccoRegistry, generate_slug
from .id_policy import canonical_policy

# Standard Namespaces
CPSV = Namespace("http://purl.org/vocab/cpsv#")
CV = Namespace("http://data.europa.eu/m8g/")
DCT = Namespace("http://purl.org/dc/terms/")
ORG = Namespace("http://www.w3.org/ns/org#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
PACPSV = Namespace("http://procedures_administratives_cpsv.ma/id/")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "src", "procedures_administratives_cpsv.db")
OUTPUT_TTL = os.path.join(BASE_DIR, "output", "procedures_administratives_cpsv.ttl")
OUTPUT_RDF = os.path.join(BASE_DIR, "output", "procedures_administratives_cpsv.rdf")

class ProcedureComposer:
    """Composes and serializes individual or bulk procedures into CPSV-AP 3.2.0 RDF."""
    def __init__(self, registry: Optional[MoroccoRegistry] = None):
        self.registry = registry or MoroccoRegistry()

    def build_procedure_graph(self, data: Dict[str, Any]) -> Graph:
        """
        Build an rdflib.Graph for a single Moroccan public procedure
        enforcing all SEMIC CPSV-AP 3.2.0 guardrails and mandatory identifiers.
        """
        g = Graph()
        # Bind standard prefixes
        g.bind("cpsv", CPSV)
        g.bind("cv", CV)
        g.bind("dct", DCT)
        g.bind("org", ORG)
        g.bind("skos", SKOS)
        g.bind("procedures_administratives_cpsv", PACPSV)

        # -----------------------------------------------------------------
        # GUARDRAIL 1: European Commission Controlled Vocabulary Assertions
        # -----------------------------------------------------------------
        ara_uri = URIRef("http://publications.europa.eu/resource/authority/language/ARA")
        mar_uri = URIRef("http://publications.europa.eu/resource/authority/country/MAR")
        g.add((ara_uri, RDF.type, DCT.LinguisticSystem))
        g.add((mar_uri, RDF.type, DCT.Location))

        # Currency Guardrail
        currency_code = (data.get("cost", {}).get("currency") or "MAD").upper()
        curr_uri = URIRef(f"http://publications.europa.eu/resource/authority/currency/{currency_code}")
        g.add((curr_uri, RDF.type, SKOS.Concept))

        # -----------------------------------------------------------------
        # 2. Competent Authority
        # -----------------------------------------------------------------
        org_slug = data.get("authority_slug")
        org_name = data.get("authority_name")
        if not org_slug and org_name:
            matched = [a for a in self.registry.authorities if a["org_name"] == org_name]
            if matched:
                org_slug = matched[0]["org_slug"]
            else:
                new_org = self.registry.add_authority(org_name)
                org_slug = new_org["org_slug"]
        elif not org_slug:
            org_slug = "org_c8752c04661f" # fallback: الجماعة
            org_name = "الجماعة"

        org_uri = URIRef(f"http://procedures_administratives_cpsv.ma/id/organisation/{org_slug}")
        # GUARDRAIL 2: Dual-Typing and Required Labels for Competent Authorities
        g.add((org_uri, RDF.type, CV.PublicOrganisation))
        g.add((org_uri, RDF.type, ORG.Organization))
        g.add((org_uri, DCT.identifier, Literal(org_slug, datatype=XSD.string)))
        g.add((org_uri, SKOS.prefLabel, Literal(org_name, lang="ar")))
        g.add((org_uri, DCT.title, Literal(org_name, lang="ar")))
        g.add((org_uri, DCT.spatial, mar_uri))

        # -----------------------------------------------------------------
        # 3. Public Service Entity
        # -----------------------------------------------------------------
        title_ar = data.get("title_ar", "").strip() or "مسطرة إدارية"
        desc_ar = data.get("description_ar", "").strip() or "مسطرة إدارية تابعة للإدارة المغربية"
        ps_slug = data.get("service_slug") or generate_slug("ps_", title_ar)
        service_uri = URIRef(f"http://procedures_administratives_cpsv.ma/id/service/{ps_slug}")

        g.add((service_uri, RDF.type, CV.PublicService))
        g.add((service_uri, DCT.identifier, Literal(ps_slug, datatype=XSD.string)))
        g.add((service_uri, DCT.title, Literal(title_ar, lang="ar")))
        if data.get("title_fr"):
            g.add((service_uri, DCT.title, Literal(data["title_fr"].strip(), lang="fr")))

        g.add((service_uri, DCT.description, Literal(desc_ar, lang="ar")))
        g.add((service_uri, DCT.language, ara_uri))
        g.add((service_uri, DCT.spatial, mar_uri))
        g.add((service_uri, CV.hasCompetentAuthority, org_uri))

        if data.get("processing_time"):
            import re
            raw_pt = str(data["processing_time"]).strip()
            if re.match(r"^P\d+D$", raw_pt):
                pt_iso = raw_pt
            else:
                digits = re.findall(r"\d+", raw_pt)
                days = digits[0] if digits else "20"
                pt_iso = f"P{days}D"
            g.add((service_uri, CV.processingTime, Literal(pt_iso, datatype=XSD.duration)))

        # -----------------------------------------------------------------
        # 4. Cost / Fee Entity
        # -----------------------------------------------------------------
        cost_data = data.get("cost")
        if cost_data:
            cost_val = float(cost_data.get("value", 0.0))
            cost_desc = cost_data.get("description", "مجانية بدون رسوم" if cost_val == 0 else f"{cost_val} {currency_code}")
            cost_slug = generate_slug("cost_", f"{ps_slug}_{cost_val}_{currency_code}")
            cost_uri = URIRef(f"http://procedures_administratives_cpsv.ma/id/cost/{cost_slug}")

            g.add((cost_uri, RDF.type, CV.Cost))
            g.add((cost_uri, DCT.identifier, Literal(cost_slug, datatype=XSD.string)))
            g.add((cost_uri, CV.value, Literal(cost_val, datatype=XSD.double)))
            g.add((cost_uri, CV.hasValue, Literal(cost_val, datatype=XSD.double)))
            g.add((cost_uri, CV.currency, curr_uri))
            g.add((cost_uri, DCT.description, Literal(cost_desc, lang="ar")))
            g.add((cost_uri, CV.isDefinedBy, org_uri))

            g.add((service_uri, CV.hasCost, cost_uri))

        # -----------------------------------------------------------------
        # 5. Output / Deliverable Entity
        # -----------------------------------------------------------------
        outputs = data.get("outputs", [])
        if not outputs and data.get("output_title"):
            outputs = [data.get("output_title")]
        elif not outputs and data.get("output_name"):
            outputs = [data.get("output_name")]

        for out in outputs:
            out_title = out.get("title", "").strip() if isinstance(out, dict) else str(out).strip()
            if not out_title:
                continue
            out_slug = out.get("slug") if (isinstance(out, dict) and out.get("slug")) else generate_slug("out_", out_title)
            out_uri = URIRef(f"http://procedures_administratives_cpsv.ma/id/output/{out_slug}")

            g.add((out_uri, RDF.type, CV.Output))
            g.add((out_uri, DCT.identifier, Literal(out_slug, datatype=XSD.string)))
            g.add((out_uri, DCT.title, Literal(out_title, lang="ar")))
            g.add((out_uri, DCT.language, ara_uri))
            g.add((service_uri, CV.produces, out_uri))

        # -----------------------------------------------------------------
        # 6. Evidences / Required Documents
        # -----------------------------------------------------------------
        evidences = data.get("evidences", [])
        for ev in evidences:
            ev_title = ev.get("title", "").strip() if isinstance(ev, dict) else str(ev).strip()
            if not ev_title:
                continue
            ev_slug = ev.get("slug") if (isinstance(ev, dict) and ev.get("slug")) else generate_slug("id_", ev_title)
            ev_uri = URIRef(f"http://procedures_administratives_cpsv.ma/id/evidence/{ev_slug}")

            g.add((ev_uri, RDF.type, CV.Evidence))
            g.add((ev_uri, DCT.identifier, Literal(ev_slug, datatype=XSD.string)))
            g.add((ev_uri, DCT.title, Literal(ev_title, lang="ar")))
            g.add((ev_uri, DCT.language, ara_uri))
            g.add((service_uri, CV.hasInput, ev_uri))

        # -----------------------------------------------------------------
        # 7. Delivery Channels
        # -----------------------------------------------------------------
        channels = data.get("channels", [])
        if not channels:
            channels = [{"type": "counter", "name": "مكتب الاستقبال الإداري"}]

        for ch in channels:
            ch_name = ch.get("name", "شباك استقبال").strip()
            ch_slug = generate_slug("chan_", f"{ps_slug}_{ch_name}")
            ch_uri = URIRef(f"http://procedures_administratives_cpsv.ma/id/channel/{ch_slug}")

            g.add((ch_uri, RDF.type, CV.Channel))
            g.add((ch_uri, DCT.identifier, Literal(ch_slug, datatype=XSD.string)))
            g.add((ch_uri, CV.ownedBy, org_uri))
            if ch.get("url"):
                g.add((ch_uri, DCT.relation, URIRef(ch["url"])))
            g.add((service_uri, CV.hasChannel, ch_uri))

        return g

    def to_turtle(self, data: Dict[str, Any]) -> str:
        """Serializes the procedure to valid Turtle format."""
        g = self.build_procedure_graph(data)
        return g.serialize(format="turtle")

    def save_to_database_and_repo(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Saves the validated procedure into SQLite database and appends to output/procedures_administratives_cpsv.ttl
        without altering existing IDs, following the canonical ID policy and proper schema.
        """
        if not os.path.exists(DB_PATH):
            return False, f"Database not found at {DB_PATH}"

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            title_ar = data.get("title_ar", "").strip()
            desc_ar = data.get("description_ar", "").strip()
            org_slug = data.get("authority_slug")
            org_name = data.get("authority_name")
            cost_val = float(data.get("cost", {}).get("value", 0.0))
            proc_time = data.get("processing_time", "P20D")
            candidate_uuid = data.get("service_slug")

            # Resolve canonical UUID
            ps_uuid, _ = canonical_policy.resolve_procedure_uuid(title_ar, candidate_uuid)

            # Resolve authority
            org_id = 1
            if org_slug:
                cursor.execute("SELECT org_id FROM organisations WHERE org_slug = ?", (org_slug,))
                row = cursor.fetchone()
                if row:
                    org_id = row["org_id"]
            if org_id == 1 and org_name:
                cursor.execute("SELECT org_id FROM organisations WHERE org_name = ?", (org_name,))
                row = cursor.fetchone()
                if row:
                    org_id = row["org_id"]
                else:
                    new_slug, _ = canonical_policy.resolve_authority_slug(org_name)
                    cursor.execute("INSERT OR IGNORE INTO organisations (org_slug, org_name) VALUES (?, ?)", (new_slug, org_name))
                    org_id = cursor.lastrowid or 1

            # Resolve output
            output_title = data.get("output_title")
            output_id = None
            if output_title:
                cursor.execute("SELECT output_id FROM outputs WHERE output_title = ?", (output_title,))
                row = cursor.fetchone()
                if row:
                    output_id = row["output_id"]
                else:
                    out_slug = f"out_{abs(hash(output_title)) % 10000000}"
                    cursor.execute("INSERT OR IGNORE INTO outputs (output_slug, output_title) VALUES (?, ?)", (out_slug, output_title))
                    output_id = cursor.lastrowid

            # Check if procedure already exists
            cursor.execute("SELECT ps_id FROM public_services WHERE ps_uuid = ?", (ps_uuid,))
            existing = cursor.fetchone()
            if existing:
                ps_id = existing["ps_id"]
                cursor.execute("""
                    UPDATE public_services
                    SET procedure_name_raw = ?, procedure_name_cleaned = ?, description_cleaned = ?,
                        authority_id = ?, output_id = ?, fee_raw = ?, processing_time_raw = ?,
                        processing_time_iso = ?, url_source = ?
                    WHERE ps_id = ?
                """, (title_ar, title_ar, desc_ar, org_id, output_id, str(cost_val), proc_time, proc_time, f"http://procedures_administratives_cpsv.ma/id/service/{ps_uuid}", ps_id))
            else:
                cursor.execute("""
                    INSERT INTO public_services (
                        ps_uuid, procedure_name_raw, procedure_name_cleaned, description_cleaned,
                        authority_id, output_id, fee_raw, processing_time_raw, processing_time_iso, url_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ps_uuid, title_ar, title_ar, desc_ar, org_id, output_id, str(cost_val), proc_time, proc_time, f"http://procedures_administratives_cpsv.ma/id/service/{ps_uuid}"))
                ps_id = cursor.lastrowid

            # Save costs
            cost_slug = f"cost_{ps_uuid}"
            cursor.execute("DELETE FROM costs WHERE ps_id = ?", (ps_id,))
            cursor.execute("""
                INSERT INTO costs (cost_slug, ps_id, cost_value, currency, description_cleaned, defined_by_org_id)
                VALUES (?, ?, ?, 'http://publications.europa.eu/resource/authority/currency/MAD', ?, ?)
            """, (cost_slug, ps_id, cost_val, f"تكلفة المسطرة: {cost_val} درهم", org_id))

            # Evidences mapping
            evidences = data.get("evidences", [])
            cursor.execute("DELETE FROM service_evidences WHERE ps_id = ?", (ps_id,))
            for ev_item in evidences:
                ev_title = ev_item.get("title") if isinstance(ev_item, dict) else str(ev_item)
                ev_title = ev_title.strip()
                if not ev_title:
                    continue
                cursor.execute("SELECT evidence_id FROM evidences WHERE evidence_title = ?", (ev_title,))
                erow = cursor.fetchone()
                if erow:
                    ev_id = erow["evidence_id"]
                else:
                    ev_slug = f"ev_{abs(hash(ev_title)) % 10000000}"
                    cursor.execute("INSERT OR IGNORE INTO evidences (evidence_slug, evidence_title) VALUES (?, ?)", (ev_slug, ev_title))
                    ev_id = cursor.lastrowid
                if ev_id:
                    cursor.execute("INSERT OR IGNORE INTO service_evidences (ps_id, evidence_id) VALUES (?, ?)", (ps_id, ev_id))

            conn.commit()
            conn.close()

            # Append the triples cleanly to output/procedures_administratives_cpsv.ttl
            new_turtle = self.to_turtle(data)
            body_lines = [l for l in new_turtle.splitlines() if not l.startswith("@prefix")]
            
            with open(OUTPUT_TTL, "a", encoding="utf-8") as f:
                f.write(f"\n# --- New Validated Moroccan Procedure: {ps_uuid} ---\n")
                f.write("\n".join(body_lines) + "\n")

            return True, f"Successfully persisted procedure '{title_ar}' ({ps_uuid}) to database and repo."

        except Exception as e:
            return False, f"Error saving procedure: {str(e)}"
