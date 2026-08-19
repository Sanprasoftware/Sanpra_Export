import uuid
import frappe
from frappe.utils import add_days, flt, today

def run():
 point="forex_settlement_audit"; frappe.db.savepoint(point)
 try:
  company=frappe.get_all("Company",filters={"default_currency":"INR"},pluck="name",limit=1)[0]
  order=frappe.get_all("Sales Order",filters={"company":company,"docstatus":1,"currency":["!=","INR"]},fields=["name","customer","currency","grand_total"],limit=1)[0]
  bank=frappe.get_all("Bank",pluck="name",limit=1)[0]
  fc=frappe.get_doc({"doctype":"Forward Contract","company":company,"contract_number":f"SETTLE-{uuid.uuid4().hex[:10]}","contract_type":"Export","bank":bank,"booking_date":today(),"maturity_date":add_days(today(),30),"currency":order.currency,"company_currency":"INR","contract_amount":100,"forward_rate":84.5,"customer":order.customer,"sales_order":order.name,"sales_order_currency":order.currency,"sales_order_total":order.grand_total}).insert(ignore_permissions=True); fc.submit()
  u=frappe.get_doc({"doctype":"Forward Contract Utilization","company":company,"forward_contract":fc.name,"sales_order":order.name,"customer":order.customer,"utilization_date":today(),"currency":order.currency,"utilized_amount":60,"forward_rate":84.5,"settlement_rate":84.75,"reference_exchange_rate":83.8}).insert(ignore_permissions=True); u.submit()
  settlement=frappe.get_doc({"doctype":"Forward Contract Settlement","company":company,"forward_contract":fc.name,"bank":bank,"settlement_date":today(),"currency":order.currency,"settlement_amount":40,"forward_rate":84.5,"actual_bank_rate":84.75,"reference_value":3352}).insert(ignore_permissions=True); settlement.submit()
  blocked=False
  try:
   frappe.get_doc({"doctype":"Forward Contract Settlement","company":company,"forward_contract":fc.name,"bank":bank,"settlement_date":today(),"currency":order.currency,"settlement_amount":21,"forward_rate":84.5,"actual_bank_rate":84.75,"reference_value":1759.8}).insert(ignore_permissions=True)
  except frappe.ValidationError: blocked=True
  return {"settlement_submitted":settlement.docstatus==1,"forward_value":flt(settlement.forward_value)==3380,"actual_value":flt(settlement.actual_value)==3390,"gain_loss":flt(settlement.gain_loss)==38,"over_settlement_blocked":blocked,"all_passed":settlement.docstatus==1 and blocked and flt(settlement.gain_loss)==38}
 finally: frappe.db.rollback(save_point=point)
