import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from export_sanpra.export_sanpra.doctype.forward_contract.forward_contract import update_sales_order
from export_sanpra.export_sanpra.forex_actions import sync_sales_invoice

class ForwardContractUtilization(Document):
 def validate(self):
  if flt(self.utilized_amount)<=0: frappe.throw(_("Utilized Amount must be greater than zero"))
  fc=frappe.get_doc("Forward Contract", self.forward_contract)
  if fc.docstatus!=1 or fc.status not in ("Open","Partly Utilized"): frappe.throw(_("Forward Contract is not open for utilization"))
  if self.currency!=fc.currency: frappe.throw(_("Currency must match Forward Contract"))
  used=frappe.db.sql("select coalesce(sum(utilized_amount),0) from `tabForward Contract Utilization` where forward_contract=%s and docstatus=1 and name!=%s",(fc.name,self.name or ""))[0][0]
  if flt(used)+flt(self.utilized_amount)>flt(fc.contract_amount)-flt(fc.cancellation_amount): frappe.throw(_("Utilization exceeds available contract amount"))
  if self.sales_invoice:
   si=frappe.db.get_value("Sales Invoice",self.sales_invoice,["docstatus","company","customer","currency","outstanding_amount"],as_dict=True)
   if not si or si.docstatus!=1 or (si.company,si.customer,si.currency)!=(fc.company,fc.customer,fc.currency): frappe.throw(_("Sales Invoice company, customer and currency must match"))
   invoice_used=frappe.db.sql("select coalesce(sum(utilized_amount),0) from `tabForward Contract Utilization` where sales_invoice=%s and docstatus=1 and name!=%s",(self.sales_invoice,self.name or ""))[0][0]
   if flt(invoice_used)+flt(self.utilized_amount)>flt(si.outstanding_amount): frappe.throw(_("Utilization exceeds eligible invoice outstanding amount"))
  self.company_currency_amount=flt(self.utilized_amount)*flt(self.forward_rate)
  self.forex_gain_loss=flt(self.utilized_amount)*(flt(self.settlement_rate)-flt(self.reference_exchange_rate))
 def on_submit(self): recalculate(self.forward_contract); sync_sales_invoice(self.sales_invoice)
 def on_cancel(self): recalculate(self.forward_contract); sync_sales_invoice(self.sales_invoice)

def recalculate(name):
 fc=frappe.get_doc("Forward Contract",name)
 used=flt(frappe.db.sql("select coalesce(sum(utilized_amount),0) from `tabForward Contract Utilization` where forward_contract=%s and docstatus=1",name)[0][0])
 available=max(flt(fc.contract_amount)-flt(fc.cancellation_amount)-used,0)
 status="Fully Utilized" if available<=0 else "Partly Utilized" if used else "Open"
 frappe.db.set_value("Forward Contract",name,{"utilized_amount":used,"available_amount":available,"utilization_percentage":used/flt(fc.contract_amount)*100 if fc.contract_amount else 0,"status":status},update_modified=False)
 update_sales_order(fc.sales_order)
