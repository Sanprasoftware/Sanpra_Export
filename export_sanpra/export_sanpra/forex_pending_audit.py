import uuid
import frappe
from frappe.utils import add_days, flt, today
from export_sanpra.export_sanpra.forex_actions import close_contract, make_rollover, partial_cancel

def run():
 point="forex_pending_audit"; frappe.db.savepoint(point)
 try:
  company=frappe.get_all("Company",filters={"default_currency":"INR"},pluck="name",limit=1)[0]
  order=frappe.get_all("Sales Order",filters={"company":company,"docstatus":1,"currency":["!=","INR"]},fields=["name","customer","currency","grand_total"],limit=1)[0]
  bank=frappe.get_all("Bank",pluck="name",limit=1)[0]
  fc=frappe.get_doc({"doctype":"Forward Contract","company":company,"contract_number":f"PENDING-{uuid.uuid4().hex[:10]}","contract_type":"Export","bank":bank,"booking_date":today(),"maturity_date":add_days(today(),30),"currency":order.currency,"company_currency":"INR","contract_amount":100,"forward_rate":84.5,"customer":order.customer,"sales_order":order.name,"sales_order_currency":order.currency,"sales_order_total":order.grand_total}).insert(ignore_permissions=True); fc.submit()
  rollover=make_rollover(fc.name,25,add_days(today(),60))
  cancelled=partial_cancel(fc.name,40,100,"Audit partial cancellation")
  fc.reload()
  u=frappe.get_doc({"doctype":"Forward Contract Utilization","company":company,"forward_contract":fc.name,"sales_order":order.name,"customer":order.customer,"utilization_date":today(),"currency":order.currency,"utilized_amount":60,"forward_rate":84.5}).insert(ignore_permissions=True); u.submit(); fc.reload()
  close_contract(fc.name,"Audit closure"); fc.reload()
  result={"rollover_draft":rollover.rollover_from==fc.name and flt(rollover.contract_amount)==25,"partial_cancel":flt(cancelled.cancellation_amount)==40 and flt(cancelled.available_amount)==60,"effective_full_utilization":fc.available_amount==0,"formal_closure":fc.status=="Closed","account_filter_script":bool(frappe.db.exists("Client Script","Forex - Company Account Filters"))}
  result["all_passed"]=all(result.values()); return result
 finally: frappe.db.rollback(save_point=point)
