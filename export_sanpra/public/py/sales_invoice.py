import frappe


def create_journal_entry_for_global_invoice(doc, method=None):
    if doc.custom_sales_invoice_type != "Global":
        return
    duty_drawback_amount = frappe.db.get_value(
        "Export Sales Invoice s",
        {"sales_invoice_id": doc.name},
        "duty_drawback_amount_copy",
    )
    if duty_drawback_amount is None:
        frappe.throw(
            f"Export Sales Invoice s is missing for Sales Invoice {doc.name}."
        )

    existing_je_name = frappe.db.get_value(
        "Journal Entry", {"custom_reference_id": doc.name}, "name"
    )
    if existing_je_name:
        je = frappe.get_doc("Journal Entry", existing_je_name)
    else:
        je = frappe.new_doc("Journal Entry")
    if existing_je_name and je.docstatus != 0:
        frappe.db.set_value(
            "Sales Invoice", doc.name, "custom_journal_entry_id", je.name,
            update_modified=False,
        )
        return

    settings = frappe.get_single("Sanpra Setting")

    debit_account = settings.debit_account
    credit_account = settings.credit_account

    if not debit_account or not credit_account:
        frappe.throw("Please set Debit Account and Credit Account in Sanpra Setting.")

    je.voucher_type = "Journal Entry"
    je.naming_series = "K/JV.FY./.#"
    je.posting_date = doc.posting_date
    je.custom_cost_center = doc.cost_center
    je.custom_reference_id = doc.name
    je.cheque_no = doc.shipping_bill_number
    je.cheque_date = doc.shipping_bill_date

    je.set("accounts", [])
    je.append("accounts", {
        "account": debit_account,
        "debit_in_account_currency": duty_drawback_amount,
        "credit_in_account_currency": 0,
        "cost_center": doc.cost_center
    })

    je.append("accounts", {
        "account": credit_account,
        "debit_in_account_currency": 0,
        "credit_in_account_currency": duty_drawback_amount,
        "cost_center": doc.cost_center
    })

    je.save(ignore_permissions=True)
    je.submit()
    frappe.db.set_value(
        "Sales Invoice", doc.name, "custom_journal_entry_id", je.name,
        update_modified=False,
    )


def cancel_linked_journal_entry(doc, method=None):
    journal_entry_name = doc.get("custom_journal_entry_id") or frappe.db.get_value(
        "Journal Entry", {"custom_reference_id": doc.name}, "name"
    )
    if not journal_entry_name or not frappe.db.exists("Journal Entry", journal_entry_name):
        return

    journal_entry = frappe.get_doc("Journal Entry", journal_entry_name)
    if journal_entry.docstatus == 1:
        journal_entry.flags.ignore_permissions = True
        journal_entry.cancel()


def mark_sales_invoice_drawback_jv_created(doc, method=None):
    invoice_name = doc.get("custom_reference_id")

    if invoice_name and frappe.db.exists("Sales Invoice", invoice_name):
        frappe.db.set_value(
            "Sales Invoice",
            invoice_name,
            "custom_duty_drawback_jv_create",
            1,
            update_modified=False,
        )
