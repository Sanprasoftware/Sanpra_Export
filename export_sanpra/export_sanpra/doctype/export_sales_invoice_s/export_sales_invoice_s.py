# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ExportSalesInvoices(Document):
	def on_update(self):
		self.update_sales_invoice_fob_value()

	def on_submit(self):
		self.update_sales_invoice_fob_value()

	def update_sales_invoice_fob_value(self):
		if not self.sales_invoice_id:
			return

		frappe.db.set_value(
			"Sales Invoice",
			self.sales_invoice_id,
			"custom_fob_invoice_value_inr",
			self.fob_value_inr,
			update_modified=False,
		)

	def validate(self):
		if not flt(self.duty_drawback_amount_copy):
			self.duty_drawback_amount_copy = self.duty_drawback_amount
		if not flt(self.rodtepe_amount_copy):
			self.rodtepe_amount_copy = self.rodtepe_amount
		if not flt(self.other_deduction_usd_copy):
			self.other_deduction_usd_copy = self.other_deduction_usd
		if not flt(self.export_duty_inr_copy):
			self.export_duty_inr_copy = self.export_duty_inr

		invoice_total = 0
		invoice_base_total = 0
		if self.sales_invoice_id:
			invoice = frappe.get_doc("Sales Invoice", self.sales_invoice_id)
			invoice_total = invoice.total or 0
			invoice_base_total = flt(invoice.base_total)
			self.igst_assessable_value_inr = flt(invoice.base_total)
			self.less_freight_insuranceinr = (
				flt(self.less_freight_insuranceusd) * flt(invoice.conversion_rate)
			)
			self.packing_charges_inr = flt(self.packing_charges) * flt(invoice.conversion_rate)
			self.igst_inr = get_igst_inr(invoice.name)
		else:
			self.igst_inr = 0
			self.igst_assessable_value_inr = 0
			self.less_freight_insuranceinr = 0
			self.packing_charges_inr = 0
			self.other_deduction_inr = 0

		export_duty_rate = flt(self.export_duty_rate_)
		if 100 + export_duty_rate:
			self.export_duty_usd = (
				(flt(invoice_total) - flt(self.less_freight_insuranceusd) - flt(self.packing_charges))
				/ (100 + export_duty_rate)
				* export_duty_rate
			)
		else:
			self.export_duty_usd = 0
		self.export_duty_inr = flt(self.export_duty_usd) * flt(
			invoice.conversion_rate if self.sales_invoice_id else 0
		)
		self.other_deduction_usd = flt(self.export_duty_usd)
		self.other_deduction_inr = flt(self.other_deduction_usd) * flt(
			invoice.conversion_rate if self.sales_invoice_id else 0
		)
		self.fob_value_usd = (
			flt(invoice_total)
			- flt(self.less_freight_insuranceusd)
			- flt(self.packing_charges)
			- flt(self.other_deduction_usd)
		)
		self.fob_value_inr = flt(self.fob_value_usd) * flt(
			invoice.conversion_rate if self.sales_invoice_id else 0
		)
		self.amount_after_igst_duty = flt(self.igst_inr) + invoice_base_total


@frappe.whitelist()
def get_igst_inr(sales_invoice_id):
	if not sales_invoice_id:
		return 0

	invoice = frappe.get_doc("Sales Invoice", sales_invoice_id)
	igst_rate = next(
		(flt(item.get("igst_rate")) for item in invoice.items if item.get("igst_rate") is not None),
		0,
	)
	return flt(invoice.base_total) * igst_rate / 100

	# def before_save(self):
	# 	self.less_freight_insuranceusd = flt(self.ocean_freight_usdfcl) + flt(self.cif_insurance)
	# 	self.calculate_fob()

	# def calculate_fob(self):
	# 	si = frappe.get_value(
	# 		"Sales Invoice",
	# 		self.sales_invoice_id,
	# 		["base_total", "total", "conversion_rate"],
	# 		as_dict=True
	# 	)

	# 	if not si:
	# 		return

	# 	##Change by Karpe sir 24/09/2026
	# 	less_freight = flt(self.less_freight_insuranceusd)
	# 	packing_charges = flt(self.packing_charges)
	# 	other_deduction_usd = flt(self.other_deduction_usd)

	# 	self.fob_value_usd = flt(si.total) - less_freight - packing_charges - other_deduction_usd
		
	# 	# self.fob_invoice_value_inr = (
	# 	# 	flt(si.base_total)
	# 	# 	- (less_freight  * flt(si.conversion_rate))
	# 	# )

	# 	self.fob_invoice_value_inr = (
	# 		flt(si.base_total)
	# 		- (less_freight * flt(si.conversion_rate))
	# 		- (packing_charges * flt(si.conversion_rate))
	# 		- (other_deduction_usd * flt(si.conversion_rate))
	# 	)

	# 	frappe.db.set_value(
	# 		"Sales Invoice",
	# 		self.sales_invoice_id,
	# 		{
	# 			"custom_fob_value_usd": self.fob_value_usd,
	# 			"custom_fob_invoice_value_inr": self.fob_invoice_value_inr,
	# 		},
	# 		update_modified=False
	# 	)
