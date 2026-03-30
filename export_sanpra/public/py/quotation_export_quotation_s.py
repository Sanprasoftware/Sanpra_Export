import frappe

@frappe.whitelist()
def create_export_quotation_s(doc, method=None):
    if doc.custom_quotation_type_ != "Global":
        return

    if frappe.db.exists("Export Quotation s", {"quotation_id": doc.name}):
        return

    new_doc = frappe.new_doc("Export Quotation s")
    new_doc.quotation_id = doc.name 
    new_doc.save()


@frappe.whitelist()
def calculate_total_amount_before_duty(qty=None, custom_item_rate=None):
    qty = frappe.utils.flt(qty)
    custom_item_rate = frappe.utils.flt(custom_item_rate)
    return qty * custom_item_rate

@frappe.whitelist()
def calculate_custom_total_purchase_amt(qty=None, custom__cargo_purc_rate_inr_mt=None):
    qty = frappe.utils.flt(qty)
    custom__cargo_purc_rate_inr_mt = frappe.utils.flt(custom__cargo_purc_rate_inr_mt)
    return qty * custom__cargo_purc_rate_inr_mt


@frappe.whitelist()
def calculate_custom__cargo_shortage_inr__mt(custom__cargo_purc_rate_inr_mt=None, custom_shortage_=None):
    custom__cargo_purc_rate_inr_mt = frappe.utils.flt(custom__cargo_purc_rate_inr_mt)
    custom_shortage_ = frappe.utils.flt(custom_shortage_)
    return (custom__cargo_purc_rate_inr_mt * custom_shortage_) / 100


@frappe.whitelist()
def calculate_custom_purc_brokaerage_inr__mt(qty=None, custom_purc_brokaerage_inr__mt=None):
    qty = frappe.utils.flt(qty)
    custom_purc_brokaerage_inr__mt = frappe.utils.flt(custom_purc_brokaerage_inr__mt)
    return qty * custom_purc_brokaerage_inr__mt


@frappe.whitelist()
def calculate_custom_export_duty(custom_total_amount_before_duty=None, custom_export_duty_single_item=None):
    custom_total_amount_before_duty = frappe.utils.flt(custom_total_amount_before_duty)
    custom_export_duty_single_item = frappe.utils.flt(custom_export_duty_single_item)
    return (custom_total_amount_before_duty * custom_export_duty_single_item) / 100


@frappe.whitelist()
def calculate_custom_export_duty_single_item(custom_export_duty=None, custom_total_amount_before_duty=None):
    custom_export_duty = frappe.utils.flt(custom_export_duty)
    custom_total_amount_before_duty = frappe.utils.flt(custom_total_amount_before_duty)
    if not custom_total_amount_before_duty:
        return 0
    return (custom_export_duty / custom_total_amount_before_duty) * 100
