import frappe

@frappe.whitelist()
def export_sales_order_s(doc, method=None):
    if doc.custom_sales_order_type != "Global":
        return

    if frappe.db.exists("Export Sales Order s", {"sales_order_id": doc.name}):
        return

    # export_quotation = frappe.get_doc("Export Quotation s", {"name": doc.custom_quotation_id}, ["*"])
    export_quotation = frappe.get_doc("Export Quotation s", doc.custom_quotation_id)
    # frappe.throw(f"{export_quotation.name}, {export_quotation.transit_days}")
    new_doc = frappe.new_doc("Export Sales Order s")
    new_doc.sales_order_id = doc.name
    new_doc.orgin = export_quotation.orgin
    new_doc.discharge_country = export_quotation.discharge_country
    new_doc.type_of_stuffing = export_quotation.type_of_stuffing
    new_doc.discharge_port = export_quotation.discharge_port
    new_doc.agent_name = export_quotation.agent_name  
    new_doc.loading_port = export_quotation.loading_port
    new_doc.contracted_qty = export_quotation.contracted_qty
    new_doc.craft_paper__kg_rate = export_quotation.craft_paper__kg_rate
    new_doc.cif_insurance = export_quotation.cif_insurance
    new_doc.no_of_fcl = export_quotation.no_of_fcl 
    new_doc.craft_paper_kg_fcl = export_quotation.craft_paper_kg_fcl
    new_doc.ecgc_rate = export_quotation.ecgc_rate
    new_doc.stuffing_qty_fcl = export_quotation.stuffing_qty_fcl
    new_doc.fumigation = export_quotation.fumigation
    new_doc.additional_document = export_quotation.additional_document
    new_doc.no_of_docs = export_quotation.no_of_docs
    new_doc.local_transp_dpds_rupees__mt = export_quotation.local_transp_dpds_rupees__mt
    new_doc.buyer_standard_document = export_quotation.buyer_standard_document
    new_doc.no_of_s_b = export_quotation.no_of_s_b
    new_doc.ocean_frieght_fcl_doller = export_quotation.ocean_frieght_fcl_doller
    new_doc.silica_gel__kg_rate = export_quotation.silica_gel__kg_rate
    new_doc.ocean_frieght_fcl_calcu = export_quotation.ocean_frieght_fcl_calcu
    new_doc.silica_gel_kg__fcl = export_quotation.silica_gel_kg__fcl
    new_doc.thc_fcl_rupees = export_quotation.thc_fcl_rupees
    new_doc.bl_cost_docs_rupees = export_quotation.bl_cost_docs_rupees

    new_doc.refresh = export_quotation.refresh
    new_doc.sales_commission_mt = export_quotation.sales_commission_mt
    new_doc.margin = export_quotation.margin
    new_doc.selling_rate = export_quotation.selling_rate
    new_doc.selling_offer_rate_mt = export_quotation.selling_offer_rate_mt
    new_doc.cargo_pur_rate = export_quotation.cargo_pur_rate
    new_doc.cost_of_export = export_quotation.cost_of_export 
    new_doc.net_margin = export_quotation.net_margin

    new_doc.fob_cost = export_quotation.fob_cost
    new_doc.fob_cost_mt_rs__mt = export_quotation.fob_cost_mt_rs__mt
    new_doc.fob_cost_mt_doller = export_quotation.fob_cost_mt_doller
    new_doc.cnf_ocean_freight = export_quotation.cnf_ocean_freight
    new_doc.cin_ocean_freight_rs__mt = export_quotation.cin_ocean_freight_rs__mt
    new_doc.cnf_ocean_freight_doller = export_quotation.cnf_ocean_freight_doller
    new_doc.cif_insurance_cost = export_quotation.cif_insurance_cost
    new_doc.cif_insurance_cost_rs__mt = export_quotation.cif_insurance_cost_rs__mt  
    new_doc.cif_insurance_cost_doller = export_quotation.cif_insurance_cost_doller
    new_doc.cargo_pur_amt = export_quotation.cargo_pur_amt
    new_doc.cargo_purc_amt_rupees__mt = export_quotation.cargo_purc_amt_rupees__mt
    new_doc.cargo_purc_amt_dollar___mt = export_quotation.cargo_purc_amt_dollar___mt
    new_doc.local_transp_dpds_fob = export_quotation.local_transp_dpds_fob
    new_doc.local_transp_dpds_rs__mt = export_quotation.local_transp_dpds_rs__mt
    new_doc.local_transp_dpds_doller__mt = export_quotation.local_transp_dpds_doller__mt
    new_doc.cha_clearing_cost_fob = export_quotation.cha_clearing_cost_fob
    new_doc.cha_clearing_cost_rs__mt = export_quotation.cha_clearing_cost_rs__mt
    new_doc.cha_clearing_cost_doller__mt = export_quotation.cha_clearing_cost_doller__mt
    new_doc.surveyor_cost_fob = export_quotation.surveyor_cost_fob
    new_doc.surveyor_cost_rs__mt = export_quotation.surveyor_cost_rs__mt
    new_doc.surveyor_cost_doller__mt = export_quotation.surveyor_cost_doller__mt
    new_doc.additional_certificate_fob = export_quotation.additional_certificate_fob
    new_doc.additional_certificate_rs__mt = export_quotation.additional_certificate_rs__mt
    new_doc.additional_certificate_doller__mt = export_quotation.additional_certificate_doller__mt
    new_doc.purc_brokaerage_fob = export_quotation.purc_brokaerage_fob
    new_doc.purc_brokaerage_rs__mt = export_quotation.purc_brokaerage_rs__mt
    new_doc.purc_brokaerage_doller__mt = export_quotation.purc_brokaerage_doller__mt
    new_doc.ecgc_fob = export_quotation.ecgc_fob
    new_doc.ecgc_rs__mt = export_quotation.ecgc_rs__mt
    new_doc.ecgc_doller__mt = export_quotation.ecgc_doller__mt
    new_doc.bank_charges_fob = export_quotation.bank_charges_fob
    new_doc.bank_charges_rs__mt = export_quotation.bank_charges_rs__mt
    new_doc.bank_charges_doller__mt = export_quotation.bank_charges_doller__mt
    new_doc.administrative_cost_fob = export_quotation.administrative_cost_fob
    new_doc.administrative_cost_rs__mt = export_quotation.administrative_cost_rs__mt
    new_doc.administrative_cost_doller__mt = export_quotation.administrative_cost_doller__mt
    new_doc.wc_interest = export_quotation.wc_interest
    new_doc.wc_interest_rs__mt = export_quotation.wc_interest_rs__mt
    new_doc.wc_interest_doller__mt = export_quotation.wc_interest_doller__mt
    new_doc.cargo_shortage_cost = export_quotation.cargo_shortage_cost 
    new_doc.cargo_shortage_rs__mt = export_quotation.cargo_shortage_rs__mt
    new_doc.cargo_shortage_doller__mt = export_quotation.cargo_shortage_doller__mt
    new_doc.silica_gel = export_quotation.silica_gel
    new_doc.silica_gel_rs__mt = export_quotation.silica_gel_rs__mt
    new_doc.silica_gel_doller__mt = export_quotation.silica_gel_doller__mt
    new_doc.craft_paper = export_quotation.craft_paper
    new_doc.craft_paper_rs__mt = export_quotation.craft_paper_rs__mt
    new_doc.craft_paper_doller__mt = export_quotation.craft_paper_doller__mt
    new_doc.fumigation_cost = export_quotation.fumigation_cost
    new_doc.fumigation_rs__mt = export_quotation.fumigation_rs__mt
    new_doc.fumigation_doller__mt = export_quotation.fumigation_doller__mt
    new_doc.other_cost = export_quotation.other_cost
    new_doc.other_cost_rs__mt = export_quotation.other_cost_rs__mt
    new_doc.other_cost_doller__mt = export_quotation.other_cost_doller__mt 
    new_doc.bank_charge = export_quotation.bank_charge
    new_doc.thc_cost_rs__mt = export_quotation.thc_cost_rs__mt
    new_doc.thc_cost_doller__mt = export_quotation.thc_cost_doller__mt 
    new_doc.thc_cost = export_quotation.thc_cost
    new_doc.export_expense_rs__mt = export_quotation.export_expense_rs__mt
    new_doc.export_expense_doller = export_quotation.export_expense_doller
    new_doc.intrest_rate = export_quotation.intrest_rate
    new_doc.linear_currency = export_quotation.linear_currency
    new_doc.cin_insurance_calculation = export_quotation.cin_insurance_calculation
    new_doc.export_expense_total = export_quotation.export_expense_total
    new_doc.transit_days = export_quotation.transit_days
    new_doc.save()