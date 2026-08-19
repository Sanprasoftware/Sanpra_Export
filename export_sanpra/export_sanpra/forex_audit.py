import frappe
from export_sanpra.export_sanpra import forex_api
from export_sanpra.export_sanpra.report import forex_reports

def run():
 checks={}
 functions={"register":forex_reports.contract_register,"open":forex_reports.open_contracts,"utilization":forex_reports.utilization,"order_booking":forex_reports.order_booking,"exposure":forex_reports.exposure,"maturity":forex_reports.maturity,"gain_loss":forex_reports.gain_loss,"bank_summary":forex_reports.bank_summary}
 for key,fn in functions.items():
  result=fn({"company":"Nutrich Foods Pvt Ltd"})
  checks[f"report_{key}"]={"columns":len(result[0]),"rows":len(result[1])}
 source=frappe.get_all("Sales Order",filters={"docstatus":1,"currency":["!=",frappe.get_cached_value("Company","Nutrich Foods Pvt Ltd","default_currency")]},pluck="name",limit=1)
 if source:
  mapped=forex_api.make_forward_contract(source[0])
  checks["mapping"]={"source":source[0],"sales_order":mapped.sales_order,"company":mapped.company,"customer":mapped.customer,"currency":mapped.currency,"sales_order_total":mapped.sales_order_total}
 checks["doctypes"]={name:bool(frappe.db.exists("DocType",name)) for name in ("Forward Contract","Forward Contract Utilization","Forward Contract Settlement")}
 checks["workspace"]=bool(frappe.db.exists("Workspace","Forex Management"))
 checks["client_scripts"]=frappe.db.count("Client Script",{"name":["like","Forex - %"],"enabled":1})
 checks["scheduled_jobs"]=frappe.db.count("Scheduled Job Type",{"method":["like","export_sanpra.export_sanpra.forex_%"]})
 return checks
