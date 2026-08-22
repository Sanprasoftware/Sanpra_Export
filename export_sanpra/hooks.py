app_name = "export_sanpra"
app_title = "Export Sanpra"
app_publisher = "contact@sanpra.co.in"
app_description = "Create app for export"
app_email = "contact@sanpra.co.in"
app_license = "mit"

from export_sanpra.overrides.tax_withholding_entry import apply_tax_withholding_patches

apply_tax_withholding_patches()

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "export_sanpra",
# 		"logo": "/assets/export_sanpra/logo.png",
# 		"title": "Export Sanpra",
# 		"route": "/export_sanpra",
# 		"has_permission": "export_sanpra.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/export_sanpra/css/export_sanpra.css"
# app_include_js = "/assets/export_sanpra/js/export_sanpra.js"

# include js, css files in header of web template
# web_include_css = "/assets/export_sanpra/css/export_sanpra.css"
# web_include_js = "/assets/export_sanpra/js/export_sanpra.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "export_sanpra/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
	"Quotation": "public/js/quotation_export_quotation_s.js", 
	"Sales Order": "public/js/sales_order_export_sales_order_s.js",
	"Sales Invoice": "public/js/sales_invoice_export_sales_invoice_s.js",
	"Journal Entry": "public/js/journal_entry_blank_add_row.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "export_sanpra/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "export_sanpra.utils.jinja_methods",
# 	"filters": "export_sanpra.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "export_sanpra.install.before_install"
# after_install = "export_sanpra.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "export_sanpra.uninstall.before_uninstall"
# after_uninstall = "export_sanpra.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "export_sanpra.utils.before_app_install"
# after_app_install = "export_sanpra.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "export_sanpra.utils.before_app_uninstall"
# after_app_uninstall = "export_sanpra.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "export_sanpra.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Budget": "export_sanpra.overrides.budget.CustomBudget"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {  
    "Quotation": {
        "after_insert": "export_sanpra.public.py.quotation_export_quotation_s.create_export_quotation_s",
        "on_update": "export_sanpra.public.py.quotation_export_quotation_s.create_export_quotation_s",
        "on_cancel": "export_sanpra.public.py.quotation_export_quotation_s.set_export_quotation_status_cancelled",
        "on_trash": "export_sanpra.public.py.quotation_export_quotation_s.delete_export_quotation_s"
    },
    "Sales Order": { 
        "after_insert": "export_sanpra.public.py.export_sales_order_s.export_sales_order_s",
        "on_update": "export_sanpra.public.py.export_sales_order_s.export_sales_order_s",
        "on_cancel": "export_sanpra.public.py.export_sales_order_s.set_export_sales_order_status_cancelled",
        "on_trash": "export_sanpra.public.py.export_sales_order_s.delete_export_sales_order_s"
    },
    "Sales Invoice": {
        "after_insert": "export_sanpra.public.py.export_sales_invoice_s.export_sales_invoice_s",
        "on_update": "export_sanpra.public.py.export_sales_invoice_s.export_sales_invoice_s",
        "on_cancel": "export_sanpra.public.py.export_sales_invoice_s.set_export_sales_invoice_status_cancelled",
        "on_trash": "export_sanpra.public.py.export_sales_invoice_s.delete_export_sales_invoice_s"
    },
    "Purchase Invoice": {
        "before_save": "export_sanpra.public.py.purchase_invoice.validate_supplier_invoice_no"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"export_sanpra.tasks.all"
# 	],
# 	"daily": [
# 		"export_sanpra.tasks.daily"
# 	],
# 	"hourly": [
# 		"export_sanpra.tasks.hourly"
# 	],
# 	"weekly": [
# 		"export_sanpra.tasks.weekly"
# 	],
# 	"monthly": [
# 		"export_sanpra.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "export_sanpra.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "export_sanpra.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "export_sanpra.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["export_sanpra.utils.before_request"]
# after_request = ["export_sanpra.utils.after_request"]

# Job Events
# ----------
# before_job = ["export_sanpra.utils.before_job"]
# after_job = ["export_sanpra.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"export_sanpra.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
scheduler_events = {
    "daily": [
        "export_sanpra.export_sanpra.forex_tasks.update_maturity_indicators",
        "export_sanpra.export_sanpra.forex_notifications.send_maturity_notifications",
    ]
}
after_migrate = "export_sanpra.export_sanpra.forex_install.after_migrate"
