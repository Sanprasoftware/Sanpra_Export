import frappe

REPORTS=["Forward Contract Register","Open Forward Contracts","Forward Contract Utilization Report","Export Order vs Forward Booking","Hedged vs Unhedged Exposure","Contract Maturity Report","Forex Gain Loss Report","Bank Wise Forward Contract Summary"]

def install():
 for name in REPORTS:
  if not frappe.db.exists("Report",name):
   frappe.get_doc({"doctype":"Report","report_name":name,"ref_doctype":"Forward Contract","report_type":"Script Report","is_standard":"Yes","module":"Export Sanpra"}).insert(ignore_permissions=True)
 doctype_links=[{"type":"Link","label":"Forward Contract","link_type":"DocType","link_to":"Forward Contract"},{"type":"Link","label":"Forward Contract Utilization","link_type":"DocType","link_to":"Forward Contract Utilization"},{"type":"Link","label":"Forward Contract Settlement","link_type":"DocType","link_to":"Forward Contract Settlement"},{"type":"Link","label":"Forward Contract Valuation","link_type":"DocType","link_to":"Forward Contract Valuation"}]
 if not frappe.db.exists("Workspace","Forex Management"):
  frappe.get_doc({"doctype":"Workspace","title":"Forex Management","label":"Forex Management","module":"Export Sanpra","public":1,"is_hidden":0,"content":"[]","links":doctype_links+[{"type":"Link","label":r,"link_type":"Report","link_to":r,"doctype":"Forward Contract"} for r in REPORTS]}).insert(ignore_permissions=True)
 frappe.db.commit()
