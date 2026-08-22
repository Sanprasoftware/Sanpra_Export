frappe.ui.form.on("Journal Entry", {
	refresh(frm) {
		if (frm.__blank_accounts_add_patched) return;

		// ERPNext normally copies Account, Party and the outstanding difference
		// from existing rows here. Keep a genuinely new row at its defaults.
		frm.cscript.accounts_add = function (doc, cdt, cdn) {
			const row = frappe.get_doc(cdt, cdn);
			if (!row.exchange_rate) row.exchange_rate = 1;
			frm.cscript.update_totals(doc);
		};

		frm.__blank_accounts_add_patched = true;
	},
});
