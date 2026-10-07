#!/usr/bin/env python3
"""
Morocco CPSV Procedure Manager
==============================
Provides high-performance query, search, inspection, and update capabilities
for Moroccan administrative procedures in the SQLite database and RDF datasets.
"""

import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

try:
    from .id_policy import canonical_policy
except ImportError:
    from id_policy import canonical_policy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "src", "procedures_administratives_cpsv.db")


class ProcedureManager:
    """Manages CRUD and search operations over the procedures_administratives_cpsv database."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def search_procedures(self, search: Optional[str] = None, limit: int = 30, offset: int = 0) -> Dict[str, Any]:
        """Search procedures by title keyword or UUID."""
        conn = self._get_connection()
        c = conn.cursor()

        if search and search.strip():
            kw = f"%{search.strip()}%"
            c.execute("""
                SELECT COUNT(*) FROM public_services
                WHERE procedure_name_cleaned LIKE ? OR ps_uuid LIKE ?
            """, (kw, kw))
            total = c.fetchone()[0]

            c.execute("""
                SELECT p.ps_id, p.ps_uuid, p.procedure_name_cleaned, p.fee_raw, p.processing_time_raw,
                       o.org_id, o.org_name,
                       (SELECT COUNT(*) FROM service_evidences se WHERE se.ps_id = p.ps_id) AS ev_count
                FROM public_services p
                LEFT JOIN organisations o ON p.authority_id = o.org_id
                WHERE p.procedure_name_cleaned LIKE ? OR p.ps_uuid LIKE ?
                ORDER BY p.ps_id DESC
                LIMIT ? OFFSET ?
            """, (kw, kw, limit, offset))
        else:
            c.execute("SELECT COUNT(*) FROM public_services")
            total = c.fetchone()[0]

            c.execute("""
                SELECT p.ps_id, p.ps_uuid, p.procedure_name_cleaned, p.fee_raw, p.processing_time_raw,
                       o.org_id, o.org_name,
                       (SELECT COUNT(*) FROM service_evidences se WHERE se.ps_id = p.ps_id) AS ev_count
                FROM public_services p
                LEFT JOIN organisations o ON p.authority_id = o.org_id
                ORDER BY p.ps_id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        rows = c.fetchall()
        procedures = []
        for r in rows:
            fee = 0.0
            try:
                fee = float(r["fee_raw"]) if r["fee_raw"] else 0.0
            except ValueError:
                fee = 0.0

            procedures.append({
                "ps_id": r["ps_id"],
                "ps_uuid": r["ps_uuid"] or f"PS-{r['ps_id']}",
                "title": r["procedure_name_cleaned"] or "مسطرة إدارية",
                "authority_id": r["org_id"] or 1,
                "authority_name": r["org_name"] or "المملكة المغربية",
                "cost": fee,
                "processing_time": r["processing_time_raw"] or "20 يوماً",
                "evidences_count": r["ev_count"] or 0
            })

        conn.close()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "procedures": procedures
        }

    def get_procedure_detail(self, proc_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full details and associated evidences for a given procedure ID or UUID."""
        conn = self._get_connection()
        c = conn.cursor()

        c.execute("""
            SELECT p.ps_id, p.ps_uuid, p.procedure_name_raw, p.procedure_name_cleaned,
                   p.description_cleaned, p.authority_id, o.org_name, o.org_slug,
                   p.output_id, out.output_title, out.output_slug,
                   p.fee_raw, p.processing_time_raw, p.url_source
            FROM public_services p
            LEFT JOIN organisations o ON p.authority_id = o.org_id
            LEFT JOIN outputs out ON p.output_id = out.output_id
            WHERE p.ps_id = ? OR p.ps_uuid = ?
        """, (proc_id, proc_id))
        row = c.fetchone()
        if not row:
            conn.close()
            return None

        ps_id = row["ps_id"]

        # Fetch evidences
        c.execute("""
            SELECT e.evidence_id, e.evidence_slug, e.evidence_title
            FROM service_evidences se
            JOIN evidences e ON se.evidence_id = e.evidence_id
            WHERE se.ps_id = ?
            ORDER BY e.evidence_id ASC
        """, (ps_id,))
        ev_rows = c.fetchall()
        evidences = [{
            "evidence_id": er["evidence_id"],
            "slug": er["evidence_slug"],
            "title": er["evidence_title"]
        } for er in ev_rows]

        conn.close()

        fee = 0.0
        try:
            fee = float(row["fee_raw"]) if row["fee_raw"] else 0.0
        except ValueError:
            fee = 0.0

        return {
            "ps_id": row["ps_id"],
            "ps_uuid": row["ps_uuid"] or f"PS-{row['ps_id']}",
            "title": row["procedure_name_cleaned"] or row["procedure_name_raw"] or "",
            "description": row["description_cleaned"] or "",
            "authority_id": row["authority_id"] or 1,
            "authority_name": row["org_name"] or "المملكة المغربية",
            "authority_slug": row["org_slug"] or "",
            "output_id": row["output_id"],
            "output_title": row["output_title"] or "",
            "output_slug": row["output_slug"] or "",
            "cost": fee,
            "processing_time": row["processing_time_raw"] or "20 يوماً",
            "url_source": row["url_source"] or "",
            "evidences": evidences
        }

    def update_procedure(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update procedure fields, deliverable output, and associated evidences in SQLite database."""
        ps_id = data.get("ps_id")
        if not ps_id:
            return False, "Procedure ps_id is required."

        title = data.get("title", "").strip()
        if not title:
            return False, "Procedure title is required."

        desc = data.get("description", "").strip() or title
        authority_id = data.get("authority_id", 1)
        cost_val = float(data.get("cost", 0.0))
        proc_time = data.get("processing_time", "20 يوماً")
        output_title = data.get("output_title", "").strip()

        conn = self._get_connection()
        c = conn.cursor()

        try:
            from .audit_logger import log_public_service_change, log_evidence_change, log_output_change, log_action
        except ImportError:
            from audit_logger import log_public_service_change, log_evidence_change, log_output_change, log_action

        try:
            # Fetch existing procedure details for audit comparison
            c.execute("""
                SELECT p.ps_id, p.ps_uuid, p.procedure_name_cleaned, p.description_cleaned,
                       p.authority_id, p.output_id, out.output_title, p.fee_raw, p.processing_time_raw
                FROM public_services p
                LEFT JOIN outputs out ON p.output_id = out.output_id
                WHERE p.ps_id = ?
            """, (ps_id,))
            old = c.fetchone()
            ps_uuid = old["ps_uuid"] if old and old["ps_uuid"] else f"PS-{ps_id}"

            # Handle output_id
            output_id = data.get("output_id")
            if output_title:
                c.execute("SELECT output_id FROM outputs WHERE output_title = ?", (output_title,))
                orow = c.fetchone()
                if orow:
                    output_id = orow["output_id"]
                else:
                    slug, _ = canonical_policy.resolve_output_slug(output_title)
                    c.execute("INSERT INTO outputs (output_slug, output_title) VALUES (?, ?)", (slug, output_title))
                    output_id = c.lastrowid
                    log_output_change(str(output_id), "output_title", "added", output_title)
            else:
                output_id = None

            # Check attribute changes for audit log
            if old:
                if (old["procedure_name_cleaned"] or "") != title:
                    log_public_service_change(ps_uuid, "title", "changed", f"{old['procedure_name_cleaned']} -> {title}")
                if (old["description_cleaned"] or "") != desc:
                    log_public_service_change(ps_uuid, "description", "changed")
                if old["authority_id"] != authority_id:
                    log_public_service_change(ps_uuid, "authority_id", "changed", f"{old['authority_id']} -> {authority_id}")
                try:
                    old_cost = float(old["fee_raw"]) if old["fee_raw"] else 0.0
                except ValueError:
                    old_cost = 0.0
                if abs(old_cost - cost_val) > 0.001:
                    log_public_service_change(ps_uuid, "cost", "changed", f"{old_cost} -> {cost_val}")
                if (old["processing_time_raw"] or "") != proc_time:
                    log_public_service_change(ps_uuid, "processing_time", "changed", f"{old['processing_time_raw']} -> {proc_time}")
                if (old["output_title"] or "") != output_title:
                    log_public_service_change(ps_uuid, "output", "changed", f"{old['output_title']} -> {output_title}")

            # Update public_services
            c.execute("""
                UPDATE public_services
                SET procedure_name_raw = ?, procedure_name_cleaned = ?, description_cleaned = ?,
                    authority_id = ?, output_id = ?, fee_raw = ?, processing_time_raw = ?
                WHERE ps_id = ?
            """, (title, title, desc, authority_id, output_id, str(cost_val), proc_time, ps_id))

            # Evidences update
            evidence_titles = data.get("evidences", [])
            if isinstance(evidence_titles, list):
                # Fetch old evidences for audit log
                c.execute("""
                    SELECT e.evidence_title FROM service_evidences se
                    JOIN evidences e ON se.evidence_id = e.evidence_id
                    WHERE se.ps_id = ?
                """, (ps_id,))
                old_evs = set(r["evidence_title"] for r in c.fetchall())
                
                clean_new_evs = []
                for ev_item in evidence_titles:
                    ev_title = ev_item.get("title") if isinstance(ev_item, dict) else str(ev_item)
                    ev_title = ev_title.strip()
                    if ev_title:
                        clean_new_evs.append(ev_title)
                
                new_evs_set = set(clean_new_evs)
                
                # Delete existing links
                c.execute("DELETE FROM service_evidences WHERE ps_id = ?", (ps_id,))

                for ev_title in clean_new_evs:
                    c.execute("SELECT evidence_id FROM evidences WHERE evidence_title = ?", (ev_title,))
                    erow = c.fetchone()
                    if erow:
                        ev_id = erow["evidence_id"]
                    else:
                        slug, _ = canonical_policy.resolve_evidence_slug(ev_title)
                        c.execute("INSERT INTO evidences (evidence_slug, evidence_title) VALUES (?, ?)",
                                  (slug, ev_title))
                        ev_id = c.lastrowid
                        log_evidence_change(str(ev_id), "evidence_title", "added", ev_title)

                    c.execute("INSERT INTO service_evidences (ps_id, evidence_id) VALUES (?, ?)", (ps_id, ev_id))

                # Audit diff
                for ev in (new_evs_set - old_evs):
                    log_public_service_change(ps_uuid, "evidence", "added", ev)
                for ev in (old_evs - new_evs_set):
                    log_public_service_change(ps_uuid, "evidence", "deleted", ev)

            conn.commit()
            conn.close()
            return True, f"تم تحديث بيانات المسطرة '{title}' بنجاح."

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"خطأ أثناء الحفظ: {str(e)}"

    def delete_procedure(self, identifier: Any) -> Tuple[bool, str]:
        """Delete a procedure and its linked entities from the database."""
        conn = self._get_connection()
        c = conn.cursor()
        try:
            from .audit_logger import log_public_service_change
        except ImportError:
            from audit_logger import log_public_service_change

        try:
            ident_str = str(identifier).strip()
            c.execute("SELECT ps_id, ps_uuid, procedure_name_cleaned FROM public_services WHERE ps_id = ? OR ps_uuid = ?", (ident_str, ident_str))
            row = c.fetchone()
            if not row:
                conn.close()
                return False, f"المسطرة رقم أو معرف '{identifier}' غير موجودة في قاعدة البيانات."

            ps_id = row["ps_id"]
            ps_uuid = row["ps_uuid"] or f"PS-{ps_id}"
            name = row["procedure_name_cleaned"] or f"#{ps_id}"

            c.execute("DELETE FROM service_evidences WHERE ps_id = ?", (ps_id,))
            c.execute("DELETE FROM costs WHERE ps_id = ?", (ps_id,))
            c.execute("DELETE FROM service_channels WHERE ps_id = ?", (ps_id,))
            c.execute("DELETE FROM public_services WHERE ps_id = ?", (ps_id,))
            conn.commit()
            conn.close()

            log_public_service_change(ps_uuid, "procedure", "deleted", name)
            return True, f"تم حذف المسطرة '{name}' ({ps_uuid}) بنجاح."
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"خطأ أثناء حذف المسطرة: {str(e)}"
