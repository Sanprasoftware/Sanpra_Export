import frappe
from frappe.utils import date_diff, getdate, today

def update_maturity_indicators():
 now=getdate(today())
 for row in frappe.get_all("Forward Contract",filters={"docstatus":1},fields=["name","maturity_date","revised_maturity_date","available_amount"]):
  days=date_diff(getdate(row.revised_maturity_date or row.maturity_date),now)
  value="Expired With Balance" if days<0 and row.available_amount else "Matured" if days<0 else "Due Soon" if days<=7 else "Active"
  frappe.db.set_value("Forward Contract",row.name,"maturity_status",value,update_modified=False)
 frappe.db.commit()
