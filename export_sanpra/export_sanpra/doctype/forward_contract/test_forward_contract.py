import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

class TestForwardContract(IntegrationTestCase):
    def test_positive_amount_and_rate(self):
        doc=frappe.new_doc("Forward Contract"); doc.contract_amount=0; doc.forward_rate=1
        with self.assertRaises(frappe.ValidationError): doc.run_method("validate")
        doc.contract_amount=1; doc.forward_rate=0
        with self.assertRaises(frappe.ValidationError): doc.run_method("validate")

    def test_maturity_before_booking_is_rejected(self):
        doc=frappe.new_doc("Forward Contract"); doc.contract_amount=1; doc.forward_rate=1; doc.booking_date=today(); doc.maturity_date=add_days(today(),-1)
        with self.assertRaises(frappe.ValidationError): doc.run_method("validate")
