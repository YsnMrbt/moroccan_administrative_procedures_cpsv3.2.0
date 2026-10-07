#!/usr/bin/env python3
"""
Morocco CPSV Registry & Controlled Vocabulary Manager
====================================================
Manages Moroccan administrative entities:
- 104 Competent Authorities & administrative hierarchy
- 2,068 Standard Deliverable Outputs
- 7,764 Standard Evidences / Documents
- European Commission Publications Office Controlled Vocabularies
"""

import os
import csv
import hashlib
from typing import List, Dict, Optional, Any, Tuple

import sqlite3
from .id_policy import canonical_policy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "src", "procedures_administratives_cpsv.db")
CURATION_DIR = os.path.join(BASE_DIR, "curation")

AUTHORITIES_CSV = os.path.join(CURATION_DIR, "competent_authorities_hierarchy.csv")
OUTPUTS_CSV = os.path.join(CURATION_DIR, "outputs_curation_list.csv")
EVIDENCES_CSV = os.path.join(CURATION_DIR, "evidences_curation_list.csv")

# Controlled Vocabularies (EU Publications Office)
CONTROLLED_VOCABULARIES = {
    "currencies": [
        {"code": "MAD", "label": "درهم مغربي (Moroccan Dirham)", "uri": "http://publications.europa.eu/resource/authority/currency/MAD", "is_default": True},
        {"code": "EUR", "label": "يورو (Euro - للقنصليات بالخارج)", "uri": "http://publications.europa.eu/resource/authority/currency/EUR", "is_default": False},
        {"code": "USD", "label": "دولار أمريكي (US Dollar)", "uri": "http://publications.europa.eu/resource/authority/currency/USD", "is_default": False},
        {"code": "GBP", "label": "جنيه إسترليني (British Pound)", "uri": "http://publications.europa.eu/resource/authority/currency/GBP", "is_default": False}
    ],
    "languages": [
        {"code": "ARA", "label": "العربية (Arabic)", "uri": "http://publications.europa.eu/resource/authority/language/ARA", "tag": "ar", "is_default": True},
        {"code": "FRA", "label": "الفرنسية (French)", "uri": "http://publications.europa.eu/resource/authority/language/FRA", "tag": "fr", "is_default": False},
        {"code": "BER", "label": "الأمازيغية (Berber/Tamazight)", "uri": "http://publications.europa.eu/resource/authority/language/BER", "tag": "zgh", "is_default": False},
        {"code": "ENG", "label": "الإنجليزية (English)", "uri": "http://publications.europa.eu/resource/authority/language/ENG", "tag": "en", "is_default": False}
    ],
    "spatial": [
        {"code": "MAR", "label": "المملكة المغربية (Kingdom of Morocco)", "uri": "http://publications.europa.eu/resource/authority/country/MAR", "is_default": True}
    ],
    "channel_types": [
        {"code": "counter", "label": "شباك استقبال حضوري (Physical Counter / Administrative Desk)", "uri": "http://procedures_administratives_cpsv.ma/id/channel_type/counter"},
        {"code": "portal", "label": "بوابة إلكترونية / خدمة عن بعد (Online Portal / e-Service)", "uri": "http://procedures_administratives_cpsv.ma/id/channel_type/portal"},
        {"code": "mobile_app", "label": "تطبيق هاتفي ذكي (Mobile Application)", "uri": "http://procedures_administratives_cpsv.ma/id/channel_type/mobile"},
        {"code": "phone", "label": "مركز الاتصال / هاتف (Telephone Hotline)", "uri": "http://procedures_administratives_cpsv.ma/id/channel_type/phone"}
    ]
}

def generate_slug(prefix: str, text: str) -> str:
    """Generate deterministic 12-char hex MD5 slug for URIs."""
    if not text:
        return f"{prefix}none"
    h = hashlib.md5(text.strip().encode('utf-8')).hexdigest()[:12]
    return f"{prefix}{h}"


class MoroccoRegistry:
    """Registry cache and persistence manager for Moroccan CPSV entities."""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.authorities: List[Dict[str, Any]] = []
        self.outputs: List[Dict[str, Any]] = []
        self.evidences: List[Dict[str, Any]] = []
        self.load_all()

    def load_all(self):
        self._load_authorities()
        self._load_outputs()
        self._load_evidences()

    def _load_authorities(self):
        self.authorities = []
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT o.org_id, o.org_slug, o.org_name,
                           (SELECT COUNT(*) FROM public_services ps WHERE ps.authority_id = o.org_id) AS proc_count
                    FROM organisations o
                    ORDER BY o.org_id ASC
                """)
                for row in c.fetchall():
                    self.authorities.append({
                        "org_id": str(row["org_id"]),
                        "org_slug": row["org_slug"],
                        "org_uri": f"http://procedures_administratives_cpsv.ma/id/organisation/{row['org_slug']}",
                        "org_name": row["org_name"],
                        "procedure_count": int(row["proc_count"] or 0),
                        "org_level": 2,
                        "classification": "مؤسسة عمومية / إدارة",
                        "suggested_parent_name": "المملكة المغربية"
                    })
                conn.close()
                return
            except Exception as e:
                print(f"Warning loading authorities from DB: {e}")

        # Fallback to CSV if present
        if os.path.exists(AUTHORITIES_CSV):
            with open(AUTHORITIES_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.authorities.append({
                        "org_id": row.get("org_id"),
                        "org_slug": row.get("org_slug"),
                        "org_uri": row.get("org_uri"),
                        "org_name": row.get("org_name"),
                        "procedure_count": int(row.get("procedure_count", 0)),
                        "org_level": int(row.get("org_level", 2)),
                        "classification": row.get("classification"),
                        "suggested_parent_name": row.get("suggested_parent_name")
                    })

    def _load_outputs(self):
        self.outputs = []
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT out.output_id, out.output_slug, out.output_title,
                           (SELECT COUNT(*) FROM public_services ps WHERE ps.output_id = out.output_id) AS proc_count
                    FROM outputs out
                    ORDER BY out.output_id ASC
                """)
                for row in c.fetchall():
                    self.outputs.append({
                        "output_id": str(row["output_id"]),
                        "output_slug": row["output_slug"],
                        "output_uri": f"http://procedures_administratives_cpsv.ma/id/output/{row['output_slug']}",
                        "output_title": row["output_title"],
                        "procedure_count": int(row["proc_count"] or 0)
                    })
                conn.close()
                return
            except Exception as e:
                print(f"Warning loading outputs from DB: {e}")

        if os.path.exists(OUTPUTS_CSV):
            with open(OUTPUTS_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.outputs.append({
                        "output_id": row.get("output_id"),
                        "output_slug": row.get("output_slug"),
                        "output_uri": row.get("output_uri"),
                        "output_title": row.get("output_title"),
                        "procedure_count": int(row.get("procedure_count", 0))
                    })

    def _load_evidences(self):
        self.evidences = []
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT e.evidence_id, e.evidence_slug, e.evidence_title,
                           (SELECT COUNT(*) FROM service_evidences se WHERE se.evidence_id = e.evidence_id) AS proc_count
                    FROM evidences e
                    ORDER BY e.evidence_id ASC
                """)
                for row in c.fetchall():
                    self.evidences.append({
                        "evidence_id": str(row["evidence_id"]),
                        "evidence_slug": row["evidence_slug"],
                        "evidence_uri": f"http://procedures_administratives_cpsv.ma/id/evidence/{row['evidence_slug']}",
                        "evidence_title": row["evidence_title"],
                        "procedure_count": int(row["proc_count"] or 0),
                        "doc_category": "وثيقة إدارية"
                    })
                conn.close()
                return
            except Exception as e:
                print(f"Warning loading evidences from DB: {e}")

        if os.path.exists(EVIDENCES_CSV):
            with open(EVIDENCES_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.evidences.append({
                        "evidence_id": row.get("evidence_id"),
                        "evidence_slug": row.get("evidence_slug"),
                        "evidence_uri": row.get("evidence_uri"),
                        "evidence_title": row.get("evidence_title"),
                        "procedure_count": int(row.get("procedure_count", 0)),
                        "doc_category": row.get("doc_category")
                    })

    # ==========================================
    # Public Query Methods
    # ==========================================
    def get_authorities(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                if search:
                    s = f"%{search.strip().lower()}%"
                    c.execute("""
                        SELECT o.org_id, o.org_slug, o.org_name,
                               (SELECT COUNT(*) FROM public_services p WHERE p.authority_id = o.org_id) AS proc_count
                        FROM organisations o
                        WHERE LOWER(o.org_name) LIKE ?
                        ORDER BY proc_count DESC, o.org_id ASC
                    """, (s,))
                else:
                    c.execute("""
                        SELECT o.org_id, o.org_slug, o.org_name,
                               (SELECT COUNT(*) FROM public_services p WHERE p.authority_id = o.org_id) AS proc_count
                        FROM organisations o
                        ORDER BY proc_count DESC, o.org_id ASC
                    """)
                rows = c.fetchall()
                conn.close()
                return [{
                    "org_id": str(r["org_id"]),
                    "org_slug": r["org_slug"],
                    "org_uri": f"http://procedures_administratives_cpsv.ma/id/organisation/{r['org_slug']}",
                    "org_name": r["org_name"],
                    "procedure_count": int(r["proc_count"] or 0),
                    "classification": "مؤسسة عمومية / إدارة",
                    "suggested_parent_name": "المملكة المغربية"
                } for r in rows]
            except Exception as e:
                print(f"Warning querying authorities from DB: {e}")

        if not search:
            return self.authorities
        s = search.strip().lower()
        return [a for a in self.authorities if s in a["org_name"].lower()]

    def get_outputs(self, search: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                if search:
                    s = f"%{search.strip().lower()}%"
                    c.execute("""
                        SELECT o.output_id, o.output_slug, o.output_title,
                               (SELECT COUNT(*) FROM public_services p WHERE p.output_id = o.output_id) AS proc_count
                        FROM outputs o
                        WHERE LOWER(o.output_title) LIKE ?
                        ORDER BY o.output_id DESC
                        LIMIT ?
                    """, (s, limit))
                else:
                    c.execute("""
                        SELECT o.output_id, o.output_slug, o.output_title,
                               (SELECT COUNT(*) FROM public_services p WHERE p.output_id = o.output_id) AS proc_count
                        FROM outputs o
                        ORDER BY o.output_id DESC
                        LIMIT ?
                    """, (limit,))
                rows = c.fetchall()
                conn.close()
                return [{
                    "output_id": str(r["output_id"]),
                    "output_slug": r["output_slug"],
                    "output_uri": f"http://procedures_administratives_cpsv.ma/id/output/{r['output_slug']}",
                    "output_title": r["output_title"],
                    "procedure_count": int(r["proc_count"] or 0)
                } for r in rows]
            except Exception as e:
                print(f"Warning querying outputs from DB: {e}")

        if not search:
            return self.outputs[:limit]
        s = search.strip().lower()
        matches = [o for o in self.outputs if s in o["output_title"].lower()]
        return matches[:limit]

    def get_evidences(self, search: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                if search:
                    s = f"%{search.strip().lower()}%"
                    c.execute("""
                        SELECT e.evidence_id, e.evidence_slug, e.evidence_title,
                               (SELECT COUNT(*) FROM service_evidences se WHERE se.evidence_id = e.evidence_id) AS proc_count
                        FROM evidences e
                        WHERE LOWER(e.evidence_title) LIKE ?
                        ORDER BY e.evidence_id DESC
                        LIMIT ?
                    """, (s, limit))
                else:
                    c.execute("""
                        SELECT e.evidence_id, e.evidence_slug, e.evidence_title,
                               (SELECT COUNT(*) FROM service_evidences se WHERE se.evidence_id = e.evidence_id) AS proc_count
                        FROM evidences e
                        ORDER BY e.evidence_id DESC
                        LIMIT ?
                    """, (limit,))
                rows = c.fetchall()
                conn.close()
                return [{
                    "evidence_id": str(r["evidence_id"]),
                    "evidence_slug": r["evidence_slug"],
                    "evidence_uri": f"http://procedures_administratives_cpsv.ma/id/evidence/{r['evidence_slug']}",
                    "evidence_title": r["evidence_title"],
                    "procedure_count": int(r["proc_count"] or 0),
                    "doc_category": "وثيقة إدارية"
                } for r in rows]
            except Exception as e:
                print(f"Warning querying evidences from DB: {e}")

        if not search:
            return self.evidences[:limit]
        s = search.strip().lower()
        matches = [e for e in self.evidences if s in e["evidence_title"].lower()]
        return matches[:limit]

    def get_vocabularies(self) -> Dict[str, Any]:
        return CONTROLLED_VOCABULARIES

    # ==========================================
    # Dynamic Add & Management Methods
    # ==========================================
    def add_authority(self, name_ar: str, parent_name: Optional[str] = None, classification: str = "مؤسسة عمومية / إدارة", **kwargs) -> Dict[str, Any]:
        """Dynamically register a new Moroccan public organization with canonical ID resolution."""
        name_clean = name_ar.strip()
        # Check if already exists
        for a in self.authorities:
            if a["org_name"] == name_clean:
                return a

        slug, _ = canonical_policy.resolve_authority_slug(name_clean)
        uri = f"http://procedures_administratives_cpsv.ma/id/organisation/{slug}"
        new_id = max([int(a["org_id"]) for a in self.authorities if str(a["org_id"]).isdigit()] or [0]) + 1

        new_entry = {
            "org_id": str(new_id),
            "org_slug": slug,
            "org_uri": uri,
            "org_name": name_clean,
            "procedure_count": 0,
            "classification": classification,
            "suggested_parent_name": parent_name or "المملكة المغربية"
        }

        self.authorities.append(new_entry)

        # Persist to SQLite
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute(
                    "INSERT OR IGNORE INTO organisations (org_id, org_slug, org_name) VALUES (?, ?, ?)",
                    (int(new_entry["org_id"]), new_entry["org_slug"], new_entry["org_name"])
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning saving authority to DB: {e}")

        # Append to CSV if exists
        if os.path.exists(AUTHORITIES_CSV):
            try:
                with open(AUTHORITIES_CSV, mode="a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        new_entry["org_id"], new_entry["org_slug"], new_entry["org_uri"],
                        new_entry["org_name"], 0, 2,
                        new_entry["classification"], new_entry["suggested_parent_name"],
                        "org:subOrganizationOf", "USER_ADDED"
                    ])
            except Exception:
                pass

        return new_entry

    def update_authority(self, org_id: str, name_ar: str, classification: Optional[str] = None, parent_name: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Update authority details in DB and cache."""
        name_clean = name_ar.strip()
        if not name_clean:
            return False, "اسم المؤسسة مطلوب إجبارياً", {}

        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("UPDATE organisations SET org_name = ? WHERE org_id = ?", (name_clean, int(org_id)))
                conn.commit()
                conn.close()
            except Exception as e:
                return False, f"خطأ في قاعدة البيانات أثناء التحديث: {e}", {}

        updated_entry = {}
        for a in self.authorities:
            if str(a["org_id"]) == str(org_id):
                a["org_name"] = name_clean
                if classification:
                    a["classification"] = classification
                if parent_name:
                    a["suggested_parent_name"] = parent_name
                updated_entry = a
                break

        return True, "تم تحديث بيانات المؤسسة العمومية بنجاح", updated_entry

    def delete_authority(self, org_id: str) -> Tuple[bool, str]:
        """Delete authority and safely reassign linked procedures."""
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("UPDATE public_services SET authority_id = 1 WHERE authority_id = ?", (int(org_id),))
                c.execute("DELETE FROM organisations WHERE org_id = ?", (int(org_id),))
                conn.commit()
                conn.close()
            except Exception as e:
                return False, f"خطأ أثناء حذف المؤسسة: {e}"

        self.authorities = [a for a in self.authorities if str(a["org_id"]) != str(org_id)]
        return True, "تم حذف المؤسسة بنجاح"

    def add_output(self, title_ar: str) -> Dict[str, Any]:
        """Dynamically register a new procedure output/deliverable with simplified OTPT000001 code."""
        title_clean = title_ar.strip()
        for o in self.outputs:
            if o["output_title"] == title_clean:
                return o

        slug, _ = canonical_policy.resolve_output_slug(title_clean)
        uri = f"http://procedures_administratives_cpsv.ma/id/output/{slug}"
        new_id = max([int(o["output_id"]) for o in self.outputs if str(o["output_id"]).isdigit()] or [0]) + 1

        new_entry = {
            "output_id": str(new_id),
            "output_slug": slug,
            "output_uri": uri,
            "output_title": title_clean,
            "procedure_count": 0
        }

        self.outputs.append(new_entry)

        # Persist to SQLite
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute(
                    "INSERT OR IGNORE INTO outputs (output_id, output_slug, output_title) VALUES (?, ?, ?)",
                    (int(new_entry["output_id"]), new_entry["output_slug"], new_entry["output_title"])
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning saving output to DB: {e}")

        if os.path.exists(OUTPUTS_CSV):
            try:
                with open(OUTPUTS_CSV, mode="a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        new_entry["output_id"], new_entry["output_slug"], new_entry["output_uri"],
                        new_entry["output_title"], 0, "USER_ADDED", new_entry["output_title"], "ACTIVE"
                    ])
            except Exception:
                pass

        return new_entry

    def update_output(self, output_id: str, title_ar: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Update procedure output deliverable in DB and cache."""
        title_clean = title_ar.strip()
        if not title_clean:
            return False, "عنوان الشهادة أو المخرج مطلوب إجبارياً", {}

        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("UPDATE outputs SET output_title = ? WHERE output_id = ?", (title_clean, int(output_id)))
                conn.commit()
                conn.close()
            except Exception as e:
                return False, f"خطأ في قاعدة البيانات أثناء تحديث المخرج: {e}", {}

        updated_entry = {}
        for o in self.outputs:
            if str(o["output_id"]) == str(output_id):
                o["output_title"] = title_clean
                updated_entry = o
                break

        return True, "تم تحديث بيانات الشهادة أو الخدمة المسلمة بنجاح", updated_entry

    def delete_output(self, output_id: str) -> Tuple[bool, str]:
        """Delete output deliverable and unlink from procedures."""
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("UPDATE public_services SET output_id = NULL WHERE output_id = ?", (int(output_id),))
                c.execute("DELETE FROM outputs WHERE output_id = ?", (int(output_id),))
                conn.commit()
                conn.close()
            except Exception as e:
                return False, f"خطأ أثناء حذف المخرج: {e}"

        self.outputs = [o for o in self.outputs if str(o["output_id"]) != str(output_id)]
        return True, "تم حذف المخرج بنجاح"

    def add_evidence(self, title_ar: str, category: str = "وثيقة عادية (Standard Document)") -> Dict[str, Any]:
        """Dynamically register a new required evidence document with simplified EVD00001 code."""
        title_clean = title_ar.strip()
        for e in self.evidences:
            if e["evidence_title"] == title_clean:
                return e

        slug, _ = canonical_policy.resolve_evidence_slug(title_clean)
        uri = f"http://procedures_administratives_cpsv.ma/id/evidence/{slug}"
        new_id = max([int(e["evidence_id"]) for e in self.evidences if str(e["evidence_id"]).isdigit()] or [0]) + 1

        new_entry = {
            "evidence_id": str(new_id),
            "evidence_slug": slug,
            "evidence_uri": uri,
            "evidence_title": title_clean,
            "procedure_count": 0,
            "doc_category": category
        }

        self.evidences.append(new_entry)

        # Persist to SQLite
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute(
                    "INSERT OR IGNORE INTO evidences (evidence_id, evidence_slug, evidence_title) VALUES (?, ?, ?)",
                    (int(new_entry["evidence_id"]), new_entry["evidence_slug"], new_entry["evidence_title"])
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning saving evidence to DB: {e}")

        if os.path.exists(EVIDENCES_CSV):
            try:
                with open(EVIDENCES_CSV, mode="a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        new_entry["evidence_id"], new_entry["evidence_slug"], new_entry["evidence_uri"],
                        new_entry["evidence_title"], 0, new_entry["doc_category"], "ACTIVE"
                    ])
            except Exception:
                pass

        return new_entry
