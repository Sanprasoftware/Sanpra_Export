import uuid

import frappe
from frappe.utils import add_days, flt, today


def run():
    savepoint = "forex_transaction_audit"
    frappe.db.savepoint(savepoint)
    result = {}
    try:
        company = frappe.get_all("Company", filters={"default_currency": "INR"}, pluck="name", limit=1)[0]
        order = frappe.get_all(
            "Sales Order",
            filters={"company": company, "docstatus": 1, "currency": ["!=", "INR"], "grand_total": [">", 10]},
            fields=["name", "company", "customer", "currency", "grand_total"],
            order_by="modified desc",
            limit=1,
        )[0]
        bank = frappe.get_all("Bank", pluck="name", limit=1)[0]
        amount = min(flt(order.grand_total), 100)
        contract = frappe.get_doc({
            "doctype": "Forward Contract",
            "company": order.company,
            "contract_number": f"AUDIT-{uuid.uuid4().hex[:10].upper()}",
            "contract_type": "Export",
            "bank": bank,
            "booking_date": today(),
            "maturity_date": add_days(today(), 30),
            "currency": order.currency,
            "company_currency": "INR",
            "contract_amount": amount,
            "forward_rate": 84.5,
            "customer": order.customer,
            "sales_order": order.name,
            "sales_order_currency": order.currency,
            "sales_order_total": order.grand_total,
        }).insert(ignore_permissions=True)
        contract.submit()
        contract.reload()
        result["contract_submit"] = contract.status == "Open" and flt(contract.available_amount) == amount

        utilization = frappe.get_doc({
            "doctype": "Forward Contract Utilization",
            "company": order.company,
            "forward_contract": contract.name,
            "sales_order": order.name,
            "customer": order.customer,
            "utilization_date": today(),
            "currency": order.currency,
            "utilized_amount": amount * 0.6,
            "forward_rate": 84.5,
            "settlement_rate": 84.5,
            "reference_exchange_rate": 83.8,
        }).insert(ignore_permissions=True)
        utilization.submit()
        contract.reload()
        result["partial_utilization"] = contract.status == "Partly Utilized" and abs(flt(contract.available_amount) - amount * 0.4) < 0.001
        result["gain_loss"] = abs(flt(utilization.forex_gain_loss) - amount * 0.6 * 0.7) < 0.001

        cancellation_blocked = False
        try:
            contract.cancel()
        except frappe.ValidationError:
            cancellation_blocked = True
        result["cancellation_guard"] = cancellation_blocked

        utilization.cancel()
        contract.reload()
        result["utilization_cancel_recalculation"] = contract.status == "Open" and flt(contract.available_amount) == amount
        contract.cancel()
        result["ordered_cancellation"] = contract.docstatus == 2
        result["all_passed"] = all(result.values())
        return result
    finally:
        frappe.db.rollback(save_point=savepoint)
