import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import add_months, flt, fmt_money, get_last_day, getdate, month_diff
from frappe.utils.data import get_first_day, nowdate

from erpnext.accounts.doctype.budget.budget import Budget

class CustomBudget(Budget):

    def validate_existing_expenses(self):
        if self.is_new() and self.revision_of:
            return

        params = frappe._dict(
            {
                "company": self.company,
                "account": self.account,
                "budget_start_date": self.budget_start_date,
                "budget_end_date": self.budget_end_date,
                "budget_against_field": frappe.scrub(self.budget_against),
                "budget_against_doctype": frappe.unscrub(self.budget_against),
            }
        )

        params[params.budget_against_field] = self.get(params.budget_against_field)

        if frappe.get_cached_value("DocType", params.budget_against_doctype, "is_tree"):
            params.is_tree = True
        else:
            params.is_tree = False

        actual_spent = get_actual_expense(params)

        if actual_spent > self.budget_amount:
            frappe.msgprint(
                _(
                    "Spending for Account {0} ({1}) between {2} and {3} "
                    "has already exceeded the new allocated budget. "
                    "Spent: {4}, Budget: {5}"
                ).format(
                    frappe.bold(self.account),
                    frappe.bold(self.company),
                    frappe.bold(self.budget_start_date),
                    frappe.bold(self.budget_end_date),
                    frappe.bold(frappe.utils.fmt_money(actual_spent)),
                    frappe.bold(frappe.utils.fmt_money(self.budget_amount)),
                ),
                title=_("Budget Limit Exceeded"),
            )
    
    def validate_budget_amount(self):
        pass
        # if self.budget_amount <= 0:
        #     frappe.msgprint(_("Budget Amount can not be {0}.").format(self.budget_amount))


def get_actual_expense(params):
    if not params.budget_against_doctype:
        params.budget_against_doctype = frappe.unscrub(params.budget_against_field)

    budget_against_field = params.get("budget_against_field")
    condition1 = " and gle.posting_date <= %(month_end_date)s" if params.get("month_end_date") else ""

    date_condition = (
        f"and gle.posting_date between '{params.budget_start_date}' and '{params.budget_end_date}'"
    )

    if params.is_tree:
        lft_rgt = frappe.db.get_value(
            params.budget_against_doctype, params.get(budget_against_field), ["lft", "rgt"], as_dict=1
        )
        params.update(lft_rgt)

        condition2 = f"""
            and exists(
                select name from `tab{params.budget_against_doctype}`
                where lft >= %(lft)s and rgt <= %(rgt)s
                and name = gle.{budget_against_field}
            )
        """
    else:
        condition2 = f"""
            and gle.{budget_against_field} = %({budget_against_field})s
        """

    amount = flt(
        frappe.db.sql(
            f"""
                select sum(gle.debit) - sum(gle.credit)
                from `tabGL Entry` gle
                where
                    is_cancelled = 0
                    and gle.account = %(account)s
                    {condition1}
                    {date_condition}
                    and gle.company = %(company)s
                    and gle.docstatus = 1
                    {condition2}
            """,
            params,
        )[0][0]
    )  # nosec

    return amount