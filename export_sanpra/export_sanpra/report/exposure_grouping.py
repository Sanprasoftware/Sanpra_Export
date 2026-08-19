import frappe
from frappe.utils import flt
from export_sanpra.export_sanpra.report.forex_reports import order_booking

DIMENSIONS={"Currency":"currency","Customer":"customer","Sales Order":"sales_order"}

def execute(filters=None):
 filters=frappe._dict(filters or {}); group_by=filters.get("group_by") or "Currency"
 if group_by=="Bank": return _by_bank(filters)
 _,orders=order_booking(filters); field=DIMENSIONS.get(group_by,"currency"); grouped={}
 for row in orders:
  key=row.get(field) or "Not Set"; item=grouped.setdefault(key,{"group":key,"total_export_exposure":0,"total_forward_booked":0,"total_utilized":0,"available_forward_balance":0,"unhedged_exposure":0})
  item["total_export_exposure"]+=flt(row.sales_order_amount); item["total_forward_booked"]+=flt(row.forward_booked); item["total_utilized"]+=flt(row.forward_utilized); item["available_forward_balance"]+=flt(row.remaining_forward); item["unhedged_exposure"]+=flt(row.unhedged_exposure)
 data=[frappe._dict(row) for row in grouped.values()]; _percent(data)
 return _response(group_by,data)

def _by_bank(filters):
 conditions=["fc.docstatus=1"]; values={}
 for key,column in (("company","fc.company"),("currency","fc.currency"),("customer","fc.customer")):
  if filters.get(key): conditions.append(f"{column}=%({key})s"); values[key]=filters[key]
 data=frappe.db.sql(f"""select coalesce(fc.bank,'Not Set') `group`,sum(so.grand_total*fc.contract_amount/nullif(t.booked,0)) total_export_exposure,sum(fc.contract_amount-fc.cancellation_amount) total_forward_booked,sum(fc.utilized_amount) total_utilized,sum(fc.available_amount) available_forward_balance,greatest(sum(so.grand_total*fc.contract_amount/nullif(t.booked,0))-sum(fc.contract_amount-fc.cancellation_amount),0) unhedged_exposure from `tabForward Contract` fc join `tabSales Order` so on so.name=fc.sales_order join (select sales_order,sum(contract_amount) booked from `tabForward Contract` where docstatus=1 group by sales_order) t on t.sales_order=fc.sales_order where {' and '.join(conditions)} group by fc.bank order by fc.bank""",values,as_dict=True)
 _percent(data); return _response("Bank",data)

def _percent(data):
 for row in data: row["hedge_percentage"]=flt(row.total_forward_booked)/flt(row.total_export_exposure)*100 if row.total_export_exposure else 0

def _response(label,data):
 columns=[f"{label}:Data:180","Total Export Exposure:Currency:150","Total Forward Booked:Currency:150","Total Utilized:Currency:130","Available Forward Balance:Currency:160","Unhedged Exposure:Currency:150","Hedge %:Percent:100"]
 chart={"data":{"labels":[r.group for r in data],"datasets":[{"name":"Hedged","values":[flt(r.total_forward_booked) for r in data]},{"name":"Unhedged","values":[flt(r.unhedged_exposure) for r in data]}]},"type":"bar"}
 summary=[{"label":"Export Exposure","value":sum(flt(r.total_export_exposure) for r in data),"indicator":"Blue","datatype":"Currency"},{"label":"Forward Booked","value":sum(flt(r.total_forward_booked) for r in data),"indicator":"Green","datatype":"Currency"},{"label":"Unhedged","value":sum(flt(r.unhedged_exposure) for r in data),"indicator":"Orange","datatype":"Currency"}]
 return columns,data,None,chart,summary
