import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 300,
		},
		{
			"label": _("Purchase Receipt No"),
			"fieldname": "purchase_receipt",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 180,
		},
		{
			"label": _("PR Date"),
			"fieldname": "purchase_receipt_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Purchase Receipt Net Amount"),
			"fieldname": "purchase_receipt_amount",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": _("Purchase Invoice ID"),
			"fieldname": "purchase_invoice",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 180,
		},
		{
			"label": _("PI Date"),
			"fieldname": "purchase_invoice_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Purchase Invoice Net Amount"),
			"fieldname": "purchase_invoice_amount",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": _("Difference"),
			"fieldname": "difference",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters):
	pr_conditions = [
		"pr.docstatus = 1",
		"coalesce(pr.is_internal_supplier, 0) = 0",
		"coalesce(pr.inter_company_reference, '') = ''",
		"coalesce(supplier.is_internal_supplier, 0) = 0",
		"coalesce(supplier.represents_company, '') = ''",
	]
	values = {}

	if filters.get("purchase_receipt"):
		pr_conditions.append("pr.name = %(purchase_receipt)s")
		values["purchase_receipt"] = filters.get("purchase_receipt")

	if filters.get("supplier"):
		pr_conditions.append("pr.supplier = %(supplier)s")
		values["supplier"] = filters.get("supplier")

	if filters.get("from_date"):
		pr_conditions.append("pr.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		pr_conditions.append("pr.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	pr_rows = frappe.db.sql(
		f"""
		select
			pr.name as purchase_receipt,
			pr.net_total as purchase_receipt_amount,
			pr.supplier_name,
			pr.posting_date as purchase_receipt_date
		from `tabPurchase Receipt` pr
		left join `tabSupplier` supplier on supplier.name = pr.supplier
		where {' and '.join(pr_conditions)}
		order by pr.posting_date, pr.name
		""",
		values,
		as_dict=1,
	)

	if not pr_rows:
		return []

	pr_names = [row.purchase_receipt for row in pr_rows]
	invoice_map = get_invoice_map(pr_names)

	data = []
	total_pr_amount = 0.0
	total_pi_amount = 0.0
	total_difference = 0.0

	for pr_row in pr_rows:
		invoice_rows = invoice_map.get(pr_row.purchase_receipt, [])
		pr_total_pi_amount = sum(flt(row.purchase_invoice_amount) for row in invoice_rows)
		difference = flt(pr_row.purchase_receipt_amount) - pr_total_pi_amount

		total_pr_amount += flt(pr_row.purchase_receipt_amount)
		total_pi_amount += pr_total_pi_amount
		total_difference += difference

		if not invoice_rows:
			data.append(
				{
					"purchase_receipt": pr_row.purchase_receipt,
					"purchase_receipt_amount": pr_row.purchase_receipt_amount,
					"purchase_receipt_date": pr_row.purchase_receipt_date,
					"supplier_name": pr_row.supplier_name,
					"purchase_invoice": None,
					"purchase_invoice_date": None,
					"purchase_invoice_amount": None,
					"difference": difference,
				}
			)
			continue

		for idx, inv_row in enumerate(invoice_rows):
			data.append(
				{
					"purchase_receipt": pr_row.purchase_receipt if idx == 0 else None,
					"purchase_receipt_date": pr_row.purchase_receipt_date if idx == 0 else None,
					"purchase_receipt_amount": pr_row.purchase_receipt_amount if idx == 0 else None,
					"supplier_name": pr_row.supplier_name if idx == 0 else None,
					"purchase_invoice": inv_row.purchase_invoice,
					"purchase_invoice_date": inv_row.purchase_invoice_date,
					"purchase_invoice_amount": inv_row.purchase_invoice_amount,
					"difference": difference if idx == 0 else None,
				}
			)

	data.append(
		{
			"purchase_receipt": _("Total"),
			"purchase_receipt_date": None,
			"purchase_receipt_amount": total_pr_amount,
			"supplier_name": None,
			"purchase_invoice": None,
			"purchase_invoice_date": None,
			"purchase_invoice_amount": total_pi_amount,
			"difference": total_difference,
		}
	)

	return data


def get_invoice_map(pr_names):
	values = {"pr_names": tuple(pr_names)}

	# Direct Purchase Invoice Item -> Purchase Receipt link
	direct_rows = frappe.db.sql(
		"""
		select
			coalesce(nullif(pii.purchase_receipt, ''), pri.parent) as purchase_receipt,
			pi.name as purchase_invoice,
			sum(pii.amount) as purchase_invoice_amount,
			max(pi.posting_date) as purchase_invoice_date
		from `tabPurchase Invoice Item` pii
		inner join `tabPurchase Invoice` pi on pi.name = pii.parent
		left join `tabSupplier` supplier on supplier.name = pi.supplier
		left join `tabPurchase Receipt Item` pri on pri.name = pii.pr_detail
		where pi.docstatus = 1
			and coalesce(pi.is_internal_supplier, 0) = 0
			and coalesce(pi.inter_company_invoice_reference, '') = ''
			and coalesce(supplier.is_internal_supplier, 0) = 0
			and coalesce(supplier.represents_company, '') = ''
			and (
				pii.purchase_receipt in %(pr_names)s
				or pri.parent in %(pr_names)s
			)
		group by coalesce(nullif(pii.purchase_receipt, ''), pri.parent), pi.name
		""",
		values,
		as_dict=1,
	)

	# Reverse link when Purchase Receipt is created from Purchase Invoice.
	pi_to_pr_rows = frappe.db.sql(
		"""
		select
			pri.parent as purchase_receipt,
			pi.name as purchase_invoice,
			sum(pri.amount) as purchase_invoice_amount,
			max(pi.posting_date) as purchase_invoice_date
		from `tabPurchase Receipt Item` pri
		inner join `tabPurchase Invoice Item` pii on pii.name = pri.purchase_invoice_item
		inner join `tabPurchase Invoice` pi on pi.name = pii.parent
		left join `tabSupplier` supplier on supplier.name = pi.supplier
		where pri.docstatus = 1
			and pi.docstatus = 1
			and coalesce(pi.is_internal_supplier, 0) = 0
			and coalesce(pi.inter_company_invoice_reference, '') = ''
			and coalesce(supplier.is_internal_supplier, 0) = 0
			and coalesce(supplier.represents_company, '') = ''
			and coalesce(pri.purchase_invoice_item, '') != ''
			and pri.parent in %(pr_names)s
		group by pri.parent, pi.name
		""",
		values,
		as_dict=1,
	)

	# Fallback when Purchase Receipt is linked through PO detail.
	fallback_rows = frappe.db.sql(
		"""
		select
			pri.parent as purchase_receipt,
			pi.name as purchase_invoice,
			sum(pii.amount * pri.amount / nullif(po_pr_amount.total_pr_amount, 0)) as purchase_invoice_amount,
			max(pi.posting_date) as purchase_invoice_date
		from `tabPurchase Invoice Item` pii
		inner join `tabPurchase Invoice` pi on pi.name = pii.parent
		left join `tabSupplier` supplier on supplier.name = pi.supplier
		inner join `tabPurchase Receipt Item` pri on pri.purchase_order_item = pii.po_detail
		inner join (
			select purchase_order_item, sum(amount) as total_pr_amount
			from `tabPurchase Receipt Item`
			where docstatus = 1
			group by purchase_order_item
		) po_pr_amount on po_pr_amount.purchase_order_item = pii.po_detail
		where pi.docstatus = 1
			and coalesce(pi.is_internal_supplier, 0) = 0
			and coalesce(pi.inter_company_invoice_reference, '') = ''
			and coalesce(supplier.is_internal_supplier, 0) = 0
			and coalesce(supplier.represents_company, '') = ''
			and (pii.purchase_receipt is null or pii.purchase_receipt = '')
			and pri.parent in %(pr_names)s
		group by pri.parent, pi.name
		""",
		values,
		as_dict=1,
	)

	combined = {}
	for row in direct_rows + pi_to_pr_rows + fallback_rows:
		key = (row.purchase_receipt, row.purchase_invoice)
		existing = combined.get(key)
		if not existing:
			combined[key] = row
			continue

		if flt(row.purchase_invoice_amount) > flt(existing.purchase_invoice_amount):
			existing.purchase_invoice_amount = row.purchase_invoice_amount
		if row.purchase_invoice_date and (
			not existing.purchase_invoice_date or row.purchase_invoice_date < existing.purchase_invoice_date
		):
			existing.purchase_invoice_date = row.purchase_invoice_date

	invoice_map = {}
	for row in combined.values():
		invoice_map.setdefault(row.purchase_receipt, []).append(row)

	for pr_name, rows in invoice_map.items():
		invoice_map[pr_name] = sorted(rows, key=lambda d: ((d.posting_date or ""), d.purchase_invoice))

	return invoice_map
