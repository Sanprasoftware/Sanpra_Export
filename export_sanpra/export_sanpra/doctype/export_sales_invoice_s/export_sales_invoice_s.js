// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Export Sales Invoice s", {
	refresh(frm) {
		if (frm.doc.sales_invoice_id) {
			update_invoice_derived_amounts(frm);
		}
	},
	ocean_freight_usdfcl: update_less_freight_insurance,
	no_of_fcl: update_less_freight_insurance,
	cif_insurance: update_less_freight_insurance,
	sales_invoice_id: update_invoice_derived_amounts,
	less_freight_insuranceusd: update_export_duty_usd,
	packing_charges: update_export_duty_usd,
	export_duty_rate_: update_export_duty_usd,
	other_deduction_usd: update_other_deduction_inr,
	fob_value_usd: update_amount_after_igst_duty,
	igst_inr: update_amount_after_igst_duty,
	fob_invoice_value_inr: update_derived_export_amounts,
	duty_drawback_rate: update_duty_drawback_amount,
	rodtepe_rate: update_rodtepe_amount,
	packing_charges_usd_invoice(frm) {
		return frm.set_value("packing_charges", flt(frm.doc.packing_charges_usd_invoice));
	},
});

function update_less_freight_insurance(frm) {
	return frm.set_value("less_freight_insuranceusd",
		(flt(frm.doc.ocean_freight_usdfcl) * flt(frm.doc.no_of_fcl)) + flt(frm.doc.cif_insurance));
}

function update_duty_drawback_amount(frm) {
	return frm.set_value(
		"duty_drawback_amount",
		flt(frm.doc.fob_value_inr) * flt(frm.doc.duty_drawback_rate) / 100
	);
}

function update_rodtepe_amount(frm) {
	return frm.set_value(
		"rodtepe_amount",
		(flt(frm.doc.fob_value_inr) * flt(frm.doc.rodtepe_rate)) / 100
	);
}

function update_derived_export_amounts(frm) {
	update_duty_drawback_amount(frm);
	update_rodtepe_amount(frm);
}

async function update_fob_value_usd(frm) {
	if (!frm.doc.sales_invoice_id) {
		await frm.set_value("fob_value_usd", 0);
		await frm.set_value("fob_value_inr", 0);
		return update_amount_after_igst_duty(frm);
	}

	const result = await frappe.db.get_value(
		"Sales Invoice",
		frm.doc.sales_invoice_id,
		["total", "conversion_rate"]
	);
	const invoice_total = flt(result && result.message && result.message.total);
	const conversion_rate = flt(result && result.message && result.message.conversion_rate);
	await frm.set_value(
		"fob_value_usd",
		invoice_total - flt(frm.doc.less_freight_insuranceusd) - flt(frm.doc.packing_charges) - flt(frm.doc.other_deduction_usd)
	);
	await frm.set_value("fob_value_inr", flt(frm.doc.fob_value_usd) * conversion_rate);
	return update_amount_after_igst_duty(frm);
}

async function update_amount_after_igst_duty(frm) {
	let invoice_base_total = 0;
	if (frm.doc.sales_invoice_id) {
		const result = await frappe.db.get_value(
			"Sales Invoice",
			frm.doc.sales_invoice_id,
			"base_total"
		);
		invoice_base_total = flt(result && result.message && result.message.base_total);
	}
	return frm.set_value("amount_after_igst_duty", flt(frm.doc.igst_inr) + invoice_base_total);
}

async function update_other_deduction_inr(frm) {
	let conversion_rate = 0;
	if (frm.doc.sales_invoice_id) {
		const result = await frappe.db.get_value(
			"Sales Invoice",
			frm.doc.sales_invoice_id,
			"conversion_rate"
		);
		conversion_rate = flt(result && result.message && result.message.conversion_rate);
	}
	await frm.set_value("other_deduction_inr", flt(frm.doc.other_deduction_usd) * conversion_rate);
	return update_fob_value_usd(frm);
}

async function update_export_duty_usd(frm) {
	const rate = flt(frm.doc.export_duty_rate_);
	let invoice_total = 0;
	let conversion_rate = 0;
	if (frm.doc.sales_invoice_id) {
		const result = await frappe.db.get_value(
			"Sales Invoice",
			frm.doc.sales_invoice_id,
			["total", "conversion_rate"]
		);
		invoice_total = flt(result && result.message && result.message.total);
		conversion_rate = flt(result && result.message && result.message.conversion_rate);
	}
	await frm.set_value("less_freight_insuranceinr", flt(frm.doc.less_freight_insuranceusd) * conversion_rate);
	await frm.set_value("packing_charges_inr", flt(frm.doc.packing_charges) * conversion_rate);

	const denominator = 100 + rate;
	const duty = denominator
		? ((invoice_total - flt(frm.doc.less_freight_insuranceusd) - flt(frm.doc.packing_charges))
			/ denominator) * rate
		: 0;
	await frm.set_value("export_duty_usd", duty);
	await frm.set_value("export_duty_inr", duty * conversion_rate);
	await frm.set_value("other_deduction_usd", duty);
	await frm.set_value("other_deduction_inr", duty * conversion_rate);
	return update_fob_value_usd(frm);
}

async function update_invoice_derived_amounts(frm) {
	await update_export_duty_usd(frm);
	await update_igst_inr(frm);
	return update_igst_assessable_value_inr(frm);
}

async function update_igst_inr(frm) {
	if (!frm.doc.sales_invoice_id) {
		return frm.set_value("igst_inr", 0);
	}
	const result = await frappe.call({
		method: "export_sanpra.export_sanpra.doctype.export_sales_invoice_s.export_sales_invoice_s.get_igst_inr",
		args: { sales_invoice_id: frm.doc.sales_invoice_id },
	});
	return frm.set_value("igst_inr", flt(result.message));
}

async function update_igst_assessable_value_inr(frm) {
	if (!frm.doc.sales_invoice_id) {
		return frm.set_value("igst_assessable_value_inr", 0);
	}
	const result = await frappe.db.get_value(
		"Sales Invoice",
		frm.doc.sales_invoice_id,
		"base_total"
	);
	return frm.set_value(
		"igst_assessable_value_inr",
		flt(result && result.message && result.message.base_total)
	);
}
