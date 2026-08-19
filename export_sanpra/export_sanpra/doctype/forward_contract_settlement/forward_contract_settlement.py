import frappe
from frappe.model.document import Document
from frappe.utils import flt

from export_sanpra.export_sanpra.forex_accounting import cancel_linked_journal_entry, create_settlement_journal_entry


class ForwardContractSettlement(Document):
 def validate(self):
  if flt(self.settlement_amount)<=0: frappe.throw("Settlement Amount must be greater than zero")
  contract=frappe.get_doc("Forward Contract",self.forward_contract)
  if contract.docstatus!=1 or contract.status in ("Closed","Cancelled"): frappe.throw("Forward Contract must be submitted and active")
  if self.company!=contract.company or self.currency!=contract.currency or self.bank!=contract.bank: frappe.throw("Company, Bank and Currency must match the Forward Contract")
  if flt(self.forward_rate)<=0 or flt(self.actual_bank_rate)<=0: frappe.throw("Forward Rate and Actual Bank Rate must be greater than zero")
  settled=frappe.db.sql("select coalesce(sum(settlement_amount),0) from `tabForward Contract Settlement` where forward_contract=%s and docstatus=1 and name!=%s",(contract.name,self.name or ""))[0][0]
  if flt(settled)+flt(self.settlement_amount)>flt(contract.utilized_amount): frappe.throw("Settlement Amount cannot exceed utilized but unsettled contract amount")
  self.forward_value=flt(self.settlement_amount)*flt(self.forward_rate)
  self.actual_value=flt(self.settlement_amount)*flt(self.actual_bank_rate)
  self.gain_loss=self.actual_value-flt(self.reference_value)
  self.hedge_gain_loss=self.forward_value-self.actual_value

 def on_submit(self):
  journal_entry=create_settlement_journal_entry(self)
  if journal_entry:
   self.db_set("journal_entry",journal_entry,update_modified=False)

 def before_cancel(self):
  cancel_linked_journal_entry(self.journal_entry,self)
