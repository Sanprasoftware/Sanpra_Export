frappe.ui.form.on("Forward Contract Utilization", {
 forward_contract(frm) {
  if (!frm.doc.forward_contract) return;
  frappe.db.get_value("Forward Contract",frm.doc.forward_contract,["company","sales_order","customer","currency","forward_rate","available_amount"]).then(({message:x})=>frm.set_value({company:x.company,sales_order:x.sales_order,customer:x.customer,currency:x.currency,forward_rate:x.forward_rate,utilized_amount:x.available_amount}));
 },
 sales_invoice(frm) {
  if (frm.doc.sales_invoice) frappe.db.get_value("Sales Invoice",frm.doc.sales_invoice,"conversion_rate").then(({message:x})=>frm.set_value("reference_exchange_rate",x.conversion_rate));
 }
});
