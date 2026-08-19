import frappe
from frappe.utils import date_diff, escape_html, getdate, today

def send_maturity_notifications():
 now=getdate(today())
 for company in frappe.get_all("Company",filters={"enable_forward_maturity_notifications":1},fields=["name","notify_before_days","forex_manager_role"]):
  days={int(x.strip()) for x in (company.notify_before_days or "7,3,1,0").split(",") if x.strip().lstrip("-").isdigit()}
  role=company.forex_manager_role or "Forex Manager"
  users=frappe.get_all("Has Role",filters={"role":role,"parenttype":"User"},pluck="parent")
  recipients=[u for u in users if "@" in u and frappe.db.get_value("User",u,"enabled")]
  if not recipients: continue
  due=[]
  for row in frappe.get_all("Forward Contract",filters={"company":company.name,"docstatus":1,"available_amount":[">",0]},fields=["name","bank","currency","available_amount","maturity_date","revised_maturity_date"]):
   row.days_remaining=date_diff(getdate(row.revised_maturity_date or row.maturity_date),now)
   if row.days_remaining in days: due.append(row)
  if due:
   body="".join(f"<tr><td>{escape_html(x.name)}</td><td>{escape_html(x.bank or '')}</td><td>{escape_html(x.currency)} {x.available_amount}</td><td>{x.revised_maturity_date or x.maturity_date}</td><td>{x.days_remaining}</td></tr>" for x in due)
   frappe.sendmail(recipients=recipients,subject=f"Forward contracts maturing - {company.name}",message=f"<p>Open forward contracts have reached a configured reminder date.</p><table border='1' cellpadding='5'><tr><th>Contract</th><th>Bank</th><th>Available</th><th>Maturity</th><th>Days</th></tr>{body}</table>")

def install():
 method="export_sanpra.export_sanpra.forex_notifications.send_maturity_notifications"
 if not frappe.db.exists("Scheduled Job Type",{"method":method}):
  frappe.get_doc({"doctype":"Scheduled Job Type","method":method,"frequency":"Daily"}).insert(ignore_permissions=True)
 frappe.db.commit()
