
// Copyright (c) 2026, contact@sanpra.co.in and contributors
// For license information, please see license.txt

frappe.query_reports["Cashbook"] = {

    filters: [

        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },

        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },

        {
            fieldname: "account",
            label: __("Account"),
            fieldtype: "Link",
            options: "Account",

            get_query: function () {
                return {
                    filters: {
                        account_type: "Cash",
                        is_group: 0,
                        disabled: 0
                    }
                };
            }
        },

        {
            fieldname: "party_type",
            label: __("Party Type"),
            fieldtype: "Link",
            options: "DocType"
        },

        {
            fieldname: "party",
            label: __("Party"),
            fieldtype: "Dynamic Link",
            options: "party_type"
        },

        {
            fieldname: "cost_center",
            label: __("Cost Center"),
            fieldtype: "Link",
            options: "Cost Center"
        }

    ]

};
