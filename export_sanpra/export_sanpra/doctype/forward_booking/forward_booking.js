// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Forward Booking", {
    setup(frm) {
        frm.set_query("sales_order", "items", function() {
            return {
                query: "export_sanpra.export_sanpra.doctype.forward_booking.forward_booking.search_sales_orders",
                filters: {
                    docstatus: 1,
                    custom_sales_order_type: "Global",
                    // Python search_sales_orders also checks:
                    // total - ifnull(custom_forward_booking_amount, 0) != 0
                    // This calculated condition cannot be represented as a simple JS field filter.
                }
                
            };
        });
    }
});
