# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ExportSalesInvoices(Document):
	
	def before_save(self):
		self.calculate_fob()

	def calculate_fob(self):
		si = frappe.get_value(
			"Sales Invoice",
			self.sales_invoice_id,
			["base_total", "total", "conversion_rate"],
			as_dict=True
		)

		if not si:
			return

		less_freight = flt(self.less_freight_insuranceusd)

		self.fob_value_usd = flt(si.total) - less_freight
		self.fob_invoice_value_inr = (
			flt(si.base_total)
			- (less_freight * flt(si.conversion_rate))
		)

		frappe.db.set_value(
			"Sales Invoice",
			self.sales_invoice_id,
			{
				"custom_fob_value_usd": self.fob_value_usd,
				"custom_fob_invoice_value_inr": self.fob_invoice_value_inr,
			},
			update_modified=False
		)