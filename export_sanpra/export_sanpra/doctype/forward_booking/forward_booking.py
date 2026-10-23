# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_sales_orders(doctype, txt, searchfield, start, page_len, filters):
	"""Return submitted Global Sales Orders with an unbooked balance."""
	if not frappe.has_permission("Sales Order", "read"):
		return []

	start = int(start or 0)
	page_len = int(page_len or 20)
	search = f"%{txt or ''}%"

	# Use SQL for the field-to-field comparison, then get_list to apply the
	# user's Sales Order row permissions before returning link results.
	candidates = frappe.db.sql(
		"""select name from `tabSales Order`
		where docstatus = 1
			and custom_sales_order_type = 'Global'
			and total - ifnull(custom_forward_booking_amount, 0) != 0
			and (name like %(search)s or customer like %(search)s or customer_name like %(search)s)
		order by modified desc
		limit %(start)s, %(page_len)s""",
		{"search": search, "start": start, "page_len": page_len},
		as_dict=True,
	)
	names = [row.name for row in candidates]
	if not names:
		return []

	visible = frappe.get_list(
		"Sales Order",
		filters={"name": ["in", names], "docstatus": 1, "custom_sales_order_type": "Global"},
		fields=["name", "customer", "customer_name", "total", "custom_forward_booking_amount"],
		limit_page_length=len(names),
	)
	return [
		[row.name, f"{row.name}: {row.customer_name or row.customer}", f"{row.total - flt(row.custom_forward_booking_amount)} available"]
		for row in visible
		if flt(row.total) - flt(row.custom_forward_booking_amount) != 0
	]

class ForwardBooking(Document):
	def before_save(self):
		for row in self.items:
			row.pending_amount = flt(row.sales_order_amount) - flt(row.booking_amount)

	# def on_submit(self):
	# 	for row in self.items:
	# 		if row.sales_order:
	# 			existing_booking_amount = flt(
	# 				frappe.db.get_value("Sales Order", row.sales_order, "custom_forward_booking_amount")
	# 			)
	# 			if existing_booking_amount > 0 and flt(row.booking_amount) > existing_booking_amount:
	# 				frappe.throw(
	# 					f"Booking Amount for Sales Order {row.sales_order} cannot exceed the already booked amount ({existing_booking_amount})."
	# 				)

	# 			frappe.db.set_value("Sales Order",row.sales_order,
	# 				{
	# 					"custom_forward_booking_amount": flt(row.booking_amount)
	# 				},
	# 			)
	def on_submit(self):
		for row in self.items:
			if row.sales_order:
				existing_booking_amount = flt(
					frappe.db.get_value(
						"Sales Order", row.sales_order, "custom_forward_booking_amount"
					)
				)
				new_booking_amount = flt(row.booking_amount)

				if existing_booking_amount > 0 and new_booking_amount > existing_booking_amount:
					frappe.throw(
						f"Booking Amount for Sales Order {row.sales_order} cannot exceed the already booked amount ({existing_booking_amount})."
					)

				total_booking_amount = existing_booking_amount + new_booking_amount
				sales_order_total = flt(
					frappe.db.get_value("Sales Order", row.sales_order, "total")
				)

				if total_booking_amount > sales_order_total:
					frappe.throw(
						f"Booking Amount for Sales Order {row.sales_order} cannot exceed the available amount. "
						f"Already booked amount: {existing_booking_amount}, "
						f"New booking amount: {new_booking_amount}."
					)

				frappe.db.set_value("Sales Order",row.sales_order,"custom_forward_booking_amount",total_booking_amount)

