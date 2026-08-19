frappe.ui.form.on("Forward Contract Settlement", {
 forward_contract(frm) {
  if (!frm.doc.forward_contract) return;
  frappe.db.get_value("Forward Contract", frm.doc.forward_contract, ["company", "bank", "currency", "forward_rate", "available_amount"]).then(({message:x}) => {
   frm.set_value({company:x.company, bank:x.bank, currency:x.currency, forward_rate:x.forward_rate, settlement_amount:x.available_amount});
  });
 },
 settlement_amount: calculate, forward_rate: calculate, actual_bank_rate: calculate, reference_value: calculate
});
function calculate(frm) {
 const amount=flt(frm.doc.settlement_amount), actual=amount*flt(frm.doc.actual_bank_rate);
 frm.set_value({forward_value:amount*flt(frm.doc.forward_rate),actual_value:actual,gain_loss:actual-flt(frm.doc.reference_value),hedge_gain_loss:amount*flt(frm.doc.forward_rate)-actual});
}
