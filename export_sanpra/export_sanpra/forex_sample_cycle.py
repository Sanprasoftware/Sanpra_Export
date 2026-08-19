"""Create the documented, idempotent Forex Management sample cycle."""

import frappe

from export_sanpra.export_sanpra.forex_actions import close_contract


CONTRACT_NUMBER = "SAMPLE-FX-CYCLE-2026-001"


def create():
    """Create and commit one complete USD export hedge cycle on the demo site."""
    existing = frappe.db.get_value(
        "Forward Contract", {"contract_number": CONTRACT_NUMBER}, "name"
    )
    if existing:
        return _summary(existing)

    sales_order = frappe.get_doc("Sales Order", "E/SO/2526/78")
    sales_invoice = frappe.get_doc("Sales Invoice", "E/SI2627/7")
    amount = 1000
    forward_rate = 92.5
    actual_bank_rate = 92.8

    contract = frappe.get_doc(
        {
            "doctype": "Forward Contract",
            "company": sales_order.company,
            "contract_number": CONTRACT_NUMBER,
            "contract_type": "Export",
            "bank": "Axis Bank",
            "booking_date": "2026-08-19",
            "maturity_date": "2026-09-18",
            "currency": sales_order.currency,
            "company_currency": "INR",
            "contract_amount": amount,
            "forward_rate": forward_rate,
            "customer": sales_order.customer,
            "sales_order": sales_order.name,
            "sales_order_currency": sales_order.currency,
            "sales_order_total": sales_order.grand_total,
            "bank_reference_number": "SAMPLE-BANK-REF-2026-001",
            "dealer_name": "Sample Forex Dealer",
            "remarks": "Training sample: complete forex management cycle.",
        }
    ).insert(ignore_permissions=True)
    contract.submit()

    utilization = frappe.get_doc(
        {
            "doctype": "Forward Contract Utilization",
            "company": contract.company,
            "forward_contract": contract.name,
            "sales_order": sales_order.name,
            "customer": contract.customer,
            "sales_invoice": sales_invoice.name,
            "utilization_date": "2026-08-19",
            "currency": contract.currency,
            "utilized_amount": amount,
            "forward_rate": forward_rate,
            "settlement_rate": actual_bank_rate,
            "reference_exchange_rate": sales_invoice.conversion_rate,
            "remarks": "Full utilization for the documented sample cycle.",
        }
    ).insert(ignore_permissions=True)
    utilization.submit()

    settlement = frappe.get_doc(
        {
            "doctype": "Forward Contract Settlement",
            "company": contract.company,
            "forward_contract": contract.name,
            "bank": contract.bank,
            "settlement_date": "2026-08-19",
            "currency": contract.currency,
            "settlement_amount": amount,
            "forward_rate": forward_rate,
            "actual_bank_rate": actual_bank_rate,
            "reference_value": amount * sales_invoice.conversion_rate,
            "remarks": "Full settlement for the documented sample cycle.",
        }
    ).insert(ignore_permissions=True)
    settlement.submit()

    close_contract(contract.name, "Fully utilized and settled sample cycle")
    frappe.db.commit()
    return _summary(contract.name)


def _summary(contract_name):
    contract = frappe.get_doc("Forward Contract", contract_name)
    utilization = frappe.db.get_value(
        "Forward Contract Utilization",
        {"forward_contract": contract.name, "docstatus": 1},
        ["name", "sales_invoice", "utilized_amount", "forex_gain_loss"],
        as_dict=True,
    )
    settlement = frappe.db.get_value(
        "Forward Contract Settlement",
        {"forward_contract": contract.name, "docstatus": 1},
        [
            "name",
            "settlement_amount",
            "forward_value",
            "actual_value",
            "gain_loss",
            "hedge_gain_loss",
            "journal_entry",
        ],
        as_dict=True,
    )
    return {
        "contract": contract.name,
        "contract_number": contract.contract_number,
        "status": contract.status,
        "docstatus": contract.docstatus,
        "sales_order": contract.sales_order,
        "contract_amount": contract.contract_amount,
        "utilized_amount": contract.utilized_amount,
        "available_amount": contract.available_amount,
        "utilization": utilization,
        "settlement": settlement,
    }
