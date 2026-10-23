# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_sales_invoices(doctype, txt, searchfield, start, page_len, filters):
	"""Return submitted Global invoices not already used in a RODTEP Script."""
	if not frappe.has_permission("Sales Invoice", "read"):
		return []

	start = int(start or 0)
	page_len = int(page_len or 20)
	search = f"%{txt or ''}%"
	invoices = frappe.get_list(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"is_return": 0,
			"custom_sales_invoice_type": "Global",
			"custom_rodtep_script_create": 0,
		},
		or_filters=[["name", "like", search], ["customer", "like", search]],
		fields=["name", "customer", "customer_name"],
		order_by="modified desc",
		start=start,
		page_length=page_len,
	)
	return [
		[row.name, row.name, row.customer_name or row.customer]
		for row in invoices
	]


class RODTEPScript(Document):

    def before_save(self):
        total = 0

        for row in self.rodtep_invoice_allocation:
            row.disallocate = flt(row.invoice_rodtep_amount) - flt(row.allocate)
            total += flt(row.allocate)

        self.total_allocate_amt = total

    def on_submit(self):

        # Get Item and Warehouse from Sanpra Setting
        rodtep_item, warehouse = frappe.db.get_value(
            "Sanpra Setting", None, ["rodtep_item", "warehouse"]
        ) or (None, None)

        if not rodtep_item or not warehouse:
            frappe.throw("Please set Item and Warehouse in Sanpra Setting.")

        # 1. Create Batch First
        batch = frappe.get_doc({
            "doctype": "Batch",
            "batch_id": self.name,
            "item": rodtep_item,
            "manufacturing_date": self.date,
            "reference_doctype": self.doctype,
			"reference_name": self.name
        })

        batch.insert(ignore_permissions=True)

        # 2. Update Sales Invoice Checkbox
        for row in self.rodtep_invoice_allocation:
            if row.sales_invoice:
                frappe.db.set_value(
                    "Sales Invoice",
                    row.sales_invoice,
                    {
                        "custom_rodtep_script_create": 1,
                        "custom_allocate_amount": flt(row.allocate),
                    },
                )

        # 3. Create Stock Entry
        cost_center = self.cost_center

        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "naming_series": "MTR/.FY./.#",
            "cost_center": cost_center,
            "posting_date" : self.date,
            "custom_rodtep_script_id": self.name,
            "items": [{
                "item_code": rodtep_item,
                "qty": 1,
                "basic_rate": flt(self.total_allocate_amt),
                "t_warehouse": warehouse,
                "cost_center": cost_center,
                "use_serial_batch_fields":1,
                "batch_no": batch.name
            }]
        })

        se.insert(ignore_permissions=True)
        se.submit()

        self.db_set("stock_entry_id", se.name)

    def on_cancel(self):
        if not self.stock_entry_id:
            return

        stock_entry = frappe.get_doc("Stock Entry", self.stock_entry_id)
        if stock_entry.docstatus == 1:
            stock_entry.flags.ignore_permissions = True
            stock_entry.cancel()
