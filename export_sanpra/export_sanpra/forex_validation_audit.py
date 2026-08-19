import uuid

import frappe
from frappe.utils import add_days, flt, today


def _fails(doc):
    try:
        doc.run_method("validate")
        return False
    except frappe.ValidationError:
        return True


def run():
    point = "forex_validation_audit"
    frappe.db.savepoint(point)
    try:
        company = frappe.get_all("Company", filters={"default_currency": "INR"}, pluck="name", limit=1)[0]
        order = frappe.get_all("Sales Order", filters={"company": company, "docstatus": 1, "currency": ["!=", "INR"], "grand_total": [">", 10]}, fields=["name", "company", "customer", "currency", "grand_total"], limit=1)[0]
        bank = frappe.get_all("Bank", pluck="name", limit=1)[0]

        def contract(**changes):
            values={"doctype":"Forward Contract","company":company,"contract_number":f"VALIDATE-{uuid.uuid4().hex[:10]}","contract_type":"Export","bank":bank,"booking_date":today(),"maturity_date":add_days(today(),30),"currency":order.currency,"company_currency":"INR","contract_amount":100,"forward_rate":84.5,"customer":order.customer,"sales_order":order.name,"sales_order_currency":order.currency,"sales_order_total":order.grand_total}
            values.update(changes)
            return frappe.get_doc(values)

        result={
            "zero_amount_blocked": _fails(contract(contract_amount=0)),
            "zero_rate_blocked": _fails(contract(forward_rate=0)),
            "invalid_maturity_blocked": _fails(contract(maturity_date=add_days(today(),-1))),
            "currency_mismatch_blocked": _fails(contract(currency="EUR" if order.currency!="EUR" else "USD")),
        }

        original=frappe.db.get_value("Company",company,"allow_forward_overhedging")
        frappe.db.set_value("Company",company,"allow_forward_overhedging",0,update_modified=False)
        result["overhedging_blocked"]=_fails(contract(contract_amount=flt(order.grand_total)+1))
        frappe.db.set_value("Company",company,"allow_forward_overhedging",original,update_modified=False)

        valid=contract(contract_amount=100).insert(ignore_permissions=True); valid.submit()
        overflow=frappe.get_doc({"doctype":"Forward Contract Utilization","company":company,"forward_contract":valid.name,"sales_order":order.name,"customer":order.customer,"utilization_date":today(),"currency":order.currency,"utilized_amount":101,"forward_rate":84.5})
        result["utilization_overflow_blocked"]=_fails(overflow)

        utilization=frappe.get_doc({"doctype":"Forward Contract Utilization","company":company,"forward_contract":valid.name,"sales_order":order.name,"customer":order.customer,"utilization_date":today(),"currency":order.currency,"utilized_amount":40,"forward_rate":84.5}).insert(ignore_permissions=True)
        utilization.submit()

        settlement=frappe.get_doc({"doctype":"Forward Contract Settlement","company":company,"forward_contract":valid.name,"bank":bank,"settlement_date":today(),"currency":order.currency,"settlement_amount":40,"forward_rate":84.5,"actual_bank_rate":84.75,"reference_value":40*83.8})
        settlement.run_method("validate")
        result["settlement_forward_value"]=flt(settlement.forward_value)==3380
        result["settlement_actual_value"]=flt(settlement.actual_value)==3390
        result["settlement_gain_loss"]=flt(settlement.gain_loss)==38
        result["all_passed"]=all(result.values())
        return result
    finally:
        frappe.db.rollback(save_point=point)
