frappe.ui.form.on("Forward Contract Valuation", {
 forward_contract(frm) {
  if (!frm.doc.forward_contract) return;
  frappe.db.get_value("Forward Contract",frm.doc.forward_contract,["company","currency","contract_type","forward_rate","available_amount"]).then(({message:x})=>frm.set_value({company:x.company,currency:x.currency,contract_type:x.contract_type,forward_rate:x.forward_rate,open_amount:x.available_amount}));
 },
 market_rate: calculate
});
function calculate(frm) {
 const direction=frm.doc.contract_type==="Import"?-1:1;
 frm.set_value("mtm_value",(flt(frm.doc.forward_rate)-flt(frm.doc.market_rate))*flt(frm.doc.open_amount)*direction);
}
