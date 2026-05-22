import frappe
from frappe.query_builder.functions import IfNull


def apply_tax_withholding_patches():
	from erpnext.accounts.doctype.tax_withholding_entry.tax_withholding_entry import (
		TaxWithholdingController,
	)

	if getattr(TaxWithholdingController, "_export_sanpra_threshold_patch", False):
		return

	TaxWithholdingController._export_sanpra_original_create_entries_for_category = (
		TaxWithholdingController._create_entries_for_category
	)
	TaxWithholdingController._get_unused_threshold = _get_unused_threshold
	TaxWithholdingController._create_entries_for_category = _create_entries_for_category
	TaxWithholdingController._export_sanpra_threshold_patch = True


def _create_entries_for_category(self, category):
	if not category.tax_on_excess_amount:
		return self._export_sanpra_original_create_entries_for_category(category)

	entries = []

	if not category.taxable_amount:
		return entries

	if category.unused_threshold:
		entries.append(self._create_threshold_exemption_entry(category))
		if category.taxable_amount <= 0:
			return entries

	entry = self._create_default_entry(category)
	entry.update(
		{
			"taxable_amount": category.taxable_amount,
			"withholding_amount": self.compute_withheld_amount(
				category.taxable_amount,
				category.tax_rate,
				round_off_tax_amount=category.round_off_tax_amount,
			),
		}
	)
	entries.append(entry)

	return entries


def _get_unused_threshold(self, category):
	"""Count all prior below-threshold taxable amounts for tax-on-excess TDS."""
	if not category.tax_on_excess_amount:
		return 0

	entry = frappe.qb.DocType("Tax Withholding Entry")
	rows = (
		self._base_threshold_query(category)
		.where(
			(entry.status == "Under Withheld")
			| (
				(entry.status == "Settled")
				& (IfNull(entry.under_withheld_reason, "") == "Threshold Exemption")
			)
		)
		.run()
	)

	consumed_threshold = sum(row[1] or 0 for row in rows)
	return max(category.cumulative_threshold - consumed_threshold, 0)
