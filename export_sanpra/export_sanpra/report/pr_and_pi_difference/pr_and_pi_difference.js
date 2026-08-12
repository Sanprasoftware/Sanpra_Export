// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.query_reports["PR and PI Difference"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "purchase_receipt",
			label: __("Purchase Receipt"),
			fieldtype: "Link",
			options: "Purchase Receipt",
		},
	],
	formatter: function(value, row, column, data, default_formatter) {
		const formatted_value = default_formatter(value, row, column, data);
		if (column.fieldname !== "difference" || !data || data.difference === null || data.difference === undefined) {
			return formatted_value;
		}

		if (data.difference < 0) {
			return `<span style="color: #d32f2f; font-weight: 600;">${formatted_value}</span>`;
		}

		if (data.difference > 0) {
			return `<span style="color: #2e7d32; font-weight: 600;">${formatted_value}</span>`;
		}

		return formatted_value;
	},
};
