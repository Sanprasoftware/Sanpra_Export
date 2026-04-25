# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
# from erpnext.erpnext.setup.doctype import incoterm


class ExportQuotations(Document):
	
	def before_save(self):
		self.all_calculations()

	def all_calculations(self):
		
		quotation_values = frappe.db.get_value(
			"Quotation", 
			{"name": self.quotation_id},
			["conversion_rate", "custom_total_export_duty", "total_qty", "custom_total_purchase_amt", "base_total", "incoterm"],
			as_dict=True,
		) or {}

		

	
		self.contracted_qty = quotation_values.get("total_qty")
		# self.contracted_qty = quotation_values.total_qty
		
		conversion_rate = flt(quotation_values.get("conversion_rate"))
		custom_total_export_duty = flt(quotation_values.get("custom_total_export_duty"))
		total_qty = flt(quotation_values.get("total_qty"))
		custom_total_purchase_amt = flt(quotation_values.get("custom_total_purchase_amt"))
		contracted_qty = flt(self.contracted_qty)
		no_of_fcl = flt(self.no_of_fcl)
		no_of_docs = flt(self.no_of_docs)
		ocean_frieght_fcl_doller = flt(self.ocean_frieght_fcl_doller)
		total_inr = flt(quotation_values.get("base_total"))
		incoterm_value = quotation_values.get("incoterm")	
		
		incoterm_doc = frappe.get_value("Incoterm", {"name": incoterm_value}, ["custom_cif_insurance_rate", "custom_amount"], as_dict=True) or {}

		self.cif_insurances = incoterm_doc.get("custom_cif_insurance_rate", 0)
		stuffing = frappe.get_value("FOB Costing s", 
			{"name": self.type_of_stuffing}, 
			"*",
			as_dict=True
		) or 0
		
		# linear_currency = flt(self.linear_currency)
		linear_currency = flt(stuffing.get("linear_currency_")) if stuffing else 0


		item_map = {}
		total_rate = 0
		quotation_items = []
		if self.quotation_id:
			quotation_items = frappe.get_all(
				"Quotation Item",
				filters={"parent": self.quotation_id, "parenttype": "Quotation"},
				fields=["item_code", "custom_sales_comm_usd__mt", "rate", "custom_purc_brokaerage_amt", "custom__cargo_shortage_inr__mt", "custom_item_rate"],
			)

			
		
				# Group item rates
			for row in quotation_items:
				item = row.item_code
				rate = flt(row.custom_item_rate)

				if item not in item_map:
					item_map[item] = []

				item_map[item].append(rate)

			# Calculate avg for duplicates and sum
			for item, rates in item_map.items():
				if len(rates) > 1:
					total_rate += sum(rates) / len(rates)
				else:
					total_rate += rates[0]

		self.selling_rate = flt(total_rate)  



		# frappe.throw(str(conversion_rate))
		self.ocean_frieght_fcl_calcu = (ocean_frieght_fcl_doller * no_of_fcl * conversion_rate) + (linear_currency / 100)
		
		self.sales_commission_mt = sum(flt(item.custom_sales_comm_usd__mt) for item in quotation_items)

		self.cargo_pur_rate = custom_total_export_duty / total_qty if total_qty else 0
		
		
		

		self.cargo_purc_amt_dollar___mt = flt(self.cargo_purc_amt_rupees__mt) / conversion_rate if conversion_rate else 0
		self.export_expense_doller = flt(self.export_expense_rs__mt) / conversion_rate if conversion_rate else 0

		self.cost_of_export = flt(self.cargo_purc_amt_dollar___mt) + flt(self.export_expense_doller)
		self.selling_offer_rate_mt = flt(self.selling_rate) + flt(self.cargo_pur_rate)
		self.net_margin = flt(self.selling_offer_rate_mt) - flt(self.sales_commission_mt) - flt(self.cargo_pur_rate) - flt(self.cost_of_export)
		# self.net_margin = 
		self.margin = (flt(self.net_margin) / flt(self.selling_offer_rate_mt)) * 100 if flt(self.selling_offer_rate_mt) else 0
		
		self.local_transp_dpds_fob = flt(self.local_transp_dpds_rupees__mt) * contracted_qty if contracted_qty else 0


	
		# self.cha_clearing_cost_fob = no_of_fcl * flt(stuffing.cha_clearing_cost)
		if stuffing:
			self.cha_clearing_cost_fob = flt(self.no_of_fcl) * flt(stuffing.get("cha_clearing_cost"))
			self.surveyor_cost_fob = no_of_fcl * flt(stuffing.get("surveyor_cost"))
			self.administrative_cost_fob = no_of_fcl * flt(stuffing.get("administrative_cost"))
			self.other_cost = no_of_fcl * flt(stuffing.get("other_cost"))
		else:
			self.cha_clearing_cost_fob = 0
			self.surveyor_cost_fob = 0
			self.administrative_cost_fob = 0
			self.other_cost = 0

		fumigation = frappe.get_value("Fumigation s",	
			{"name": self.fumigation},
			"*",
			as_dict=True
		) or 0	
		
		if fumigation:	
			self.fumigation_cost = no_of_fcl * flt(fumigation.get("rate"))
		else:
			self.fumigation_cost = 0 

		discharge_country = frappe.get_value("Country", {"name": self.discharge_country}, ["custom_ecgc_rate_"], as_dict=True) or {}
		custom_ecgc_rate_ = flt(discharge_country.get("custom_ecgc_rate_"))

		self.ecgc_fob = flt(total_inr) * custom_ecgc_rate_ / 100 if total_inr else 0

		total_bank_charges = 0
		total_custom_int = 0
		quotation_doc = frappe.get_doc("Quotation", self.quotation_id)

		if quotation_doc.payment_schedule:
			for row in quotation_doc.payment_schedule:
				# bank_charges = frappe.get_value(
				# 	"Payment Term",
				# 	row.payment_term,
				# 	"custom_bank_charges"
				# ) or 0

				values = frappe.get_value(
					"Payment Term", 
					row.payment_term,
					["custom_bank_charges", "custom_int_"],  
					as_dict=True
				) or {}

				bank_charges = flt(values.get("custom_bank_charges", 0))
				custom_int = flt(values.get("custom_int_", 0))


				total_bank_charges += flt(bank_charges)
				total_custom_int += custom_int

		# final calculation
		self.bank_charges_fob = flt(no_of_docs) * total_bank_charges

		# self.wc_interest = ((flt(custom_total_purchase_amt) * flt(self.intrest_rate)) / 100) / 365 * flt(self.transits_days)
		self.wc_interest = ((flt(custom_total_purchase_amt) * flt(total_custom_int)) / 100) / 365 * flt(self.transits_days)

		self.fob_cost = (
			flt(self.local_transp_dpds_fob)
			+ flt(self.cha_clearing_cost_fob)
			+ flt(self.surveyor_cost_fob)
			+ flt(self.additional_certificate_fob)
			+ flt(self.purc_brokaerage_fob)
			+ flt(self.ecgc_fob)
			+ flt(self.bank_charges_fob)
			+ flt(self.administrative_cost_fob)
			+ flt(self.wc_interest)
			+ flt(self.cargo_shortage_cost)
			+ flt(self.other_cost)
			+ flt(self.fumigation_cost)
			+ flt(self.thc_cost)
			+ flt(self.silica_gel)
			+ flt(self.craft_paper)
		)

		# (Ocean Frieght FCL $ (Doller) * No of FCL * Exchange Rate) * linear currency %
		self.cnf_ocean_freight = flt(self.ocean_frieght_fcl_doller) * no_of_fcl * conversion_rate * linear_currency
		# self.cnf_ocean_freight = flt(self.ocean_frieght_fcl_calcu) + (flt(self.ocean_frieght_fcl_calcu) * flt(self.linear_currency) / 100)

		total_item_rate = sum(flt(item.rate) for item in quotation_items)
		item_count = len(quotation_items)
		avg_rate = total_item_rate / item_count if item_count else 0

		self.cif_insurance_cost = (flt(total_inr) * flt(self.cif_insurances) / 100) if total_inr else 0
		# 330*480*89*
		# if contracted_qty > 0:
		# 	# self.cif_insurance_cost = flt(avg_rate) * contracted_qty * conversion_rate * (flt(self.cif_insurance) / 100)
		# else:
		# 	self.cif_insurance_cost = 0 

		# self.cargo_pur_amt = flt(self.cargo_purc_amt_rupees__mt) * flt(total_qty)
		self.cargo_pur_amt = custom_total_purchase_amt


		

		self.purc_brokaerage_fob = sum(flt(item.custom_purc_brokaerage_amt) for item in quotation_items)
		
		
		

		
		self.cargo_shortage_cost = sum(flt(item.custom__cargo_shortage_inr__mt) for item in quotation_items)
		
		self.silica_gel = flt(self.silica_gel__kg_rate) * flt(self.silica_gel_kg__fcl) * flt(self.no_of_fcl)
		self.craft_paper = flt(self.craft_paper__kg_rate) * flt(self.craft_paper_kg_fcl) * flt(self.no_of_fcl)
		
		self.bank_charge = flt(self.bank_charge) * no_of_docs
		 
		# self.thc_cost = flt(self.thc_fcl_rupees) * flt(self.no_of_docs)
		self.thc_cost = flt(self.thc_fcl_rupees) * flt(no_of_fcl) #Change BY Devika Mam

		self.cin_insurance_calculation = (flt(self.ocean_frieght_fcl_doller) * flt(self.no_of_docs) * conversion_rate) * flt(linear_currency) / 100
		self.export_expense_total = flt(self.fob_cost) + flt(self.cnf_ocean_freight) + flt(self.cif_insurance_cost)
		self.fob_cost_mt_rs__mt = flt(self.fob_cost) / contracted_qty if contracted_qty else 0
		self.cin_ocean_freight_rs__mt = flt(self.cnf_ocean_freight) / contracted_qty if contracted_qty else 0
		self.cif_insurance_cost_rs__mt = flt(self.cif_insurance_cost) / contracted_qty if contracted_qty else 0
		self.cargo_purc_amt_rupees__mt = flt(self.cargo_pur_amt) / contracted_qty if contracted_qty else 0
		self.local_transp_dpds_rs__mt = flt(self.local_transp_dpds_fob) / contracted_qty if contracted_qty else 0

		# self.cha_clearing_cost_rs__mt = flt(self.cha_clearing_cost_fob) / flt(self.contracted_qty)
		if flt(self.contracted_qty):
			self.cha_clearing_cost_rs__mt = flt(self.cha_clearing_cost_fob) / flt(self.contracted_qty)
		else:
			self.cha_clearing_cost_rs__mt = 0
		
		self.surveyor_cost_rs__mt = flt(self.surveyor_cost_fob) / contracted_qty if contracted_qty else 0
		self.additional_certificate_rs__mt = flt(self.additional_certificate_fob) / contracted_qty if contracted_qty else 0
		self.purc_brokaerage_rs__mt = flt(self.purc_brokaerage_fob) / contracted_qty if contracted_qty else 0
		self.ecgc_rs__mt = flt(self.ecgc_fob) / contracted_qty if contracted_qty else 0
		self.bank_charges_rs__mt = flt(self.bank_charges_fob) / contracted_qty if contracted_qty else 0
		self.administrative_cost_rs__mt = flt(self.administrative_cost_fob) / contracted_qty if contracted_qty else 0
		self.wc_interest_rs__mt = flt(self.wc_interest) / contracted_qty if contracted_qty else 0
		self.cargo_shortage_rs__mt = flt(self.cargo_shortage_cost) / contracted_qty if contracted_qty else 0
		self.silica_gel_rs__mt = flt(self.silica_gel) / contracted_qty if contracted_qty else 0
		self.craft_paper_rs__mt = flt(self.craft_paper) / contracted_qty if contracted_qty else 0
		self.fumigation_rs__mt = flt(self.fumigation_cost) / contracted_qty if contracted_qty else 0
		self.other_cost_rs__mt = flt(self.other_cost) / contracted_qty if contracted_qty else 0
		self.thc_cost_rs__mt = flt(self.thc_cost) / contracted_qty if contracted_qty else 0
		self.export_expense_rs__mt = flt(self.export_expense_total) / contracted_qty if contracted_qty else 0
		
		self.fob_cost_mt_doller = flt(self.fob_cost_mt_rs__mt) / conversion_rate if conversion_rate else 0
		self.cnf_ocean_freight_doller = flt(self.cin_ocean_freight_rs__mt) / conversion_rate if conversion_rate else 0
		self.cif_insurance_cost_doller = flt(self.cif_insurance_cost_rs__mt) / conversion_rate if conversion_rate else 0
		
		self.local_transp_dpds_doller__mt = flt(self.local_transp_dpds_rs__mt) / conversion_rate if conversion_rate else 0
		self.cha_clearing_cost_doller__mt = flt(self.cha_clearing_cost_rs__mt) / conversion_rate if conversion_rate else 0
		self.surveyor_cost_doller__mt = flt(self.surveyor_cost_rs__mt) / conversion_rate if conversion_rate else 0
		self.additional_certificate_doller__mt = flt(self.additional_certificate_rs__mt) / conversion_rate if conversion_rate else 0
		self.purc_brokaerage_doller__mt = flt(self.purc_brokaerage_rs__mt) / conversion_rate if conversion_rate else 0
		self.ecgc_doller__mt = flt(self.ecgc_rs__mt) / conversion_rate if conversion_rate else 0
		self.bank_charges_doller__mt = flt(self.bank_charges_rs__mt) / conversion_rate if conversion_rate else 0
		self.administrative_cost_doller__mt = flt(self.administrative_cost_rs__mt) / conversion_rate if conversion_rate else 0
		self.wc_interest_doller__mt = flt(self.wc_interest_rs__mt) / conversion_rate if conversion_rate else 0
		self.cargo_shortage_doller__mt = flt(self.cargo_shortage_rs__mt) / conversion_rate if conversion_rate else 0
		self.silica_gel_doller__mt = flt(self.silica_gel_rs__mt) / conversion_rate if conversion_rate else 0
		self.craft_paper_doller__mt = flt(self.craft_paper_rs__mt) / conversion_rate if conversion_rate else 0
		self.fumigation_doller__mt = flt(self.fumigation_rs__mt) / conversion_rate if conversion_rate else 0
		self.other_cost_doller__mt = flt(self.other_cost_rs__mt) / conversion_rate if conversion_rate else 0
		self.thc_cost_doller__mt = flt(self.thc_cost_rs__mt) / conversion_rate if conversion_rate else 0
		