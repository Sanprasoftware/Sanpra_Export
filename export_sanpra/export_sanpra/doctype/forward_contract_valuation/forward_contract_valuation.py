import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from export_sanpra.export_sanpra.forex_accounting import cancel_linked_journal_entry, create_mtm_journal_entry


class ForwardContractValuation(Document):
    def validate(self):
        if flt(self.market_rate) <= 0:
            frappe.throw(_("Market Rate must be greater than zero"))
        contract = frappe.get_doc("Forward Contract", self.forward_contract)
        if contract.docstatus != 1 or contract.status in ("Closed", "Cancelled"):
            frappe.throw(_("Forward Contract must be submitted and active"))
        self.company = contract.company
        self.currency = contract.currency
        self.contract_type = contract.contract_type
        self.forward_rate = contract.forward_rate
        self.open_amount = contract.available_amount
        if flt(self.open_amount) <= 0:
            frappe.throw(_("Forward Contract has no open amount for MTM"))
        direction = 1 if contract.contract_type == "Export" else -1
        self.mtm_value = flt((flt(self.forward_rate) - flt(self.market_rate)) * flt(self.open_amount) * direction, 2)
        previous = frappe.db.sql(
            """select mtm_value, valuation_date from `tabForward Contract Valuation`
            where forward_contract=%s and docstatus=1 and name!=%s
            order by valuation_date desc, creation desc limit 1""",
            (self.forward_contract, self.name or ""),
        )
        if previous and getdate(self.valuation_date) < getdate(previous[0][1]):
            frappe.throw(
                _("Valuation Date cannot be before the latest submitted valuation dated {0}").format(previous[0][1])
            )
        self.previous_mtm_value = flt(previous[0][0], 2) if previous else 0
        self.adjustment_amount = flt(self.mtm_value - self.previous_mtm_value, 2)

    def on_submit(self):
        journal_entry = create_mtm_journal_entry(self)
        if journal_entry:
            self.db_set("journal_entry", journal_entry, update_modified=False)

    def before_cancel(self):
        later = frappe.db.sql(
            """select name from `tabForward Contract Valuation`
            where forward_contract=%s and docstatus=1 and name!=%s
            and (valuation_date>%s or (valuation_date=%s and creation>%s)) limit 1""",
            (self.forward_contract, self.name, self.valuation_date, self.valuation_date, self.creation),
        )
        if later:
            frappe.throw(_("Cancel later Forward Contract Valuations first"))
        cancel_linked_journal_entry(self.journal_entry, self)
