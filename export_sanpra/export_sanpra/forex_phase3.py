import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

SALES_ORDER_JS="""frappe.ui.form.on('Sales Order',{refresh(frm){if(frm.doc.docstatus===1&&frm.doc.currency!==frappe.defaults.get_default('currency')){frm.add_custom_button(__('Forward Contract'),()=>frappe.model.open_mapped_doc({method:'export_sanpra.export_sanpra.forex_api.make_forward_contract',frm}),__('Create'));}}});"""
SALES_INVOICE_JS="""frappe.ui.form.on('Sales Invoice',{refresh(frm){if(frm.doc.docstatus===1&&frm.doc.currency!==frappe.defaults.get_default('currency')){frm.add_custom_button(__('Forward Utilization'),async()=>{let rows=await frappe.call({method:'export_sanpra.export_sanpra.forex_api.eligible_contracts',args:{company:frm.doc.company,customer:frm.doc.customer,currency:frm.doc.currency}});if(!rows.message.length){frappe.msgprint(__('No eligible Forward Contract'));return;}let d=new frappe.ui.Dialog({title:__('Select Forward Contract'),fields:[{fieldname:'forward_contract',label:__('Forward Contract'),fieldtype:'Select',options:rows.message.map(x=>x.name),reqd:1}],primary_action_label:__('Create'),primary_action(v){frappe.model.open_mapped_doc({method:'export_sanpra.export_sanpra.forex_api.make_utilization',frm,args:{forward_contract:v.forward_contract,sales_invoice:frm.doc.name}});d.hide();}});d.show();},__('Create'));}}});"""
PAYMENT_JS="""frappe.ui.form.on('Payment Entry',{forward_contract(frm){if(frm.doc.forward_contract){frappe.db.get_value('Forward Contract',frm.doc.forward_contract,['forward_rate','available_amount']).then(r=>frm.set_value('actual_bank_rate',r.message.forward_rate));}}});"""

def _client_script(name,dt,script):
 values={"dt":dt,"view":"Form","enabled":1,"script":script}
 if frappe.db.exists("Client Script",name): frappe.db.set_value("Client Script",name,values)
 else: frappe.get_doc({"doctype":"Client Script","name":name,**values}).insert(ignore_permissions=True)

def install():
 create_custom_fields({"Company":[{"fieldname":"enable_forward_maturity_notifications","label":"Enable Forward Maturity Notifications","fieldtype":"Check","insert_after":"default_forex_cost_center"},{"fieldname":"notify_before_days","label":"Notify Before Days","fieldtype":"Data","default":"7,3,1,0","description":"Comma-separated days","insert_after":"enable_forward_maturity_notifications"},{"fieldname":"forex_manager_role","label":"Forex Manager Role","fieldtype":"Link","options":"Role","default":"Forex Manager","insert_after":"notify_before_days"}]},update=True)
 _client_script("Forex - Sales Order","Sales Order",SALES_ORDER_JS); _client_script("Forex - Sales Invoice","Sales Invoice",SALES_INVOICE_JS); _client_script("Forex - Payment Entry","Payment Entry",PAYMENT_JS)
 method="export_sanpra.export_sanpra.forex_tasks.update_maturity_indicators"
 if not frappe.db.exists("Scheduled Job Type",{"method":method}): frappe.get_doc({"doctype":"Scheduled Job Type","method":method,"frequency":"Daily"}).insert(ignore_permissions=True)
 frappe.db.commit()
