"""Idempotent installer for the complete Forex Management feature set."""

from export_sanpra.export_sanpra.forex_setup import install as install_custom_fields
from export_sanpra.export_sanpra.forex_phase2 import install as install_reports_workspace
from export_sanpra.export_sanpra.forex_phase3 import install as install_client_integrations
from export_sanpra.export_sanpra.forex_notifications import install as install_notification_job
from export_sanpra.export_sanpra.forex_phase7 import install as install_phase7


def after_migrate():
    install_custom_fields()
    install_reports_workspace()
    install_client_integrations()
    install_notification_job()
    install_phase7()
