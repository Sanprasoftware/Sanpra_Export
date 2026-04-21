frappe.ui.form.on("Quotation", {
	refresh(frm) {
		update_export_button(frm);
	},
	after_save(frm) {
		update_export_button(frm);
	},
});
 
function update_export_button(frm) {
	if (frm.is_new() || frm.doc.custom_quotation_type_ !== "Global") {
		frm.remove_custom_button("Export Quotation s");
		return;
	}

	frappe.db
		.get_value("Export Quotation s", { quotation_id: frm.doc.name }, "name")
		.then((r) => {
			const export_name = r && r.message && r.message.name;
			if (!export_name) {
				frm.remove_custom_button("Export Quotation s");
				return;
			}

			frm.remove_custom_button("Export Quotation s");
			frm.add_custom_button("Export Quotation s", () => {
				open_export_quotation_popup(export_name);
			});
		});
}

function open_export_quotation_popup(export_name) {
	if (!export_name) {
		return;
	}

	frappe.model.with_doctype("Export Quotation s", () => {
		frappe.db.get_doc("Export Quotation s", export_name).then((doc) => {
			const dialog = new frappe.ui.Dialog({
				title: `Export Quotation s: ${export_name}`,
				fields: get_export_quotation_fields(),
				primary_action_label: "Save",
				primary_action(values) {
					if (!values) {
						return;
					}

					const updated = { ...doc, ...values };
					frappe.call({
						method: "frappe.client.save",
						args: { doc: updated },
						callback: (r) => {
							if (!r.exc) {
								frappe.show_alert({
									message: "Export Quotation s updated",
									indicator: "green",
								});
								dialog.hide();
							}
						},
					});
				},
			});

			dialog.set_values(doc);
			set_dialog_read_only(dialog, ["quotation_id"]);
			dialog.show();
		});
	});
}

function get_export_quotation_fields() {
	const meta = frappe.get_meta("Export Quotation s");
	if (!meta) {
		return [];
	}

	const fields = [];
	(meta.fields || []).forEach((field) => {
		if (!field || !field.fieldtype) {
			return;
		}

		fields.push({
			fieldname: field.fieldname,
			fieldtype: field.fieldtype,
			label: field.label,
			options: field.options,
			hidden: field.hidden,
			depends_on: field.depends_on,
			description: field.description,
		});
	});

	return fields;
}

// function set_dialog_read_only(dialog, fieldnames) {
// 	if (!Array.isArray(fieldnames)) { return; }
// 	(dialog.fields || []).forEach((field) => {
// 		if (!field || !field.df || !field.df.fieldname) {
// 			return;
// 		}
// 		if (fieldnames.includes(field.df.fieldname)) {
// 			field.df.read_only = 1;
// 			field.refresh();
// 		}
// 	});
// }
function set_dialog_read_only(dialog, fieldnames) {
	if (!Array.isArray(fieldnames)) return;

	fieldnames.forEach(fieldname => {
		dialog.set_df_property(fieldname, "read_only", 1);
	});
}

// Child Table Calculation

frappe.ui.form.on("Quotation Item", {
	qty(frm, cdt, cdn) {
		update_item_total_before_duty(frm, cdt, cdn);
		update_custom_total_purchase_amt(frm, cdt, cdn);
		update_custom_purc_brokaerage_inr__mt(cdt, cdn)
	},

	custom_item_rate(frm, cdt, cdn) {
		update_item_total_before_duty(frm, cdt, cdn);
	},

	custom__cargo_purc_rate_inr_mt(frm, cdt, cdn) {
		update_custom_total_purchase_amt(frm, cdt, cdn);
		update_custom__cargo_shortage_inr__mt(cdt, cdn);
	},

	custom_shortage_(frm, cdt, cdn) {
		update_custom__cargo_shortage_inr__mt(cdt, cdn);
	},

	custom_purc_brokaerage_inr__mt(frm, cdt, cdn) {
		update_custom_purc_brokaerage_inr__mt(cdt, cdn);
	},

	custom_sales_comm_usd__mt(frm) {
		recalculate_custom_total_sales_commission(frm);
	},

	custom_total_purchase_amt(frm) {
		recalculate_custom_total_purchase_amt(frm);
	},
	
	custom_export_duty(frm, cdt, cdn) {
		calculate_custom_total_export_duty(frm);
	},

	custom_total_amount_before_duty(frm, cdt, cdn) {
		update_custom_export_duty_single_item(cdt, cdn);
		update_custom_export_duty(frm, cdt, cdn);
	},

	custom_export_duty_single_item(frm, cdt, cdn) {
		update_custom_export_duty(frm, cdt, cdn);
	},

});

// Total Amount Before Duty ($) 
function update_item_total_before_duty(frm, cdt, cdn) {
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) { return; } 
	frappe.call({
		method: "export_sanpra.public.py.quotation_export_quotation_s.calculate_total_amount_before_duty",
		args: {
			qty: row.qty,
			custom_item_rate: row.custom_item_rate,
		},
		callback: (r) => {
			if (!r || r.exc) { return; }
			frappe.model.set_value(cdt,cdn,"custom_total_amount_before_duty",r.message || 0);
			recalculate_custom_amount_without_duty(frm);
		},
	});
}


// Total Purchase Amt
function update_custom_total_purchase_amt(frm, cdt, cdn) {
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) { return; }
	frappe.call({
		method: "export_sanpra.public.py.quotation_export_quotation_s.calculate_custom_total_purchase_amt",
		args: {
			qty: row.qty,
			custom__cargo_purc_rate_inr_mt: row.custom__cargo_purc_rate_inr_mt,
		},
		callback: (r) => {
			if (!r || r.exc) { return; }
			frappe.model.set_value(cdt,cdn,"custom_total_purchase_amt",r.message || 0);
			recalculate_custom_total_purchase_amt(frm);
		},
	});
}

// Cargo Shortage (INR) / MT
function update_custom__cargo_shortage_inr__mt(cdt, cdn){
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) { return; }
	frappe.call({
		method: "export_sanpra.public.py.quotation_export_quotation_s.calculate_custom__cargo_shortage_inr__mt",
		args: {
			custom__cargo_purc_rate_inr_mt: row.custom__cargo_purc_rate_inr_mt,
			custom_shortage_: row.custom_shortage_,
		},
		callback: (r) => {
			if (!r || r.exc) {
				return;
			}
			frappe.model.set_value(cdt,cdn,"custom__cargo_shortage_inr__mt",r.message || 0);
		},
	}); 
}


// Purc Brokaerage Amt
function update_custom_purc_brokaerage_inr__mt(cdt, cdn){
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) { return; }
	frappe.call({
		method: "export_sanpra.public.py.quotation_export_quotation_s.calculate_custom_purc_brokaerage_inr__mt",
		args: {
			qty: row.qty,
			custom_purc_brokaerage_inr__mt: row.custom_purc_brokaerage_inr__mt,
		},
		callback: (r) => { 
			if (!r || r.exc) {
				return;
			}
			frappe.model.set_value(cdt,cdn,"custom_purc_brokaerage_amt",r.message || 0);
		},
	}); 
}


// Export Duty
function update_custom_export_duty(frm, cdt, cdn){
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) { return; }
	frappe.call({
		method: "export_sanpra.public.py.quotation_export_quotation_s.calculate_custom_export_duty",
		args: {
			custom_total_amount_before_duty: row.custom_total_amount_before_duty,
			custom_export_duty_single_item: row.custom_export_duty_single_item,
		},
		callback: (r) => { 
			if (!r || r.exc) {
				return;
			}
			frappe.model
				.set_value(cdt, cdn, "custom_export_duty", r.message || 0)
				.then(() => {
					calculate_custom_total_export_duty(frm);
				});
		},
	}); 
}  


// Export Duty Single Item (%)
function update_custom_export_duty_single_item(cdt, cdn){
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) { return; }
	frappe.call({
		method: "export_sanpra.public.py.quotation_export_quotation_s.calculate_custom_export_duty_single_item",
		args: {
			custom_export_duty: row.custom_export_duty,
			custom_total_amount_before_duty: row.custom_total_amount_before_duty,
		},
		callback: (r) => { 
			if (!r || r.exc) {
				return;
			}
			frappe.model.set_value(cdt,cdn,"custom_export_duty_single_item",r.message || 0);
		},
	}); 
}


// Amount Without Duty ($)
function recalculate_custom_amount_without_duty(frm) {
	if (!frm || !frm.doc) { return; }
	const items = frm.doc.items || [];
	let total = 0;
	for (let i = 0; i < items.length; i += 1) {
		total += flt(items[i].custom_total_amount_before_duty);
	}
	frm.set_value("custom_amount_without_duty", total);
}
 

// Total Export Duty ($)
function calculate_custom_total_export_duty(frm) {
	if (!frm || !frm.doc) { return; }
	const items = frm.doc.items || [];
	let total = 0;
	for (let i = 0; i < items.length; i += 1) {
		total += flt(items[i].custom_export_duty);
	}
	frm.set_value("custom_total_export_duty", total);
}


function recalculate_custom_total_sales_commission(frm) {
	if (!frm || !frm.doc) { return; }
	const items = frm.doc.items || [];
	let total = 0;
	for (let i = 0; i < items.length; i += 1) {
		total += flt(items[i].custom_sales_comm_usd__mt);
	}
	frm.set_value("custom_total_sales_commission", total);
}


function recalculate_custom_total_purchase_amt(frm) {
	if (!frm || !frm.doc) { return; }
	const items = frm.doc.items || [];
	let total = 0;
	for (let i = 0; i < items.length; i += 1) {
		total += flt(items[i].custom_total_purchase_amt);
	}
	frm.set_value("custom_total_purchase_amt", total);
}
