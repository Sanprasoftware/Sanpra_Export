import frappe
from frappe import _
from frappe.utils import flt


def _company_settings(company):
    return frappe.db.get_value(
        "Company",
        company,
        [
            "default_currency",
            "enable_auto_forward_settlement_gl",
            "enable_forward_mtm_gl",
            "forward_contract_gain_account",
            "forward_contract_loss_account",
            "forex_bank_charge_account",
            "forward_mtm_gain_account",
            "forward_mtm_loss_account",
            "forward_mtm_balance_account",
            "default_forex_cost_center",
        ],
        as_dict=True,
    )


def _validate_account(account, company, label, company_currency):
    if not account:
        frappe.throw(_("Configure {0} in Company {1}").format(label, company))
    values = frappe.db.get_value("Account", account, ["company", "is_group", "account_currency", "account_type"], as_dict=True)
    if not values or values.company != company or values.is_group:
        frappe.throw(_("{0} must be a ledger account for Company {1}").format(label, company))
    if values.account_currency != company_currency:
        frappe.throw(_("{0} must use company currency {1}").format(label, company_currency))
    if values.account_type in ("Receivable", "Payable"):
        frappe.throw(_("{0} cannot be a Receivable or Payable account").format(label))
    return account


def _journal_series(kind):
    options = (frappe.get_meta("Journal Entry").get_field("naming_series").options or "").splitlines()
    options = [option.strip() for option in options if option.strip()]
    preferred = "PROV" if kind == "mtm" else "REM"
    return next((option for option in options if preferred in option.upper()), options[0] if options else None)


def _make_journal_entry(company, posting_date, remark, lines, kind, source_name):
    settings = _company_settings(company)
    accounts = []
    for line in lines:
        amount = flt(line.get("amount"), 2)
        if not amount:
            continue
        account = _validate_account(line.get("account"), company, line.get("label") or "Account", settings.default_currency)
        row = {"account": account, "cost_center": line.get("cost_center") or settings.default_forex_cost_center}
        row["debit_in_account_currency" if amount > 0 else "credit_in_account_currency"] = abs(amount)
        accounts.append(row)
    if not accounts:
        return None
    debit = sum(flt(row.get("debit_in_account_currency")) for row in accounts)
    credit = sum(flt(row.get("credit_in_account_currency")) for row in accounts)
    if flt(debit-credit, 2):
        frappe.throw(_("Forward accounting Journal Entry is not balanced"))
    journal_entry = frappe.get_doc({
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "naming_series": _journal_series(kind),
        "company": company,
        "posting_date": posting_date,
        "user_remark": remark,
        "accounts": accounts,
    })
    journal_entry.set_new_name(set_name=f"FC-{kind.upper()}-{source_name}")
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    return journal_entry.name


def create_settlement_journal_entry(settlement):
    settings = _company_settings(settlement.company)
    if not settings.enable_auto_forward_settlement_gl:
        return None
    contract = frappe.get_doc("Forward Contract", settlement.forward_contract)
    bank_account = frappe.db.get_value("Bank Account", contract.bank_account, ["account", "company"], as_dict=True) if contract.bank_account else None
    if not bank_account or bank_account.company != settlement.company:
        frappe.throw(_("Forward Contract must have a Bank Account linked to Company {0}").format(settlement.company))
    hedge = flt(settlement.hedge_gain_loss, 2)
    charge = flt(settlement.bank_charge, 2)
    lines = []
    bank_net = hedge-charge
    if bank_net:
        lines.append({"account": bank_account.account, "amount": bank_net, "label": "Forward Contract Bank Account"})
    if hedge > 0:
        lines.append({"account": settings.forward_contract_gain_account, "amount": -hedge, "label": "Forward Contract Gain Account", "cost_center": settings.default_forex_cost_center})
    elif hedge < 0:
        lines.append({"account": settings.forward_contract_loss_account, "amount": -hedge, "label": "Forward Contract Loss Account", "cost_center": settings.default_forex_cost_center})
    if charge:
        lines.append({"account": settings.forex_bank_charge_account, "amount": charge, "label": "Forex Bank Charge Account", "cost_center": settings.default_forex_cost_center})
    return _make_journal_entry(settlement.company, settlement.settlement_date, f"Forward settlement {settlement.name} / {settlement.forward_contract}", lines, "SET", settlement.name)


def create_mtm_journal_entry(valuation):
    settings = _company_settings(valuation.company)
    if not settings.enable_forward_mtm_gl:
        frappe.throw(_("Enable Forward MTM GL in Company {0}").format(valuation.company))
    adjustment = flt(valuation.adjustment_amount, 2)
    if not adjustment:
        return None
    balance = {"account": settings.forward_mtm_balance_account, "amount": adjustment, "label": "Forward MTM Asset / Liability Account"}
    if adjustment > 0:
        pnl = {"account": settings.forward_mtm_gain_account, "amount": -adjustment, "label": "Forward MTM Unrealized Gain Account", "cost_center": settings.default_forex_cost_center}
    else:
        pnl = {"account": settings.forward_mtm_loss_account, "amount": -adjustment, "label": "Forward MTM Unrealized Loss Account", "cost_center": settings.default_forex_cost_center}
    return _make_journal_entry(valuation.company, valuation.valuation_date, f"Forward MTM {valuation.name} / {valuation.forward_contract}", [balance, pnl], "MTM", valuation.name)


def cancel_linked_journal_entry(name, source=None):
    if not name:
        return
    if source:
        source.db_set("journal_entry", None, update_modified=False)
    try:
        journal_entry = frappe.get_doc("Journal Entry", name)
        if journal_entry.docstatus == 1:
            journal_entry.flags.ignore_permissions = True
            journal_entry.cancel()
    finally:
        if source:
            source.db_set("journal_entry", name, update_modified=False)
            source.journal_entry = name
