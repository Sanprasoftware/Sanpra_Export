import frappe
from frappe.utils import cint, flt, getdate, today

def _where(filters, mapping):
 parts=[]; values={}
 for key,column in mapping.items():
  if filters.get(key): parts.append(f"{column}=%({key})s"); values[key]=filters[key]
 return (" and "+" and ".join(parts) if parts else ""),values
def _ranges(filters, where, values, mapping):
 for key,(column,operator) in mapping.items():
  if filters.get(key): where += f" and {column}{operator}%({key})s"; values[key]=filters[key]
 return where,values


def contract_register(filters=None):
 filters=frappe._dict(filters or {}); where,v=_where(filters,{"company":"fc.company","bank":"fc.bank","customer":"fc.customer","currency":"fc.currency","status":"fc.status","sales_order":"fc.sales_order"})
 where,v=_ranges(filters,where,v,{"booking_date_from":("fc.booking_date",">="),"booking_date_to":("fc.booking_date","<="),"maturity_date_from":("fc.maturity_date",">="),"maturity_date_to":("fc.maturity_date","<=")})
 data=frappe.db.sql(f"""select fc.name forward_contract,fc.contract_number,fc.company,fc.bank,fc.customer,fc.sales_order,fc.currency,fc.booking_date,fc.maturity_date,fc.contract_amount,fc.forward_rate,fc.contract_value_company_currency,fc.utilized_amount,fc.available_amount,fc.utilization_percentage,fc.status from `tabForward Contract` fc where fc.docstatus=1 {where} order by fc.maturity_date""",v,as_dict=True)
 cols=["Forward Contract:Link/Forward Contract:150","Contract Number:Data:130","Company:Link/Company:140","Bank:Link/Bank:120","Customer:Link/Customer:140","Sales Order:Link/Sales Order:130","Currency:Link/Currency:80","Booking Date:Date:100","Maturity Date:Date:100","Contract Amount:Currency:120","Forward Rate:Float:90","Contract Value:Currency:130","Utilized Amount:Currency:120","Available Amount:Currency:120","Utilization %:Percent:100","Status:Data:100"]
 return cols,data

def open_contracts(filters=None):
 cols,data=contract_register(filters); now=getdate(today()); out=[]
 for r in data:
  if flt(r.available_amount)>0 and r.status in ("Open","Partly Utilized","Matured"):
   r.days_to_maturity=(getdate(r.maturity_date)-now).days
   r.indicator="Expired" if r.days_to_maturity<0 else "Due Soon" if r.days_to_maturity<=7 else "Upcoming" if r.days_to_maturity<=30 else "Normal"; out.append(r)
 return cols+["Days to Maturity:Int:110","Indicator:Data:100"],out

def utilization(filters=None):
 filters=frappe._dict(filters or {}); where,v=_where(filters,{"company":"u.company","forward_contract":"u.forward_contract","customer":"u.customer","sales_order":"u.sales_order","sales_invoice":"u.sales_invoice","currency":"u.currency"})
 where,v=_ranges(filters,where,v,{"from_date":("u.utilization_date",">="),"to_date":("u.utilization_date","<=")})
 return ["Utilization:Link/Forward Contract Utilization:160","Date:Date:100","Forward Contract:Link/Forward Contract:150","Contract Number:Data:130","Bank:Link/Bank:120","Customer:Link/Customer:140","Sales Order:Link/Sales Order:130","Sales Invoice:Link/Sales Invoice:130","Payment Entry:Link/Payment Entry:130","Currency:Link/Currency:80","Utilized Amount:Currency:120","Forward Rate:Float:90","Settlement Rate:Float:100","Forex Gain/Loss:Currency:120"],frappe.db.sql(f"""select u.name utilization,u.utilization_date date,u.forward_contract,fc.contract_number,fc.bank,u.customer,u.sales_order,u.sales_invoice,u.payment_entry,u.currency,u.utilized_amount,u.forward_rate,u.settlement_rate,u.forex_gain_loss from `tabForward Contract Utilization` u join `tabForward Contract` fc on fc.name=u.forward_contract where u.docstatus=1 {where} order by u.utilization_date desc""",v,as_dict=True)

def order_booking(filters=None):
 filters=frappe._dict(filters or {}); where,v=_where(filters,{"company":"so.company","customer":"so.customer","currency":"so.currency"})
 columns=["Sales Order:Link/Sales Order:140","Date:Date:100","Customer:Link/Customer:150","Currency:Link/Currency:80","Sales Order Amount:Currency:130","Forward Booked:Currency:120","Forward Utilized:Currency:120","Remaining Forward:Currency:130","Unhedged Exposure:Currency:130","Hedge %:Percent:90","Delivery Date:Date:100","Contract Count:Int:100"]
 data=frappe.db.sql(f"""select so.name sales_order,so.transaction_date date,so.customer,so.currency,so.grand_total sales_order_amount,
  coalesce(a.forward_booked,0) forward_booked,coalesce(u.forward_utilized,0) forward_utilized,
  greatest(coalesce(a.forward_booked,0)-coalesce(u.forward_utilized,0),0) remaining_forward,
  greatest(so.grand_total-coalesce(a.forward_booked,0),0) unhedged_exposure,
  case when so.grand_total then coalesce(a.forward_booked,0)/so.grand_total*100 else 0 end hedge_percentage,
  so.delivery_date,coalesce(a.contract_count,0) contract_count
  from `tabSales Order` so
  left join (
   select x.sales_order,sum(x.booked) forward_booked,count(distinct x.contract_name) contract_count from (
    select row.sales_order,fc.name contract_name,row.booked_amount*greatest(fc.contract_amount-fc.cancellation_amount,0)/nullif(fc.contract_amount,0) booked
    from `tabForward Contract Sales Order` row join `tabForward Contract` fc on fc.name=row.parent
    where fc.docstatus=1 and fc.status!='Closed'
    union all
    select fc.sales_order,fc.name,greatest(fc.contract_amount-fc.cancellation_amount,0)
    from `tabForward Contract` fc where fc.docstatus=1 and fc.status!='Closed' and fc.sales_order is not null
     and not exists (select 1 from `tabForward Contract Sales Order` row where row.parent=fc.name)
   ) x group by x.sales_order
  ) a on a.sales_order=so.name
  left join (select sales_order,sum(utilized_amount) forward_utilized from `tabForward Contract Utilization` where docstatus=1 group by sales_order) u on u.sales_order=so.name
  where so.docstatus=1 {where} order by so.transaction_date desc""",v,as_dict=True)
 return columns,data

def maturity(filters=None):
 cols,data=open_contracts(filters); now=getdate(today())
 for r in data:
  d=r.days_to_maturity; r.category="Overdue" if d<0 else "Due Today" if d==0 else "Next 7 Days" if d<=7 else "Next 15 Days" if d<=15 else "Next 30 Days" if d<=30 else "Later"
 return cols+["Category:Data:100"],data

def bank_summary(filters=None):
 where,v=_where(frappe._dict(filters or {}),{"company":"fc.company","bank":"fc.bank","currency":"fc.currency"})
 return ["Bank:Link/Bank:150","Currency:Link/Currency:80","Contracts:Int:80","Total Contract Amount:Currency:140","Total Utilized:Currency:120","Total Available:Currency:120","Average Forward Rate:Float:120","Gain/Loss:Currency:120","Maturing in 7 Days:Int:120","Maturing in 30 Days:Int:130"],frappe.db.sql(f"""select fc.bank,fc.currency,count(*) contracts,sum(fc.contract_amount) total_contract_amount,sum(fc.utilized_amount) total_utilized,sum(fc.available_amount) total_available,sum(fc.contract_amount*fc.forward_rate)/nullif(sum(fc.contract_amount),0) average_forward_rate,coalesce(sum(s.gain_loss),0) `gain/loss`,sum(case when datediff(fc.maturity_date,current_date) between 0 and 7 then 1 else 0 end) maturing_in_7_days,sum(case when datediff(fc.maturity_date,current_date) between 0 and 30 then 1 else 0 end) maturing_in_30_days from `tabForward Contract` fc left join `tabForward Contract Settlement` s on s.forward_contract=fc.name and s.docstatus=1 where fc.docstatus=1 {where} group by fc.bank,fc.currency""",v,as_dict=True)

def exposure(filters=None):
 cols,data=order_booking(filters); chart={"data":{"labels":[r.sales_order for r in data],"datasets":[{"name":"Hedged","values":[flt(r.forward_booked) for r in data]},{"name":"Unhedged","values":[flt(r.unhedged_exposure) for r in data]}]},"type":"bar"}
 return cols,data,None,chart

def gain_loss(filters=None):
 filters=frappe._dict(filters or {}); where,v=_where(filters,{"company":"u.company","customer":"u.customer","bank":"fc.bank","currency":"u.currency","forward_contract":"u.forward_contract"})
 where,v=_ranges(filters,where,v,{"from_date":("u.utilization_date",">="),"to_date":("u.utilization_date","<=")})
 columns=["Forward Contract:Link/Forward Contract:150","Utilization:Link/Forward Contract Utilization:150","Settlement:Link/Forward Contract Settlement:150","Customer:Link/Customer:140","Sales Invoice:Link/Sales Invoice:130","Payment Entry:Link/Payment Entry:130","Currency:Link/Currency:80","Foreign Amount:Currency:120","Invoice Exchange Rate:Float:120","Forward Rate:Float:90","Actual Bank Rate:Float:110","Invoice Value:Currency:120","Forward Value:Currency:120","Actual Realization:Currency:130","Exchange Gain/Loss:Currency:130","Forward Gain/Loss:Currency:130","Bank Charges:Currency:100","Net Gain/Loss:Currency:120"]
 data=frappe.db.sql(f"""select u.forward_contract,u.name utilization,s.name settlement,u.customer,u.sales_invoice,u.payment_entry,u.currency,u.utilized_amount foreign_amount,u.reference_exchange_rate invoice_exchange_rate,u.forward_rate,s.actual_bank_rate,u.utilized_amount*u.reference_exchange_rate invoice_value,u.utilized_amount*u.forward_rate forward_value,s.actual_value actual_realization,u.forex_gain_loss exchange_gain_loss,s.gain_loss forward_gain_loss,s.bank_charge bank_charges,coalesce(u.forex_gain_loss,0)+coalesce(s.gain_loss,0)-coalesce(s.bank_charge,0) net_gain_loss from `tabForward Contract Utilization` u join `tabForward Contract` fc on fc.name=u.forward_contract left join `tabForward Contract Settlement` s on s.forward_contract=u.forward_contract and s.docstatus=1 where u.docstatus=1 {where}""",v,as_dict=True)
 return columns,data
