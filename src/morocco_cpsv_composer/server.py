#!/usr/bin/env python3
"""
Morocco CPSV Composer & Validator - Local Web Server
===================================================
Standalone HTTP server (zero external dependencies) providing
the official Moroccan administrative portal interface for authoring
and validating CPSV-AP 3.2.0 public services.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from typing import Dict, Any

# Ensure project src is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from morocco_cpsv_composer.registry import MoroccoRegistry
from morocco_cpsv_composer.builder import ProcedureComposer
from morocco_cpsv_validator.validator import MoroccoCPSVValidator
from morocco_cpsv_composer.procedure_manager import ProcedureManager

def trigger_background_sync():
    """Runs dataset distribution synchronization in a background thread."""
    def _run():
        try:
            from sync_dataset_distributions import sync_master_distributions, sync_curated_scenarios_from_db
            sync_master_distributions()
            sync_curated_scenarios_from_db()
            print("Background distribution synchronization completed successfully.")
        except Exception as e:
            print("Background sync error:", e)
    t = threading.Thread(target=_run, daemon=True)
    t.start()

try:
    from morocco_cpsv_composer.audit_logger import (
        log_public_service_change, log_organisation_change, log_output_change, log_evidence_change
    )
except ImportError:
    from audit_logger import (
        log_public_service_change, log_organisation_change, log_output_change, log_evidence_change
    )

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

# Shared singletons
registry = MoroccoRegistry()
composer = ProcedureComposer(registry)
validator = MoroccoCPSVValidator()
proc_manager = ProcedureManager()

class MoroccoPortalHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Morocco CPSV Administrative Portal."""

    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_DELETE(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        if path.startswith("/api/procedures/"):
            proc_id_str = path.replace("/api/procedures/", "").strip()
            success, msg = proc_manager.delete_procedure(proc_id_str)
            if success:
                self._send_json(200, {"success": True, "message": msg})
            else:
                self._send_json(400, {"error": msg})
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 Not Found")

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        query = urllib.parse.parse_qs(url_parsed.query)

        # Static assets
        if path == "/" or path == "/index.html":
            self._serve_file(os.path.join(WEB_DIR, "index.html"), "text/html; charset=utf-8")
            return
        elif path == "/portal.css":
            self._serve_file(os.path.join(WEB_DIR, "portal.css"), "text/css; charset=utf-8")
            return
        elif path == "/portal.js":
            self._serve_file(os.path.join(WEB_DIR, "portal.js"), "application/javascript; charset=utf-8")
            return
        elif path == "/coat_of_arms.svg":
            self._serve_file(os.path.join(WEB_DIR, "coat_of_arms.svg"), "image/svg+xml")
            return
        elif path == "/flag_morocco.png":
            self._serve_file(os.path.join(WEB_DIR, "flag_morocco.png"), "image/png")
            return
        elif path == "/flag_morocco.svg":
            self._serve_file(os.path.join(WEB_DIR, "flag_morocco.svg"), "image/svg+xml")
            return

        # REST API endpoints
        if path == "/api/status":
            stats = {
                "authorities_count": len(registry.authorities),
                "outputs_count": len(registry.outputs),
                "evidences_count": len(registry.evidences),
                "validator_ready": True,
                "specification": "SEMIC CPSV-AP 3.2.0",
                "mode": "OFFLINE_LOCAL"
            }
            self._send_json(200, stats)

        elif path == "/api/authorities":
            q = query.get("q", [None])[0]
            auths = registry.get_authorities(search=q)
            self._send_json(200, auths)

        elif path == "/api/outputs":
            q = query.get("q", [None])[0]
            limit = int(query.get("limit", [60])[0])
            outs = registry.get_outputs(search=q, limit=limit)
            self._send_json(200, outs)

        elif path == "/api/evidences":
            q = query.get("q", [None])[0]
            limit = int(query.get("limit", [60])[0])
            evids = registry.get_evidences(search=q, limit=limit)
            self._send_json(200, evids)

        elif path == "/api/vocabularies":
            self._send_json(200, registry.get_vocabularies())

        elif path == "/api/procedures":
            q = query.get("q", [None])[0]
            limit = int(query.get("limit", [30])[0])
            offset = int(query.get("offset", [0])[0])
            res = proc_manager.search_procedures(search=q, limit=limit, offset=offset)
            self._send_json(200, res)

        elif path == "/api/audit-log":
            log_file = os.path.join(BASE_DIR, "audit_modifications.log")
            lines = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]
            self._send_json(200, {"logs": lines[-150:]}) # Last 150 log entries

        elif path.startswith("/api/procedures/"):
            proc_id = path.replace("/api/procedures/", "").strip()
            detail = proc_manager.get_procedure_detail(proc_id)
            if detail:
                self._send_json(200, detail)
            else:
                self._send_json(404, {"error": "المسطرة غير موجودة"})

        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            self._send_json(400, {"error": "Invalid JSON format"})
            return

        if path == "/api/authorities":
            name_ar = body.get("name_ar", "").strip()
            if not name_ar:
                self._send_json(400, {"error": "Authority name in Arabic is required"})
                return
            new_auth = registry.add_authority(
                name_ar=name_ar,
                parent_name=body.get("parent_name"),
                classification=body.get("classification", "مؤسسة عمومية / إدارة")
            )
            # Sync into SQLite organisations table
            try:
                import sqlite3
                conn = sqlite3.connect(proc_manager.db_path)
                conn.execute("INSERT OR IGNORE INTO organisations (org_id, org_slug, org_name) VALUES (?, ?, ?)",
                             (int(new_auth["org_id"]), new_auth["org_slug"], new_auth["org_name"]))
                conn.commit()
                conn.close()
                log_organisation_change(str(new_auth["org_id"]), "organisation", "added", new_auth["org_name"])
            except Exception as e:
                print("Warning syncing organisation to SQLite:", e)
            self._send_json(201, new_auth)

        elif path == "/api/outputs":
            title = body.get("title_ar", "").strip()
            if not title:
                self._send_json(400, {"error": "Output title is required"})
                return
            new_out = registry.add_output(title)
            # Sync into SQLite outputs table
            try:
                import sqlite3
                conn = sqlite3.connect(proc_manager.db_path)
                conn.execute("INSERT OR IGNORE INTO outputs (output_id, output_slug, output_title) VALUES (?, ?, ?)",
                             (int(new_out["output_id"]), new_out["output_slug"], new_out["output_title"]))
                conn.commit()
                conn.close()
                log_output_change(str(new_out["output_id"]), "output_title", "added", new_out["output_title"])
            except Exception as e:
                print("Warning syncing output to SQLite:", e)
            self._send_json(201, new_out)

        elif path == "/api/evidences":
            title = body.get("title_ar", "").strip()
            if not title:
                self._send_json(400, {"error": "Evidence title is required"})
                return
            new_evid = registry.add_evidence(title, category=body.get("category", "وثيقة عادية"))
            try:
                import sqlite3
                conn = sqlite3.connect(proc_manager.db_path)
                conn.execute("INSERT OR IGNORE INTO evidences (evidence_id, evidence_slug, evidence_title) VALUES (?, ?, ?)",
                             (int(new_evid["evidence_id"]), new_evid["evidence_slug"], new_evid["evidence_title"]))
                conn.commit()
                conn.close()
                log_evidence_change(str(new_evid["evidence_id"]), "evidence_title", "added", new_evid["evidence_title"])
            except Exception as e:
                print("Warning syncing evidence to SQLite:", e)
            self._send_json(201, new_evid)

        elif path == "/api/compose":
            # Generate Turtle representation without saving
            try:
                turtle_str = composer.to_turtle(body)
                self._send_json(200, {"turtle": turtle_str})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/validate":
            # Compose Turtle & Validate against official SEMIC shapes
            try:
                turtle_str = composer.to_turtle(body)
                val_res = validator.validate(turtle_str, rdf_format="turtle")
                resp = val_res.to_dict()
                resp["turtle_preview"] = turtle_str
                self._send_json(200, resp)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/save":
            # Validate first! If 0 violations, persist to DB and output/procedures_administratives_cpsv.ttl
            try:
                turtle_str = composer.to_turtle(body)
                val_res = validator.validate(turtle_str, rdf_format="turtle")
                if not val_res.conforms:
                    self._send_json(422, {
                        "error": "Validation failed. Procedure does not meet CPSV-AP 3.2.0 constraints.",
                        "violations": val_res.violations
                    })
                    return

                success, msg = composer.save_to_database_and_repo(body)
                if success:
                    try:
                        ps_slug = body.get("service_slug", "new_procedure")
                        log_public_service_change(ps_slug, "procedure", "added", body.get("title_ar", ""))
                    except Exception as e_log:
                        print("Audit log error on save:", e_log)
                    trigger_background_sync()
                    self._send_json(200, {"success": True, "message": msg})
                else:
                    self._send_json(500, {"error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/sync":
            trigger_background_sync()
            self._send_json(200, {"success": True, "message": "Dataset distribution synchronization triggered."})

        elif path == "/api/procedures/delete":
            ps_id = body.get("ps_id") or body.get("ps_uuid")
            if not ps_id:
                self._send_json(400, {"error": "Procedure ps_id or ps_uuid is required"})
                return
            success, msg = proc_manager.delete_procedure(ps_id)
            if success:
                trigger_background_sync()
                self._send_json(200, {"success": True, "message": msg})
            else:
                self._send_json(400, {"error": msg})

        elif path == "/api/procedures/update":
            # 1. Update in SQLite database
            success, msg = proc_manager.update_procedure(body)
            if not success:
                self._send_json(400, {"error": msg})
                return
            trigger_background_sync()

            # 2. Build Turtle and Validate against SEMIC SHACL
            try:
                comp_data = {
                    "title_ar": body.get("title", ""),
                    "description_ar": body.get("description", ""),
                    "authority_name": body.get("authority_name", ""),
                    "authority_id": body.get("authority_id", 1),
                    "service_slug": body.get("ps_uuid", f"ps_{body.get('ps_id')}"),
                    "output_title": body.get("output_title", ""),
                    "processing_time": body.get("processing_time", "P20D"),
                    "cost": {
                        "value": float(body.get("cost", 0.0)),
                        "currency": "MAD"
                    },
                    "evidences": body.get("evidences", [])
                }
                turtle_str = composer.to_turtle(comp_data)
                val_res = validator.validate(turtle_str, rdf_format="turtle")

                # If valid, push changes to output/procedures_administratives_cpsv.ttl
                if val_res.conforms:
                    try:
                        master_ttl_path = os.path.join(BASE_DIR, "output", "procedures_administratives_cpsv.ttl")
                        if os.path.exists(master_ttl_path):
                            body_lines = [l for l in turtle_str.splitlines() if not l.startswith("@prefix")]
                            with open(master_ttl_path, "a", encoding="utf-8") as f:
                                f.write(f"\n# --- Procedure Update: {comp_data['service_slug']} ---\n")
                                f.write("\n".join(body_lines) + "\n")
                    except Exception as e_push:
                        print("Warning pushing update to master TTL:", e_push)

                resp = {
                    "success": True,
                    "message": msg,
                    "conforms": val_res.conforms,
                    "violations_count": val_res.violations_count,
                    "violations": val_res.violations,
                    "turtle_preview": turtle_str
                }
                self._send_json(200, resp)
            except Exception as e:
                self._send_json(200, {
                    "success": True,
                    "message": msg,
                    "warning": f"تم التحديث في قاعدة البيانات مع تعذر الفحص الفوري: {str(e)}"
                })

        elif path == "/api/procedures/validate-draft":
            # Live SHACL validation of the draft state
            try:
                comp_data = {
                    "title_ar": body.get("title", ""),
                    "description_ar": body.get("description", ""),
                    "authority_name": body.get("authority_name", ""),
                    "authority_id": body.get("authority_id", 1),
                    "service_slug": body.get("ps_uuid", f"ps_{body.get('ps_id')}"),
                    "output_title": body.get("output_title", ""),
                    "processing_time": body.get("processing_time", "P20D"),
                    "cost": {
                        "value": float(body.get("cost", 0.0)),
                        "currency": "MAD"
                    },
                    "evidences": body.get("evidences", [])
                }
                turtle_str = composer.to_turtle(comp_data)
                val_res = validator.validate(turtle_str, rdf_format="turtle")
                resp = val_res.to_dict()
                resp["turtle_preview"] = turtle_str
                self._send_json(200, resp)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/authorities/update":
            org_id = body.get("org_id")
            name_ar = body.get("name_ar", "").strip()
            if not org_id or not name_ar:
                self._send_json(400, {"error": "org_id and name_ar are required"})
                return
            success, msg, updated = registry.update_authority(
                str(org_id),
                name_ar,
                classification=body.get("classification"),
                parent_name=body.get("parent_name")
            )
            if success:
                try:
                    log_organisation_change(str(org_id), "name", "updated", name_ar)
                except Exception:
                    pass
                self._send_json(200, {"success": True, "message": msg, "authority": updated})
            else:
                self._send_json(400, {"error": msg})

        elif path == "/api/authorities/delete":
            org_id = body.get("org_id")
            if not org_id:
                self._send_json(400, {"error": "org_id is required"})
                return
            success, msg = registry.delete_authority(str(org_id))
            if success:
                try:
                    log_organisation_change(str(org_id), "organisation", "deleted", f"Org #{org_id}")
                except Exception:
                    pass
                self._send_json(200, {"success": True, "message": msg})
            else:
                self._send_json(400, {"error": msg})

        elif path == "/api/outputs/update":
            output_id = body.get("output_id")
            title_ar = body.get("title_ar", "").strip()
            if not output_id or not title_ar:
                self._send_json(400, {"error": "output_id and title_ar are required"})
                return
            success, msg, updated = registry.update_output(str(output_id), title_ar)
            if success:
                try:
                    log_output_change(str(output_id), "title", "updated", title_ar)
                except Exception:
                    pass
                self._send_json(200, {"success": True, "message": msg, "output": updated})
            else:
                self._send_json(400, {"error": msg})

        elif path == "/api/outputs/delete":
            output_id = body.get("output_id")
            if not output_id:
                self._send_json(400, {"error": "output_id is required"})
                return
            success, msg = registry.delete_output(str(output_id))
            if success:
                try:
                    log_output_change(str(output_id), "output", "deleted", f"Output #{output_id}")
                except Exception:
                    pass
                self._send_json(200, {"success": True, "message": msg})
            else:
                self._send_json(400, {"error": msg})

        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 Endpoint Not Found")

    def _send_json(self, status: int, data: Any):
        self._set_headers(status, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _serve_file(self, file_path: str, content_type: str):
        if not os.path.exists(file_path):
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 File Not Found")
            return
        with open(file_path, "rb") as f:
            content = f.read()
        self._set_headers(200, content_type)
        self.wfile.write(content)

    def log_message(self, format, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


def run_server(port: int = 8085):
    os.makedirs(WEB_DIR, exist_ok=True)
    server_address = ("", port)
    httpd = HTTPServer(server_address, MoroccoPortalHandler)
    print("=" * 65)
    print("المملكة المغربية - بوابة تحرير وتدقيق المساطر الإدارية CPSV-AP")
    print(f"Server running locally at: http://localhost:{port}")
    print(f"Serving UI from: {WEB_DIR}")
    print("Press Ctrl+C to stop.")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8085
    run_server(port)
