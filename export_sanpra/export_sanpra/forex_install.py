"""Idempotent installer for the complete Forex Management feature set."""

import frappe

from erpnext.regional.united_arab_emirates.setup import make_custom_fields as make_uae_custom_fields

from export_sanpra.export_sanpra.forex_setup import install as install_custom_fields
from export_sanpra.export_sanpra.forex_phase2 import install as install_reports_workspace
from export_sanpra.export_sanpra.forex_phase3 import install as install_client_integrations
from export_sanpra.export_sanpra.forex_notifications import install as install_notification_job
from export_sanpra.export_sanpra.forex_phase7 import install as install_phase7


def ensure_uae_address_schema():
    """Ensure UAE Address metadata and its database column stay synchronized."""
    make_uae_custom_fields()

    # create_custom_fields() only synchronizes a DocType when metadata changes.
    # Repair sites where the Custom Field exists but the SQL column is missing.
    if not frappe.db.has_column("Address", "emirate"):
        frappe.clear_cache(doctype="Address")
        frappe.db.updatedb("Address")


def after_migrate():
    ensure_uae_address_schema()
    install_custom_fields()
    install_reports_workspace()
    install_client_integrations()
    install_notification_job()
    install_phase7()
