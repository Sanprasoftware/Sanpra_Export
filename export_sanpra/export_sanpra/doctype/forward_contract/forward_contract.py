import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class ForwardContract(Document):
    def validate(self):
        if flt(self.contract_amount) <= 0:
            frappe.throw(_("Contract Amount must be greater than zero"))
        if flt(self.forward_rate) <= 0:
            frappe.throw(_("Forward Rate must be greater than zero"))
        if self.booking_date and self.maturity_date and getdate(self.maturity_date) < getdate(self.booking_date):
            frappe.throw(_("Maturity Date cannot be before Booking Date"))
        self.contract_value_company_currency = flt(self.contract_amount) * flt(self.forward_rate)
        self.total_charges = flt(self.booking_charge) + flt(self.bank_charge) + flt(self.other_charge)
        self._validate_sales_order()
        self._set_exposure()

    def _validate_sales_order(self):
        if not self.sales_order:
            return
        so = frappe.db.get_value("Sales Order", self.sales_order, ["docstatus", "company", "customer", "currency", "grand_total"], as_dict=True)
        if not so or so.docstatus != 1:
            frappe.throw(_("Sales Order must be submitted"))
        if so.company != self.company or so.customer != self.customer:
            frappe.throw(_("Company and Customer must match the Sales Order"))
        if so.currency != self.currency:
            frappe.throw(_("Forward Contract currency must match Sales Order currency"))
        booked = frappe.db.sql("""select coalesce(sum(contract_amount),0) from `tabForward Contract`
            where sales_order=%s and docstatus=1 and name!=%s""", (self.sales_order, self.name or ""))[0][0]
        if not frappe.db.get_value("Company", self.company, "allow_forward_overhedging") and flt(booked) + flt(self.contract_amount) > flt(so.grand_total):
            frappe.throw(_("Total forward booking cannot exceed Sales Order amount {0}").format(so.grand_total))

    def _set_exposure(self):
        self.available_amount = max(flt(self.contract_amount) - flt(self.utilized_amount), 0)
        self.utilization_percentage = flt(self.utilized_amount) / flt(self.contract_amount) * 100 if self.contract_amount else 0
        if self.sales_order:
            other = frappe.db.sql("select coalesce(sum(contract_amount),0) from `tabForward Contract` where sales_order=%s and docstatus=1 and name!=%s", (self.sales_order, self.name or ""))[0][0]
            self.total_forward_booked_against_sales_order = flt(other) + (flt(self.contract_amount) if self.docstatus != 2 else 0)
            self.unhedged_sales_order_amount = max(flt(self.sales_order_total) - flt(self.total_forward_booked_against_sales_order), 0)

    def before_submit(self):
        self.status = "Open"

    def on_submit(self):
        update_sales_order(self.sales_order)

    def before_cancel(self):
        if frappe.db.exists("Forward Contract Utilization", {"forward_contract": self.name, "docstatus": 1}):
            frappe.throw(_("Cancel submitted utilizations before cancelling this Forward Contract"))

    def on_cancel(self):
        update_sales_order(self.sales_order)


def update_sales_order(sales_order):
    if not sales_order:
        return
    values = frappe.db.sql("""select coalesce(sum(contract_amount),0), coalesce(sum(available_amount),0)
        from `tabForward Contract` where sales_order=%s and docstatus=1""", sales_order)[0]
    total = flt(frappe.db.get_value("Sales Order", sales_order, "grand_total"))
    frappe.db.set_value("Sales Order", sales_order, {"forward_booked_amount": values[0], "forward_available_amount": values[1], "unhedged_amount": max(total-flt(values[0]),0), "hedge_percentage": flt(values[0])/total*100 if total else 0}, update_modified=False)
