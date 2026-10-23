// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("RODTEP Script", {
    setup(frm) {
        frm.set_query("sales_invoice", "rodtep_invoice_allocation", function() {
            return {
                query: "export_sanpra.export_sanpra.doctype.rodtep_script.rodtep_script.search_sales_invoices"
            };
        });
    }
});

frappe.ui.form.on("RODTEP Invoice Allocation Child", {
    sales_invoice(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.sales_invoice) {
            frappe.model.set_value(cdt, cdn, "invoice_rodtep_amount", 0);
            frappe.model.set_value(cdt, cdn, "shipping_bill_no", null);
            return;
        }

        const selected_invoice = row.sales_invoice;
        frappe.db.get_value("Sales Invoice", selected_invoice, "shipping_bill_number").then((result) => {
            if (locals[cdt][cdn].sales_invoice !== selected_invoice) return;
            frappe.model.set_value(
                cdt,
                cdn,
                "shipping_bill_no",
                result.message ? result.message.shipping_bill_number : null
            );
        });

        frappe.db.get_value(
            "Export Sales Invoice s",
            { sales_invoice_id: row.sales_invoice },
            "rodtepe_amount_copy"
        ).then((result) => {
            frappe.model.set_value(
                cdt,
                cdn,
                "invoice_rodtep_amount",
                result.message ? result.message.rodtepe_amount_copy : 0
            );
        });
    }
});
