frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		update_export_sales_invoice_button(frm);
	},
	after_save(frm) {
		update_export_sales_invoice_button(frm);
	},
});

async function update_export_sales_invoice_button(frm) {
	if (frm.is_new()) {
		frm.remove_custom_button("Export Sales Invoice s");
		return;
	}

	const invoice_type = (frm.doc.custom_sales_invoice_type || frm.doc.invoice_type || "").trim();
	if (invoice_type !== "Global") {
		frm.remove_custom_button("Export Sales Invoice s");
		return;
	}

	const r = await frappe.db.get_value(
		"Export Sales Invoice s",
		{ sales_invoice_id: frm.doc.name },
		"name" 
	);
	const export_name = r && r.message && r.message.name;
	if (!export_name) {
		frm.remove_custom_button("Export Sales Invoice s");
		return;
	}
  
	frm.remove_custom_button("Export Sales Invoice s");
	frm.add_custom_button("Export Sales Invoice s", () => {
		open_export_sales_invoice_popup(frm, export_name);
	});
}

function open_export_sales_invoice_popup(frm, export_name) {
	if (!export_name) {
		return;
	}

	frappe.model.with_doctype("Export Sales Invoice s", () => {
		frappe.db.get_doc("Export Sales Invoice s", export_name).then((doc) => {
			const dialog = new frappe.ui.Dialog({
				title: `Export Sales Invoice s: ${export_name}`,
				fields: get_export_sales_invoice_fields(),
				primary_action_label: "Save",
				primary_action(values) {
					if (!values) {
						return;
					}

					const updated = { ...doc, ...values };
					frappe.call({
						method: "frappe.client.save",
						args: { doc: updated },
						callback: async (r) => {
							if (!r.exc) {
								frappe.show_alert({
									message: "Export Sales Invoice s updated",
									indicator: "green",
								});
								dialog.hide();
								await frm.reload_doc();
							}
						},
					});
				},
			});

			dialog.set_values(doc);
			set_dialog_read_only(dialog, ["sales_invoice_id"]);
			dialog.show();
		});
	});
}

function get_export_sales_invoice_fields() {
	const meta = frappe.get_meta("Export Sales Invoice s");
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
// 	if (!Array.isArray(fieldnames)) {
// 		return;
// 	}
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

