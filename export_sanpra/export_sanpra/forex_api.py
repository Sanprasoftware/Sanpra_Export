import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, today


@frappe.whitelist()
def make_forward_contract(source_name, target_doc=None):
    def set_values(source, target):
        target.contract_type = "Export"
        target.sales_order = source.name
        target.customer = source.customer
        target.company = source.company
        target.currency = source.currency
        target.sales_order_currency = source.currency
        target.sales_order_total = source.grand_total
        target.company_currency = frappe.get_cached_value("Company", source.company, "default_currency")
        target.booking_date = today()
        target.append("sales_orders", {
            "sales_order": source.name,
            "sales_order_total": source.grand_total,
            "booked_amount": source.grand_total,
        })

    return get_mapped_doc("Sales Order", source_name, {
        "Sales Order": {"doctype": "Forward Contract", "validation": {"docstatus": ["=", 1]}}
    }, target_doc, set_values)


@frappe.whitelist()
def make_utilization(forward_contract, sales_invoice=None):
    fc = frappe.get_doc("Forward Contract", forward_contract)
    if fc.docstatus != 1 or fc.status not in ("Open", "Partly Utilized"):
        frappe.throw(_("Forward Contract is not available"))
    doc = frappe.new_doc("Forward Contract Utilization")
    for field in ("company", "sales_order", "customer", "currency", "forward_rate"):
        doc.set(field, fc.get(field))
    doc.forward_contract = fc.name
    doc.sales_invoice = sales_invoice
    doc.utilization_date = today()
    eligible = flt(fc.available_amount)
    if sales_invoice:
        eligible = min(eligible, flt(frappe.db.get_value("Sales Invoice", sales_invoice, "outstanding_amount")))
    doc.utilized_amount = eligible
    if sales_invoice:
        doc.reference_exchange_rate = flt(frappe.db.get_value("Sales Invoice", sales_invoice, "conversion_rate"))
    return doc


@frappe.whitelist()
def eligible_contracts(company, customer, currency, sales_order=None):
    filters = {
        "company": company,
        "customer": customer,
        "currency": currency,
        "docstatus": 1,
        "status": ["in", ["Open", "Partly Utilized"]],
        "available_amount": [">", 0],
    }
    if sales_order:
        names = frappe.db.sql_list("""select distinct fc.name from `tabForward Contract` fc
            left join `tabForward Contract Sales Order` row on row.parent=fc.name
            where fc.sales_order=%s or row.sales_order=%s""", (sales_order, sales_order))
        if not names:
            return []
        filters["name"] = ["in", names]
    return frappe.get_all("Forward Contract", filters=filters,
        fields=["name", "contract_number", "sales_order", "forward_rate", "available_amount", "maturity_date"],
        order_by="maturity_date")
