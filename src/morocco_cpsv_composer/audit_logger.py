#!/usr/bin/env python3
"""
Morocco CPSV Audit Logger
=========================
Maintains an institutional audit log recording all additions, modifications,
and deletions across PublicServices, PublicOrganisations, Evidences, and Outputs.
Format:
  <EntityType> <EntityID> | <attribute> | <action> (<details>) | <hh:mm:ss>
"""

import os
import datetime
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_PATH = os.path.join(BASE_DIR, "audit_modifications.log")

_lock = threading.Lock()


def get_current_time_str() -> str:
    """Returns local time in hh:mm:ss format."""
    return datetime.datetime.now().strftime("%H:%M:%S")


def log_action(entity_type: str, entity_id: str, attribute: str, action: str, details: str = ""):
    """
    Inscribes a single audit entry to audit_modifications.log.
    Format:
      <entity_type> <entity_id> | <attribute> | <action> (<details>) | <hh:mm:ss>
    """
    time_str = get_current_time_str()
    details_part = f" ({details})" if details else ""
    log_line = f"{entity_type} {entity_id} | {attribute} | {action}{details_part} | {time_str}\n"

    with _lock:
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"[AuditLogger Error] Failed to write audit log: {e}")


def log_public_service_change(ps_id: str, attribute: str, action: str, details: str = ""):
    """Log modification, addition, or deletion on PublicService."""
    log_action("PublicService", str(ps_id), attribute, action, details)


def log_organisation_change(org_id: str, attribute: str, action: str, details: str = ""):
    """Log modification, addition, or deletion on PublicOrganisation."""
    log_action("PublicOrganisation", str(org_id), attribute, action, details)


def log_evidence_change(evidence_id: str, attribute: str, action: str, details: str = ""):
    """Log modification, addition, or deletion on Evidence."""
    log_action("Evidence", str(evidence_id), attribute, action, details)


def log_output_change(output_id: str, attribute: str, action: str, details: str = ""):
    """Log modification, addition, or deletion on Output."""
    log_action("Output", str(output_id), attribute, action, details)
