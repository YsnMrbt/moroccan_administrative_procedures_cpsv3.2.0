"""
Morocco CPSV-AP 3.2.0 - ID Assignment Policy & Canonical Source of Truth Engine
=============================================================================
Ensures 100% ID consistency, continuity, and deduplication using RapidFuzz string matching.
Supports simplified IDs:
- Public Services: PS00001 (5 digits)
- Competent Authorities: CA00001 (5 digits)
- Outputs / Deliverables: OTPT000001 (6 digits)
- Evidences / Documents: EVD00001 (5 digits)
"""

import os
import re
import json
import uuid
import hashlib
from typing import Optional, Tuple, Dict, Any, List

try:
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

PROC_ID_PATTERN = re.compile(r'^PS\d{5}$', re.IGNORECASE)
ORG_SLUG_PATTERN = re.compile(r'^CA\d{5}$', re.IGNORECASE)
OUTPUT_SLUG_PATTERN = re.compile(r'^OTPT\d{6}$', re.IGNORECASE)
EVD_SLUG_PATTERN = re.compile(r'^EVD\d{5}$', re.IGNORECASE)

# Legacy patterns for backward compatibility lookups
LEGACY_UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
LEGACY_ORG_PATTERN = re.compile(r'^org_[0-9a-f]{12}$', re.IGNORECASE)


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for resilient fuzzy comparison."""
    if not text:
        return ""
    t = text.strip()
    # Remove Arabic tashkeel (diacritics)
    t = re.sub(r'[\u064B-\u065F\u0670]', '', t)
    # Normalize Alef forms: أ, إ, آ, ٱ -> ا
    t = re.sub(r'[إأآٱ]', 'ا', t)
    # Normalize Ta Marbuta: ة -> ه
    t = re.sub(r'ة', 'ه', t)
    # Normalize Ya / Alef Maksura: ى -> ي
    t = re.sub(r'ى', 'ي', t)
    # Remove multiple spaces and punctuation
    t = re.sub(r'[^\w\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()


class IdPolicyManager:
    """Singleton manager for immutable canonical IDs and fuzzy similarity assignment."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(IdPolicyManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, registry_path: Optional[str] = None):
        if getattr(self, '_initialized', False):
            return

        if registry_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(base_dir, 'registry', 'canonical_ids_registry.json')

        self.registry_path = registry_path
        self.procedures: List[Dict[str, Any]] = []
        self.authorities: List[Dict[str, Any]] = []
        self.outputs: List[Dict[str, Any]] = []
        self.evidences: List[Dict[str, Any]] = []

        self._proc_title_map: Dict[str, str] = {} # norm_title -> ps_code
        self._auth_name_map: Dict[str, str] = {}  # norm_name -> ca_code
        self._out_title_map: Dict[str, str] = {}  # norm_title -> otpt_code
        self._evd_title_map: Dict[str, str] = {}  # norm_title -> evd_code

        self._legacy_proc_map: Dict[str, str] = {} # legacy_uuid -> ps_code
        self._legacy_auth_map: Dict[str, str] = {} # legacy_slug -> ca_code

        self._proc_norm_titles: List[str] = []
        self._auth_norm_names: List[str] = []
        self._out_norm_titles: List[str] = []
        self._evd_norm_titles: List[str] = []
        self._dirty = False

        self._load_registry()
        self._initialized = True

    def _load_registry(self):
        if not os.path.exists(self.registry_path):
            return

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.procedures = data.get('procedures', [])
        self.authorities = data.get('authorities', [])
        self.outputs = data.get('outputs', [])
        self.evidences = data.get('evidences', [])

        for p in self.procedures:
            code = p.get('ps_code') or p.get('ps_uuid')
            norm = normalize_arabic(p.get('title', ''))
            if norm and norm not in self._proc_title_map:
                self._proc_title_map[norm] = code
            if p.get('legacy_uuid'):
                self._legacy_proc_map[p['legacy_uuid'].lower()] = code

        for a in self.authorities:
            code = a.get('ca_code') or a.get('org_slug')
            norm = normalize_arabic(a.get('name', ''))
            if norm and norm not in self._auth_name_map:
                self._auth_name_map[norm] = code
            if a.get('legacy_slug'):
                self._legacy_auth_map[a['legacy_slug'].lower()] = code

        for o in self.outputs:
            code = o.get('otpt_code') or o.get('output_slug')
            norm = normalize_arabic(o.get('title', ''))
            if norm and norm not in self._out_title_map:
                self._out_title_map[norm] = code

        for e in self.evidences:
            code = e.get('evd_code') or e.get('evidence_slug')
            norm = normalize_arabic(e.get('title', ''))
            if norm and norm not in self._evd_title_map:
                self._evd_title_map[norm] = code

        self._proc_norm_titles = list(self._proc_title_map.keys())
        self._auth_norm_names = list(self._auth_name_map.keys())
        self._out_norm_titles = list(self._out_title_map.keys())
        self._evd_norm_titles = list(self._evd_title_map.keys())

    def resolve_procedure_uuid(self, title: str, candidate_id: Optional[str] = None, threshold: float = 92.0) -> Tuple[str, bool]:
        """
        Resolves or assigns a compliant PS00001 code for a procedure.
        Returns: (resolved_id, is_newly_assigned)
        """
        clean_title = (title or "").strip()
        norm_title = normalize_arabic(clean_title)

        # 1. Candidate ID matches simplified format
        if candidate_id and PROC_ID_PATTERN.match(candidate_id):
            cand_upper = candidate_id.upper()
            for p in self.procedures:
                if (p.get('ps_code') or p.get('ps_uuid', '')).upper() == cand_upper:
                    return cand_upper, False

        # 2. Candidate ID matches legacy UUID
        if candidate_id and candidate_id.lower() in self._legacy_proc_map:
            return self._legacy_proc_map[candidate_id.lower()], False

        # 3. Check exact normalized match in canonical registry
        if norm_title in self._proc_title_map:
            return self._proc_title_map[norm_title], False

        # 4. Fuzzy search in source of truth via RapidFuzz
        if HAS_RAPIDFUZZ and self._proc_norm_titles:
            match = process.extractOne(
                norm_title,
                self._proc_norm_titles,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=threshold
            )
            if match:
                matched_norm, score, _ = match
                matched_id = self._proc_title_map[matched_norm]
                self._proc_title_map[norm_title] = matched_id
                return matched_id, False

        # 5. Assign new sequential ID PS00001
        new_id = f"PS{len(self.procedures) + 1:05d}"
        new_entry = {
            'ps_id': len(self.procedures) + 1,
            'ps_code': new_id,
            'ps_uuid': new_id,
            'title': clean_title,
            'description': clean_title
        }
        self.procedures.append(new_entry)
        self._proc_title_map[norm_title] = new_id
        self._proc_norm_titles.append(norm_title)
        self._dirty = True
        self.save_registry()

        return new_id, True

    def resolve_authority_slug(self, name: str, candidate_slug: Optional[str] = None, threshold: float = 92.0) -> Tuple[str, bool]:
        """
        Resolves or assigns a compliant CA00001 code for an authority.
        Returns: (resolved_slug, is_newly_assigned)
        """
        clean_name = (name or "").strip()
        norm_name = normalize_arabic(clean_name)

        if candidate_slug and ORG_SLUG_PATTERN.match(candidate_slug):
            cand_upper = candidate_slug.upper()
            for a in self.authorities:
                if (a.get('ca_code') or a.get('org_slug', '')).upper() == cand_upper:
                    return cand_upper, False

        if candidate_slug and candidate_slug.lower() in self._legacy_auth_map:
            return self._legacy_auth_map[candidate_slug.lower()], False

        if norm_name in self._auth_name_map:
            return self._auth_name_map[norm_name], False

        if HAS_RAPIDFUZZ and self._auth_norm_names:
            match = process.extractOne(
                norm_name,
                self._auth_norm_names,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=threshold
            )
            if match:
                matched_norm, score, _ = match
                matched_slug = self._auth_name_map[matched_norm]
                self._auth_name_map[norm_name] = matched_slug
                return matched_slug, False

        new_slug = f"CA{len(self.authorities) + 1:05d}"
        new_entry = {
            'org_id': len(self.authorities) + 1,
            'ca_code': new_slug,
            'org_slug': new_slug,
            'name': clean_name
        }
        self.authorities.append(new_entry)
        self._auth_name_map[norm_name] = new_slug
        self._auth_norm_names.append(norm_name)
        self._dirty = True
        self.save_registry()

        return new_slug, True

    def resolve_output_slug(self, title: str, candidate_slug: Optional[str] = None) -> Tuple[str, bool]:
        """
        Resolves or assigns a compliant OTPT000001 code for an output deliverable.
        Returns: (resolved_slug, is_newly_assigned)
        """
        clean_title = (title or "").strip()
        norm_title = normalize_arabic(clean_title)

        if candidate_slug and OUTPUT_SLUG_PATTERN.match(candidate_slug):
            cand_upper = candidate_slug.upper()
            for o in self.outputs:
                if (o.get('otpt_code') or o.get('output_slug', '')).upper() == cand_upper:
                    return cand_upper, False

        if norm_title in self._out_title_map:
            return self._out_title_map[norm_title], False

        new_slug = f"OTPT{len(self.outputs) + 1:06d}"
        new_entry = {
            'output_id': len(self.outputs) + 1,
            'otpt_code': new_slug,
            'output_slug': new_slug,
            'title': clean_title
        }
        self.outputs.append(new_entry)
        self._out_title_map[norm_title] = new_slug
        self._out_norm_titles.append(norm_title)
        self._dirty = True
        self.save_registry()

        return new_slug, True

    def resolve_evidence_slug(self, title: str, candidate_slug: Optional[str] = None) -> Tuple[str, bool]:
        """
        Resolves or assigns a compliant EVD00001 code for a required evidence.
        Returns: (resolved_slug, is_newly_assigned)
        """
        clean_title = (title or "").strip()
        norm_title = normalize_arabic(clean_title)

        if candidate_slug and EVD_SLUG_PATTERN.match(candidate_slug):
            cand_upper = candidate_slug.upper()
            for e in self.evidences:
                if (e.get('evd_code') or e.get('evidence_slug', '')).upper() == cand_upper:
                    return cand_upper, False

        if norm_title in self._evd_title_map:
            return self._evd_title_map[norm_title], False

        new_slug = f"EVD{len(self.evidences) + 1:05d}"
        new_entry = {
            'evidence_id': len(self.evidences) + 1,
            'evd_code': new_slug,
            'evidence_slug': new_slug,
            'title': clean_title
        }
        self.evidences.append(new_entry)
        self._evd_title_map[norm_title] = new_slug
        self._evd_norm_titles.append(norm_title)
        self._dirty = True
        self.save_registry()

        return new_slug, True

    def save_registry(self):
        """Persists source of truth to JSON file if modified."""
        if not self._dirty:
            return
        data = {
            'version': '0.9.0',
            'description': 'Morocco CPSV Canonical Source of Truth with Simplified IDs',
            'id_policy': {
                'public_service': 'PS00001',
                'competent_authority': 'CA00001',
                'output': 'OTPT000001',
                'evidence': 'EVD00001',
                'cost': 'COST00001'
            },
            'stats': {
                'total_procedures': len(self.procedures),
                'total_authorities': len(self.authorities),
                'total_outputs': len(self.outputs),
                'total_evidences': len(self.evidences)
            },
            'procedures': self.procedures,
            'authorities': self.authorities,
            'outputs': self.outputs,
            'evidences': self.evidences
        }
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._dirty = False


# Global default instance
id_policy = IdPolicyManager()
canonical_policy = id_policy
