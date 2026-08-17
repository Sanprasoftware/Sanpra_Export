# import frappe

# @frappe.whitelist()
# def validate_supplier_invoice_no(doc, method=None):
#     if doc.bill_no:
#         existing_invoice = frappe.get_all(
#             "Purchase Invoice",
#             filters={
#                 "supplier_name": doc.supplier_name,
#                 "bill_no": doc.bill_no,
#                 "name": ["!=", doc.name],
#                 "docstatus": ["!=", 2]
#             },
#             fields=["name"]
#         )
#         if existing_invoice:
#             frappe.throw(f"Supplier Invoice No '{doc.bill_no}' already exists in Purchase Invoice '{existing_invoice[0].name}'.")

import frappe
from frappe.utils import getdate


@frappe.whitelist()
def validate_supplier_invoice_no(doc, method=None):
    if not doc.bill_no:
        return

    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ["<=", doc.posting_date],
            "year_end_date": [">=", doc.posting_date],
        },
        ["name", "year_start_date", "year_end_date"],
        as_dict=True
    )

    if not fiscal_year:
        frappe.throw(
            f"No Fiscal Year found for posting date {doc.posting_date}."
        )

    existing_invoice = frappe.get_all(
        "Purchase Invoice",
        filters={
            "supplier_name": doc.supplier_name,
            "bill_no": doc.bill_no,
            "posting_date": [
                "between",
                [fiscal_year.year_start_date, fiscal_year.year_end_date]
            ],
            "name": ["!=", doc.name],
            "docstatus": ["!=", 2]
        },
        fields=["name"]
    )

    if existing_invoice:
        frappe.throw(
            f"Supplier Invoice No '{doc.bill_no}' already exists in "
            f"Purchase Invoice '{existing_invoice[0].name}' "
            f"for fiscal year '{fiscal_year.name}'."
        )