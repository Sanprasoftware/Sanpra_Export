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
        self._normalize_sales_orders()
        self._validate_sales_orders()
        self._set_exposure()

    def _normalize_sales_orders(self):
        if not self.get("sales_orders") and self.sales_order:
            total = flt(frappe.db.get_value("Sales Order", self.sales_order, "grand_total"))
            self.append("sales_orders", {
                "sales_order": self.sales_order,
                "sales_order_total": total,
                "booked_amount": self.contract_amount,
            })

        rows = self.get("sales_orders") or []
        self.sales_order = rows[0].sales_order if len(rows) == 1 else None
        self.sales_order_total = sum(flt(row.sales_order_total) for row in rows)
        self.sales_order_currency = self.currency if rows else None

    def _validate_sales_orders(self):
        rows = self.get("sales_orders") or []
        if not rows:
            return

        seen = set()
        for row in rows:
            if row.sales_order in seen:
                frappe.throw(_("Sales Order {0} is entered more than once").format(row.sales_order))
            seen.add(row.sales_order)
            if flt(row.booked_amount) <= 0:
                frappe.throw(_("Booked Amount for Sales Order {0} must be greater than zero").format(row.sales_order))

            so = frappe.db.get_value("Sales Order", row.sales_order, ["docstatus", "company", "customer", "currency", "grand_total"], as_dict=True)
            if not so or so.docstatus != 1:
                frappe.throw(_("Sales Order {0} must be submitted").format(row.sales_order))
            if so.company != self.company or so.customer != self.customer:
                frappe.throw(_("Company and Customer must match Sales Order {0}").format(row.sales_order))
            if so.currency != self.currency:
                frappe.throw(_("Forward Contract currency must match Sales Order {0}").format(row.sales_order))
            row.sales_order_total = so.grand_total

            booked = get_booked_amount(row.sales_order, exclude_contract=self.name)
            overhedging = frappe.db.get_value("Company", self.company, "allow_forward_overhedging")
            if not overhedging and booked + flt(row.booked_amount) > flt(so.grand_total):
                frappe.throw(_("Total forward booking cannot exceed Sales Order {0} amount {1}").format(row.sales_order, so.grand_total))

        self.sales_order_total = sum(flt(row.sales_order_total) for row in rows)
        allocated = sum(flt(row.booked_amount) for row in rows)
        if abs(allocated - flt(self.contract_amount)) > 0.01:
            frappe.throw(_("Total Sales Order Booked Amount must equal Contract Amount {0}").format(self.contract_amount))

    def _set_exposure(self):
        self.available_amount = max(flt(self.contract_amount) - flt(self.cancellation_amount) - flt(self.utilized_amount), 0)
        self.utilization_percentage = flt(self.utilized_amount) / flt(self.contract_amount) * 100 if self.contract_amount else 0
        rows = self.get("sales_orders") or []
        self.total_forward_booked_against_sales_order = sum(
            get_booked_amount(row.sales_order, exclude_contract=self.name)
            + (flt(row.booked_amount) if self.docstatus != 2 else 0)
            for row in rows
        )
        self.unhedged_sales_order_amount = max(
            flt(self.sales_order_total) - flt(self.total_forward_booked_against_sales_order), 0
        )

    def before_submit(self):
        self.status = "Open"

    def on_submit(self):
        update_sales_orders(self)

    def before_cancel(self):
        if frappe.db.exists("Forward Contract Utilization", {"forward_contract": self.name, "docstatus": 1}):
            frappe.throw(_("Cancel submitted utilizations before cancelling this Forward Contract"))

    def on_cancel(self):
        update_sales_orders(self)


def get_booked_amount(sales_order, exclude_contract=None):
    child_booked = frappe.db.sql("""
        select coalesce(sum(row.booked_amount * greatest(fc.contract_amount - fc.cancellation_amount, 0) / nullif(fc.contract_amount, 0)), 0)
        from `tabForward Contract Sales Order` row
        join `tabForward Contract` fc on fc.name = row.parent
        where row.sales_order=%s and fc.docstatus=1 and fc.status!="Closed" and fc.name!=%s
    """, (sales_order, exclude_contract or ""))[0][0]
    legacy_booked = frappe.db.sql("""
        select coalesce(sum(greatest(fc.contract_amount - fc.cancellation_amount, 0)), 0)
        from `tabForward Contract` fc
        where fc.sales_order=%s and fc.docstatus=1 and fc.status!="Closed" and fc.name!=%s
          and not exists (select 1 from `tabForward Contract Sales Order` row where row.parent=fc.name)
    """, (sales_order, exclude_contract or ""))[0][0]
    return flt(child_booked) + flt(legacy_booked)


def get_sales_orders(contract):
    rows = contract.get("sales_orders") or []
    orders = [row.sales_order for row in rows if row.sales_order]
    if contract.sales_order:
        orders.append(contract.sales_order)
    return list(dict.fromkeys(orders))


def update_sales_orders(contract):
    for sales_order in get_sales_orders(contract):
        update_sales_order(sales_order)


def update_sales_order(sales_order):
    if not sales_order:
        return
    booked = get_booked_amount(sales_order)
    utilized = flt(frappe.db.sql("""select coalesce(sum(utilized_amount),0)
        from `tabForward Contract Utilization` where sales_order=%s and docstatus=1""", sales_order)[0][0])
    total = flt(frappe.db.get_value("Sales Order", sales_order, "grand_total"))
    frappe.db.set_value("Sales Order", sales_order, {
        "forward_booked_amount": booked,
        "forward_available_amount": max(booked-utilized, 0),
        "unhedged_amount": max(total-booked, 0),
        "hedge_percentage": booked/total*100 if total else 0,
    }, update_modified=False)
