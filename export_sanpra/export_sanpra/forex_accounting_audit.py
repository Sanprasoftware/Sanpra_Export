import uuid

import frappe
from frappe.utils import add_days, flt, today


def _account(company, root_type):
    return frappe.get_all(
        "Account",
        filters={"company": company, "root_type": root_type, "is_group": 0, "account_currency": "INR", "account_type": ["not in", ["Receivable", "Payable"]]},
        pluck="name",
        limit=1,
    )[0]


def run():
    savepoint = "forex_accounting_audit"
    frappe.db.savepoint(savepoint)
    try:
        company = frappe.get_all("Company", filters={"default_currency": "INR"}, pluck="name", limit=1)[0]
        order = frappe.get_all(
            "Sales Order",
            filters={"company": company, "docstatus": 1, "currency": ["!=", "INR"], "grand_total": [">", 100]},
            fields=["name", "customer", "currency", "grand_total"],
            limit=1,
        )[0]
        bank_account = frappe.get_all(
            "Bank Account",
            filters={"company": company, "account": ["is", "set"]},
            fields=["name", "bank", "account"],
            limit=1,
        )[0]
        income = _account(company, "Income")
        expense = _account(company, "Expense")
        balance = _account(company, "Asset")
        cost_center = frappe.get_all("Cost Center", filters={"company": company, "is_group": 0}, pluck="name", limit=1)[0]
        settings = {
            "enable_auto_forward_settlement_gl": 1,
            "enable_forward_mtm_gl": 1,
            "forward_contract_gain_account": income,
            "forward_contract_loss_account": expense,
            "forex_bank_charge_account": expense,
            "forward_mtm_gain_account": income,
            "forward_mtm_loss_account": expense,
            "forward_mtm_balance_account": balance,
            "default_forex_cost_center": cost_center,
        }
        frappe.db.set_value("Company", company, settings, update_modified=False)

        contract = frappe.get_doc({
            "doctype": "Forward Contract", "company": company,
            "contract_number": f"GL-AUDIT-{uuid.uuid4().hex[:10]}", "contract_type": "Export",
            "bank": bank_account.bank, "bank_account": bank_account.name, "booking_date": today(),
            "maturity_date": add_days(today(), 30), "currency": order.currency, "company_currency": "INR",
            "contract_amount": 100, "forward_rate": 84.5, "customer": order.customer,
            "sales_order": order.name, "sales_order_currency": order.currency, "sales_order_total": order.grand_total,
        }).insert(ignore_permissions=True)
        contract.submit()
        utilization = frappe.get_doc({
            "doctype": "Forward Contract Utilization", "company": company, "forward_contract": contract.name,
            "sales_order": order.name, "customer": order.customer, "utilization_date": today(),
            "currency": order.currency, "utilized_amount": 40, "forward_rate": 84.5,
        }).insert(ignore_permissions=True)
        utilization.submit()
        settlement = frappe.get_doc({
            "doctype": "Forward Contract Settlement", "company": company, "forward_contract": contract.name,
            "bank": bank_account.bank, "settlement_date": today(), "currency": order.currency,
            "settlement_amount": 40, "forward_rate": 84.5, "actual_bank_rate": 84,
            "reference_value": 3320, "bank_charge": 5,
        }).insert(ignore_permissions=True)
        settlement.submit()
        settlement.reload()
        settlement_je = frappe.get_doc("Journal Entry", settlement.journal_entry)

        mtm_contract = frappe.copy_doc(contract)
        mtm_contract.name = None
        mtm_contract.contract_number = f"MTM-AUDIT-{uuid.uuid4().hex[:10]}"
        mtm_contract.utilized_amount = 0
        mtm_contract.available_amount = 100
        mtm_contract.docstatus = 0
        mtm_contract.insert(ignore_permissions=True)
        mtm_contract.submit()
        valuation1 = frappe.get_doc({
            "doctype": "Forward Contract Valuation", "forward_contract": mtm_contract.name,
            "valuation_date": today(), "market_rate": 84,
        }).insert(ignore_permissions=True)
        valuation1.submit()
        valuation2 = frappe.get_doc({
            "doctype": "Forward Contract Valuation", "forward_contract": mtm_contract.name,
            "valuation_date": add_days(today(), 1), "market_rate": 85,
        }).insert(ignore_permissions=True)
        valuation2.submit()
        valuation1.reload()
        valuation2.reload()

        result = {
            "settlement_hedge_difference": flt(settlement.hedge_gain_loss) == 20,
            "settlement_je_submitted": settlement_je.docstatus == 1,
            "settlement_je_balanced": flt(settlement_je.total_debit) == flt(settlement_je.total_credit) == 20,
            "mtm_first_value": flt(valuation1.mtm_value) == 50 and flt(valuation1.adjustment_amount) == 50,
            "mtm_incremental_adjustment": flt(valuation2.mtm_value) == -50 and flt(valuation2.adjustment_amount) == -100,
            "mtm_journal_entries": bool(valuation1.journal_entry and valuation2.journal_entry),
        }
        valuation2.cancel()
        valuation1.cancel()
        settlement.cancel()
        settlement_je_status = frappe.db.get_value("Journal Entry", settlement.journal_entry, "docstatus")
        result["settlement_je_status_after_cancel"] = settlement_je_status
        result["cancellation_cancels_je"] = settlement_je_status == 2
        result["all_passed"] = all(result.values())
        return result
    finally:
        frappe.db.rollback(save_point=savepoint)
