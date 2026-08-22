import frappe
from frappe import _
from frappe.utils import add_days, flt, today
from export_sanpra.export_sanpra.doctype.forward_contract.forward_contract import get_sales_orders, update_sales_order


def _active_utilized(contract):
    return flt(frappe.db.sql("select coalesce(sum(utilized_amount),0) from `tabForward Contract Utilization` where forward_contract=%s and docstatus=1",contract)[0][0])


def effective_available(doc):
    return max(flt(doc.contract_amount)-flt(doc.cancellation_amount)-_active_utilized(doc.name),0)


@frappe.whitelist()
def partial_cancel(contract, amount, charge=0, reason=None):
    frappe.only_for(("Forex Manager","Accounts Manager"))
    doc=frappe.get_doc("Forward Contract",contract)
    if doc.docstatus!=1 or doc.status in ("Closed","Cancelled","Fully Utilized"):
        frappe.throw(_("Only an active submitted contract can be partially cancelled"))
    amount=flt(amount); charge=flt(charge)
    if amount<=0 or amount>effective_available(doc):
        frappe.throw(_("Cancellation Amount must be positive and cannot exceed available amount"))
    new_cancelled=flt(doc.cancellation_amount)+amount
    available=max(flt(doc.contract_amount)-new_cancelled-_active_utilized(doc.name),0)
    status="Closed" if available<=0 else "Partly Utilized" if _active_utilized(doc.name) else "Open"
    frappe.db.set_value("Forward Contract",doc.name,{"cancellation_amount":new_cancelled,"cancellation_charge":flt(doc.cancellation_charge)+charge,"available_amount":available,"status":status},update_modified=True)
    doc.add_comment("Info",_("Partial cancellation: {0} {1}; charge {2}. Reason: {3}").format(doc.currency,amount,charge,reason or "-"))
    for sales_order in get_sales_orders(doc):
        update_sales_order(sales_order)
    return frappe.get_value("Forward Contract",doc.name,["cancellation_amount","available_amount","status"],as_dict=True)


@frappe.whitelist()
def close_contract(contract, reason=None):
    frappe.only_for(("Forex Manager","Accounts Manager"))
    doc=frappe.get_doc("Forward Contract",contract)
    if doc.docstatus!=1: frappe.throw(_("Forward Contract must be submitted"))
    if effective_available(doc)>0: frappe.throw(_("Cancel, utilize, settle, or roll over the remaining balance before closure"))
    frappe.db.set_value("Forward Contract",doc.name,"status","Closed",update_modified=True)
    doc.add_comment("Info",_("Contract closed. Reason: {0}").format(reason or "-"))
    for sales_order in get_sales_orders(doc):
        update_sales_order(sales_order)


@frappe.whitelist()
def make_rollover(contract, amount=None, maturity_date=None):
    frappe.only_for(("Forex Manager","Accounts Manager"))
    source=frappe.get_doc("Forward Contract",contract)
    available=effective_available(source); amount=flt(amount or available)
    if source.docstatus!=1 or amount<=0 or amount>available: frappe.throw(_("Rollover amount must be within available contract balance"))
    target=frappe.new_doc("Forward Contract")
    for field in ("company","contract_type","bank","bank_account","customer","sales_order","currency","company_currency","sales_order_currency","sales_order_total","dealer_name"):
        target.set(field,source.get(field))
    for row in source.get("sales_orders") or []:
        target.append("sales_orders", {"sales_order": row.sales_order, "sales_order_total": row.sales_order_total, "booked_amount": flt(row.booked_amount) * amount / flt(source.contract_amount)})
    target.booking_date=today(); target.maturity_date=maturity_date or add_days(source.maturity_date,30)
    target.contract_amount=amount; target.forward_rate=source.forward_rate; target.rollover_from=source.name
    return target


def _sync_sales_order(sales_order):
    if not sales_order: return
    total=flt(frappe.db.get_value("Sales Order",sales_order,"grand_total"))
    booked,available=frappe.db.sql("select coalesce(sum(contract_amount-cancellation_amount),0),coalesce(sum(available_amount),0) from `tabForward Contract` where sales_order=%s and docstatus=1 and status!='Closed'",sales_order)[0]
    frappe.db.set_value("Sales Order",sales_order,{"forward_booked_amount":booked,"forward_available_amount":available,"unhedged_amount":max(total-flt(booked),0),"hedge_percentage":flt(booked)/total*100 if total else 0},update_modified=False)


def sync_sales_invoice(sales_invoice):
    if not sales_invoice: return
    used=flt(frappe.db.sql("select coalesce(sum(utilized_amount),0) from `tabForward Contract Utilization` where sales_invoice=%s and docstatus=1",sales_invoice)[0][0])
    contract=frappe.db.get_value("Forward Contract Utilization",{"sales_invoice":sales_invoice,"docstatus":1},"forward_contract",order_by="utilization_date desc")
    values={"forward_utilized_amount":used}
    if contract:
        fc=frappe.db.get_value("Forward Contract",contract,["name","forward_rate","contract_amount","available_amount"],as_dict=True)
        values.update({"forward_contract":fc.name,"forward_contract_rate":fc.forward_rate,"forward_contract_amount":fc.contract_amount,"forward_available_amount":fc.available_amount})
    frappe.db.set_value("Sales Invoice",sales_invoice,values,update_modified=False)
