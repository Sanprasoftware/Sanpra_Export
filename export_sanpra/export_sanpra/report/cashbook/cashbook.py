
# Copyright (c) 2026, contact@sanpra.co.in and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def validate_filters(filters):

    if filters.from_date and filters.to_date:
        if getdate(filters.from_date) > getdate(filters.to_date):
            frappe.throw(_("From Date cannot be greater than To Date."))

    if filters.account:
        account_type = frappe.db.get_value(
            "Account",
            filters.account,
            "account_type"
        )

        if account_type != "Cash":
            frappe.throw(_("Please select a Cash Account."))


def get_columns():

    return [
        {
            "label": _("ID"),
            "fieldname": "journal_entry",
            "fieldtype": "Link",
            "options": "Journal Entry",
            "width": 160
        },
		{
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 110
        },
		{
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Data",
            "width": 160
        },
		{
			"label": _("Reference Type"),
			"fieldname": "reference_type",
			"fieldtype": "Data",
			"width": 130
		},
		{
            "label": _("Account"),
            "fieldname": "account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200
        },
        {
            "label": _("Cost Center"),
            "fieldname": "custom_cost_center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 150
        },
        {
            "label": _("Debit"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Credit"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "width": 120
        },
		{
            "label": _("User Remark"),
            "fieldname": "user_remark",
            "fieldtype": "Data",
            "width": 200
        }
		# {
        #     "label": _("Company"),
        #     "fieldname": "company",
        #     "fieldtype": "Link",
        #     "options": "Company",
        #     "width": 180
        # },
        # {
        #     "label": _("Company GSTIN"),
        #     "fieldname": "company_gstin",
        #     "fieldtype": "Data",
        #     "width": 140
        # },
        # {
        #     "label": _("Entry Type"),
        #     "fieldname": "voucher_type",
        #     "fieldtype": "Data",
        #     "width": 120
        # },
		# {
        #     "label": _("Account Cost Center"),
        #     "fieldname": "account_cost_center",
        #     "fieldtype": "Link",
        #     "options": "Cost Center",
        #     "width": 160
        # },
		# {
        #     "label": _("Series"),
        #     "fieldname": "naming_series",
        #     "fieldtype": "Data",
        #     "width": 140
        # },
        
        # {
        #     "label": _("Multi Currency"),
        #     "fieldname": "multi_currency",
        #     "fieldtype": "Check",
        #     "width": 110
        # },
        # {
        #     "label": _("Consider for TDS"),
        #     "fieldname": "apply_tds",
        #     "fieldtype": "Check",
        #     "width": 110
        # },
        # {
        #     "label": _("Reference Id"),
        #     "fieldname": "custom_reference_id",
        #     "fieldtype": "Data",
        #     "width": 150
        # },
        # {
        #     "label": _("Total Debit"),
        #     "fieldname": "total_debit",
        #     "fieldtype": "Currency",
        #     "width": 120
        # },
        # {
        #     "label": _("Total Credit"),
        #     "fieldname": "total_credit",
        #     "fieldtype": "Currency",
        #     "width": 120
        # },
        # {
        #     "label": _("Reference Number"),
        #     "fieldname": "cheque_no",
        #     "fieldtype": "Data",
        #     "width": 140
        # },
        # {
        #     "label": _("Reference Date"),
        #     "fieldname": "cheque_date",
        #     "fieldtype": "Date",
        #     "width": 110
        # },
       
    ]


def get_data(filters):

    conditions = [
        "je.docstatus = 1",
        "je.voucher_type = 'Cash Entry'"
    ]

    values = {}

    if filters.from_date:
        conditions.append("je.posting_date >= %(from_date)s")
        values["from_date"] = filters.from_date

    if filters.to_date:
        conditions.append("je.posting_date <= %(to_date)s")
        values["to_date"] = filters.to_date

    if filters.account:
        conditions.append("jea.account = %(account)s")
        values["account"] = filters.account

    if filters.party_type:
        conditions.append("jea.party_type = %(party_type)s")
        values["party_type"] = filters.party_type

    if filters.party:
        conditions.append("jea.party = %(party)s")
        values["party"] = filters.party

    if filters.cost_center:
        conditions.append("jea.cost_center = %(cost_center)s")
        values["cost_center"] = filters.cost_center

    where_clause = " AND ".join(conditions)

    data = frappe.db.sql(
        f"""
        SELECT
            je.name AS journal_entry,
            je.company,
            je.company_gstin,
            je.voucher_type,
            je.custom_cost_center,
            je.naming_series,
            je.posting_date,
            je.multi_currency,
            je.apply_tds,
            je.custom_reference_id,

            jea.account,
            jea.party_type,
            jea.party,
			jea.reference_type AS reference_type,
            jea.cost_center AS account_cost_center,
            jea.debit,
            jea.credit,

            je.total_debit,
            je.total_credit,
            je.cheque_no,
            je.cheque_date,
            je.user_remark

        FROM
            `tabJournal Entry` je

        INNER JOIN
            `tabJournal Entry Account` jea
            ON jea.parent = je.name
            AND jea.parenttype = 'Journal Entry'
            AND jea.parentfield = 'accounts'

        WHERE
            {where_clause}

        ORDER BY
            je.posting_date ASC,
            je.name ASC,
            jea.idx ASC
        """,
        values,
        as_dict=True
    )

    return data
