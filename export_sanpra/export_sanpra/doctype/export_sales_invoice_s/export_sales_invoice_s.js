// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Export Sales Invoice s", {
	ocean_freight_usdfcl: update_less_freight_insurance,
	cif_insurance: update_less_freight_insurance,
});

function update_less_freight_insurance(frm) {
	return frm.set_value("less_freight_insuranceusd",
		flt(frm.doc.ocean_freight_usdfcl) + flt(frm.doc.cif_insurance));
}
