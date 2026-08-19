import frappe

COMPANY_JS="""frappe.ui.form.on('Company',{setup(frm){const account=(root_type)=>()=>({filters:{company:frm.doc.name,is_group:0,root_type}});frm.set_query('forex_gain_account',account('Income'));frm.set_query('forward_contract_gain_account',account('Income'));frm.set_query('forward_mtm_gain_account',account('Income'));frm.set_query('forex_loss_account',account('Expense'));frm.set_query('forward_contract_loss_account',account('Expense'));frm.set_query('forex_bank_charge_account',account('Expense'));frm.set_query('forward_mtm_loss_account',account('Expense'));frm.set_query('forward_mtm_balance_account',()=>({filters:{company:frm.doc.name,is_group:0}}));frm.set_query('default_forex_cost_center',()=>({filters:{company:frm.doc.name,is_group:0}}));}});"""

def install():
 values={"dt":"Company","view":"Form","enabled":1,"script":COMPANY_JS}
 name="Forex - Company Account Filters"
 if frappe.db.exists("Client Script",name): frappe.db.set_value("Client Script",name,values)
 else: frappe.get_doc({"doctype":"Client Script","name":name,**values}).insert(ignore_permissions=True)
 frappe.db.commit()
