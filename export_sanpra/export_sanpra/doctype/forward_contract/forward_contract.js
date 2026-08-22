frappe.ui.form.on("Forward Contract", {
 setup(frm) {
  frm.set_query("sales_order", "sales_orders", () => ({filters: {
   docstatus: 1,
   company: frm.doc.company,
   customer: frm.doc.customer,
   currency: frm.doc.currency
  }}));
 },
 refresh(frm) {
  frm.set_query("bank_account", () => ({filters: {company: frm.doc.company, is_company_account: 1}}));
  if (frm.doc.docstatus === 1 && ["Open", "Partly Utilized"].includes(frm.doc.status)) {
   frm.add_custom_button(__("Forward Utilization"), () => frappe.model.open_mapped_doc({method: "export_sanpra.export_sanpra.forex_api.make_utilization", frm, args: {forward_contract: frm.doc.name}}), __("Create"));
   frm.add_custom_button(__("Partial Cancellation"),()=>{let d=new frappe.ui.Dialog({title:__("Partial Cancellation"),fields:[{fieldname:"amount",label:__("Amount"),fieldtype:"Currency",reqd:1},{fieldname:"charge",label:__("Cancellation Charge"),fieldtype:"Currency"},{fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}],primary_action_label:__("Apply"),primary_action(v){frappe.call({method:"export_sanpra.export_sanpra.forex_actions.partial_cancel",args:{contract:frm.doc.name,...v},freeze:true}).then(()=>frm.reload_doc());d.hide();}});d.show();},__("Actions"));
   frm.add_custom_button(__("Rollover"),()=>frappe.model.open_mapped_doc({method:"export_sanpra.export_sanpra.forex_actions.make_rollover",frm,args:{contract:frm.doc.name}}),__("Actions"));
  }
  if (frm.doc.docstatus === 1 && frm.doc.status !== "Closed" && flt(frm.doc.available_amount) === 0) {
   frm.add_custom_button(__("Close Contract"),()=>frappe.confirm(__("Close this Forward Contract?"),()=>frappe.call({method:"export_sanpra.export_sanpra.forex_actions.close_contract",args:{contract:frm.doc.name},freeze:true}).then(()=>frm.reload_doc())),__("Actions"));
  }
 }
});

frappe.ui.form.on("Forward Contract Sales Order", {
 sales_order(frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  if (!row.sales_order) return;
  frappe.db.get_value("Sales Order", row.sales_order, "grand_total").then(({message}) => {
   frappe.model.set_value(cdt, cdn, "sales_order_total", message.grand_total);
   if (!row.booked_amount) frappe.model.set_value(cdt, cdn, "booked_amount", message.grand_total);
  });
 }
});
