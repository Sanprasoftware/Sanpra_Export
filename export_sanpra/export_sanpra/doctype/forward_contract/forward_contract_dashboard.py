from frappe import _


def get_data():
    return {
        "fieldname": "forward_contract",
        "internal_links": {"Sales Order": "sales_order"},
        "transactions": [
            {
                "label": _("References"),
                "items": ["Sales Order", "Sales Invoice", "Payment Entry"],
            },
            {
                "label": _("Forex Transactions"),
                "items": [
                    "Forward Contract Utilization",
                    "Forward Contract Settlement",
                    "Forward Contract Valuation",
                ],
            },
        ],
    }
