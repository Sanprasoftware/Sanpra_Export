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
		frappe.db.get_doc("Export Sales Invoice s", export_name).then(async (doc) => {
			if (doc.sales_invoice_id) {
				const invoice = await frappe.db.get_doc("Sales Invoice", doc.sales_invoice_id);
				const invoice_items = invoice.items || [];
				doc.fob_invoice_value_inr = flt(invoice.custom_fob_invoice_value_inr)
					|| flt(invoice.base_total);
				if (!flt(doc.duty_drawback_rate)) {
					doc.duty_drawback_rate = get_weighted_item_rate(
						invoice_items, "custom_duty_drawback_rate"
					);
				}
				if (!flt(doc.rodtepe_rate)) {
					doc.rodtepe_rate = get_weighted_item_rate(invoice_items, "meis_rate");
				}
				const item_with_igst_rate = (invoice.items || []).find(
					(item) => item.igst_rate !== null && item.igst_rate !== undefined
				);
				doc.igst_inr = flt(invoice.base_total)
					* flt(item_with_igst_rate && item_with_igst_rate.igst_rate) / 100;
				doc.igst_assessable_value_inr = flt(invoice.base_total);
			} else {
				doc.igst_inr = 0;
				doc.igst_assessable_value_inr = 0;
			}
			doc.duty_drawback_amount =
				(flt(doc.fob_value_inr) * flt(doc.duty_drawback_rate)) / 100;
			doc.rodtepe_amount =
				(flt(doc.fob_value_inr) * flt(doc.rodtepe_rate)) / 100;

			const dialog = new frappe.ui.Dialog({
				title: `Export Sales Invoice s: ${export_name}`,
				fields: get_export_sales_invoice_fields(),
				primary_action_label: "Save",
				async primary_action(values) {
					if (!values) {
						return;
					}

					const updated = { ...doc, ...values };
					const save_result = await frappe.call({
						method: "frappe.client.save",
						args: { doc: updated },
					});
					if (save_result.exc) {
						return;
					}

					frappe.show_alert({
						message: "Export Sales Invoice s updated",
						indicator: "green",
					});
					dialog.hide();
					await frm.reload_doc();
				},
			});

			const update_less_freight = async () => {
				await dialog.set_value("less_freight_insuranceusd",
					(flt(dialog.get_value("ocean_freight_usdfcl")) * flt(dialog.get_value("no_of_fcl")))
					+ flt(dialog.get_value("cif_insurance")));
				await update_export_duty();
			};
			const update_packing_charges = async () => {
				await dialog.set_value(
					"packing_charges",
					flt(dialog.get_value("packing_charges_usd_invoice"))
				);
				await update_export_duty();
			};
			const update_duty_drawback_amount = () => {
				return dialog.set_value(
					"duty_drawback_amount",
					(flt(dialog.get_value("fob_value_inr"))
						* flt(dialog.get_value("duty_drawback_rate"))) / 100
				);
			};
			const update_rodtepe_amount = () => {
				return dialog.set_value(
					"rodtepe_amount",
					(flt(dialog.get_value("fob_value_inr"))
						* flt(dialog.get_value("rodtepe_rate"))) / 100
				);
			};
			const update_fob_value_usd = async () => {
				const invoice_id = dialog.get_value("sales_invoice_id");
				const result = invoice_id
					? await frappe.db.get_value("Sales Invoice", invoice_id, ["total", "conversion_rate"])
					: null;
				const invoice_total = flt(result && result.message && result.message.total);
				const conversion_rate = flt(result && result.message && result.message.conversion_rate);
				const fob_value = invoice_total
					- flt(dialog.get_value("less_freight_insuranceusd"))
					- flt(dialog.get_value("packing_charges"))
					- flt(dialog.get_value("other_deduction_usd"));
				await dialog.set_value(
					"fob_value_usd",
					fob_value
				);
				await dialog.set_value("fob_value_inr", fob_value * conversion_rate);
				await update_amount_after_igst_duty();
			};
			const update_amount_after_igst_duty = () => {
				return dialog.set_value(
					"amount_after_igst_duty",
					flt(dialog.get_value("fob_value_usd"))
						+ flt(dialog.get_value("other_deduction_usd"))
						+ flt(dialog.get_value("packing_charges"))
						+ flt(dialog.get_value("less_freight_insuranceusd"))
				);
			};
			const update_export_duty = async () => {
				const invoice_id = dialog.get_value("sales_invoice_id");
				const result = invoice_id
					? await frappe.db.get_value("Sales Invoice", invoice_id, ["total", "conversion_rate"])
					: null;
				const invoice_total = flt(result && result.message && result.message.total);
				const conversion_rate = flt(result && result.message && result.message.conversion_rate);
				await dialog.set_value(
					"less_freight_insuranceinr",
					flt(dialog.get_value("less_freight_insuranceusd")) * conversion_rate
				);
				await dialog.set_value(
					"packing_charges_inr",
					flt(dialog.get_value("packing_charges")) * conversion_rate
				);
				const rate = flt(dialog.get_value("export_duty_rate_"));
				const denominator = 100 + rate;
				const duty = denominator
					? ((invoice_total
						- flt(dialog.get_value("less_freight_insuranceusd"))
						- flt(dialog.get_value("packing_charges"))) / denominator) * rate
					: 0;
				await dialog.set_value("export_duty_usd", duty);
				await dialog.set_value("export_duty_inr", duty * conversion_rate);
				await dialog.set_value("other_deduction_usd", duty);
				await dialog.set_value("other_deduction_inr", duty * conversion_rate);
				await update_fob_value_usd();
			};
			const update_other_deduction_inr = async () => {
				const invoice_id = dialog.get_value("sales_invoice_id");
				const result = invoice_id
					? await frappe.db.get_value("Sales Invoice", invoice_id, "conversion_rate")
					: null;
				const conversion_rate = flt(result && result.message && result.message.conversion_rate);
				await dialog.set_value(
					"other_deduction_inr",
					flt(dialog.get_value("other_deduction_usd")) * conversion_rate
				);
				await update_fob_value_usd();
			};
			const update_export_duty_inr = async () => {
				const invoice_id = dialog.get_value("sales_invoice_id");
				const result = invoice_id
					? await frappe.db.get_value("Sales Invoice", invoice_id, "conversion_rate")
					: null;
				const conversion_rate = flt(result && result.message && result.message.conversion_rate);
				await dialog.set_value(
					"export_duty_inr",
					flt(dialog.get_value("export_duty_usd")) * conversion_rate
				);
			};
			["ocean_freight_usdfcl", "no_of_fcl", "cif_insurance"].forEach((fieldname) => {
				dialog.fields_dict[fieldname].df.onchange = update_less_freight;
			});
			dialog.fields_dict.packing_charges_usd_invoice.df.onchange = update_packing_charges;
			dialog.fields_dict.export_duty_rate_.df.onchange = update_export_duty;
			dialog.fields_dict.packing_charges.df.onchange = update_export_duty;
			dialog.fields_dict.less_freight_insuranceusd.df.onchange = update_export_duty;
			dialog.fields_dict.export_duty_usd.df.onchange = update_export_duty_inr;
			dialog.fields_dict.other_deduction_usd.df.onchange = update_other_deduction_inr;
			dialog.fields_dict.fob_value_inr.df.onchange = () => {
				update_duty_drawback_amount();
				update_rodtepe_amount();
			};
			dialog.fields_dict.duty_drawback_rate.df.onchange = update_duty_drawback_amount;
			dialog.fields_dict.rodtepe_rate.df.onchange = update_rodtepe_amount;
			dialog.set_values(doc);
			await update_less_freight();
			await update_packing_charges();
			await update_export_duty();
			await update_other_deduction_inr();
			await update_duty_drawback_amount();
			await update_rodtepe_amount();
			set_dialog_read_only(dialog, ["sales_invoice_id"]);
			dialog.show();
		});
	});
}

function get_weighted_item_rate(items, rate_field) {
	const rows = (items || []).filter((item) => flt(item[rate_field]));
	const total_amount = rows.reduce((total, item) => total + flt(item.base_amount || item.amount), 0);
	if (!total_amount) {
		return 0;
	}
	return rows.reduce(
		(total, item) => total + flt(item.base_amount || item.amount) * flt(item[rate_field]),
		0
	) / total_amount;
}

function get_export_sales_invoice_fields() {
	const meta = frappe.get_meta("Export Sales Invoice s");
	if (!meta) {
		return [];
	}

	const fields = [];
	const fields_by_name = new Map((meta.fields || []).map((field) => [field.fieldname, field]));
	let field_order = meta.field_order;
	if (typeof field_order === "string") {
		try {
			field_order = JSON.parse(field_order);
		} catch (error) {
			field_order = null;
		}
	}
	if (!Array.isArray(field_order) || !field_order.length) {
		field_order = (meta.fields || []).map((field) => field.fieldname);
	}

	let skip_section = false;
	for (const fieldname of field_order) {
		// Exclude Comparative Statement and the cost breakdown that follows.
		if (["section_break_pbdp", "comparative_statement_section"].includes(fieldname)) {
			break;
		}
		const field = fields_by_name.get(fieldname);

		if (!field || !field.fieldtype) {
			continue;
		}
		if (field.fieldtype === "Section Break") {
			skip_section = field.fieldname === "section_break_ypoj";
		}
		if (skip_section) {
			continue;
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
	}

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
