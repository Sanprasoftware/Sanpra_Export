// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Export Budget", {
	// refresh(frm) {

	// },
	get_accounts(frm) {
        frappe.call({
            method: "get_budget_accounts",
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    console.log(r.message);
                    // frm.resfresh_field("budget_accounts");
                    frm.refresh_field("budget_accounts");
                    // frm.reload_doc();
                }
            }   
        })
	},
});
 