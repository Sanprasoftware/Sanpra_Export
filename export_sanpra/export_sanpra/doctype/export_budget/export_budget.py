# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.document import flt
# import flt


class ExportBudget(Document):

	def before_save(self):
		self.validate_budget_amount()

	def on_submit(self):
		self.create_multiple_budget()

	def on_cancel(self):
		self.cancel_linked_budgets()

	def cancel_linked_budgets(self):
		budget_names = frappe.get_all(
			"Budget",
			filters={"custom_export_budget": self.name, "docstatus": 1},
			pluck="name",
		)

		for budget_name in budget_names:
			frappe.get_doc("Budget", budget_name).cancel()
	
	def validate_budget_amount(self):
		butget_amount = 0
		if self.budget_accounts:
			for row in self.budget_accounts:
				butget_amount += row.budget_amount
			# frappe.throw(str(butget_amount))
			self.budget_amount = butget_amount
			# frappe.throw("Total Budget Amount Not Match to sum of Budget Amount in Budget Accounts table.")

	def create_multiple_budget(self):
		if self.budget_accounts:
			for row in self.budget_accounts:
				new_doc = frappe.new_doc("Budget")
				new_doc.custom_export_budget = self.name
				new_doc.budget_against = self.budget_against
				new_doc.company = self.company
				new_doc.from_fiscal_year = self.from_fiscal_year
				new_doc.to_fiscal_year = self.to_fiscal_year
				new_doc.cost_center = self.cost_center
				new_doc.account = row.account
				new_doc.project = self.project
				new_doc.distribution_frequency = self.distribution_frequency
				new_doc.budget_amount = row.budget_amount
				# new_doc.account = row.account
				# new_doc.amount = row.amount
				
				new_doc.applicable_on_material_request = self.applicable_on_material_request
				new_doc.action_if_annual_budget_exceeded_on_mr = self.action_if_annual_budget_exceeded_on_mr
				new_doc.action_if_accumulated_monthly_budget_exceeded_on_mr = self.action_if_accumulated_monthly_budget_exceeded_on_mr
				
				new_doc.applicable_on_purchase_order = self.applicable_on_purchase_order
				new_doc.action_if_annual_budget_exceeded_on_po = self.action_if_annual_budget_exceeded_on_po
				new_doc.action_if_accumulated_monthly_budget_exceeded_on_po = self.action_if_accumulated_monthly_budget_exceeded_on_po
				
				new_doc.applicable_on_booking_actual_expenses = self.applicable_on_booking_actual_expenses
				new_doc.action_if_annual_budget_exceeded = self.action_if_annual_budget_exceeded_on_actual
				new_doc.action_if_accumulated_monthly_budget_exceeded = self.action_if_accumulated_monthly_budget_exceeded_on_actual
				
				new_doc.applicable_on_cumulative_expense = self.applicable_on_cumulative_expense
				new_doc.action_if_annual_exceeded_on_cumulative_expense = self.action_if_anual_budget_exceeded_on_cumulative_expense
				new_doc.action_if_accumulated_monthly_exceeded_on_cumulative_expense = self.action_if_accumulated_monthly_exceeded_on_cumulative_expense
				
				new_doc.revision_of = self.revision_of

				new_doc.append("budget_distribution",{
					"amount": row.budget_amount,
					"start_date": self.budget_start_date,
					"end_date": self.budget_end_date
				})
				new_doc.save()
				new_doc.submit()

	
	@frappe.whitelist()
	def get_budget_accounts(self):
		if self.budget_against == "Project":
			quotation = frappe.get_value("Quotation", {"custom_project": self.project}, "name")
			# frappe.throw(str(quotation))
			export_quotation = frappe.get_doc("Export Quotation s", quotation)

			sales_order_commission = frappe.get_value("Sales Order", {"project": self.project}, "total_commission")
			# frappe.throw(str(sales_order_commission))

			other_export_expenses_nfpl = (
				flt(export_quotation.wc_interest) +
				flt(export_quotation.silica_gel) +
				flt(export_quotation.craft_paper) +
				flt(export_quotation.fumigation_cost) +
				(flt(export_quotation.no_of_fcl) * 1000)
			)
			accounts = [
				{
					"account": "OCEAN FREIGHT CHARGES - NFPL",
					"budget_amount": flt(export_quotation.cnf_ocean_freight)
				},
				{
					"account": "Cost of Goods Sold - NFPL",
					"budget_amount": flt(export_quotation.cargo_pur_amt)
				},
				{
					"account": "CHA CLEARING EXPENSES - NFPL",
					"budget_amount": flt(export_quotation.cha_clearing_cost_fob)
				},
				{
					"account": "INSPECTION & TECH. CHARGES (EXPORT) - NFPL",
					"budget_amount": flt(export_quotation.surveyor_cost_fob)
				},
				{
					"account": "BROKERAGE AND COMMISION (PURCHASES) - NFPL",
					"budget_amount": flt(export_quotation.purc_brokaerage_fob)
				},
				{
					"account": "ECGC Insurance Charges - NFPL",
					"budget_amount": flt(export_quotation.ecgc_fob)
				},
				{
					"account": "OTHER EXPORT EXPENSES - NFPL",
					"budget_amount": flt(other_export_expenses_nfpl)
				},
				{
					"account": "TERMINAL HANDELING CHARGES - NFPL",
					"budget_amount": flt(export_quotation.thc_cost)
				},
				{
					"account": "CIF Insurance - NFPL",
					"budget_amount": flt(export_quotation.cif_insurance_cost)
				},
				{
					"account": "Export Duty Expenses - NFPL",
					# "budget_amount": flt(export_quotation.cnf_ocean_freight)
					"budget_amount": 0
				},
				{
					"account": "Brokerage & Commision on Export Sales - NFPL",
					"budget_amount": flt(sales_order_commission)  		## Fetch from Sales Order
				},
				{
					"account": "Additional Certificate Charges - NFPL",
					"budget_amount": flt(export_quotation.additional_certificate_fob)
				},
				{
					"account": "Local Transport DPDS - NFPL",
					"budget_amount": flt(export_quotation.local_transp_dpds_fob)
				},
			] 

			# frappe.throw(str(accounts))
			self.set("budget_accounts", [])
			for row in accounts:
				self.append("budget_accounts", {
					"account": row.get("account"),
					"budget_amount": row.get("budget_amount")
				})
			return self.budget_accounts
