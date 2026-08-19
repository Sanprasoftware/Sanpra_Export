import os
import frappe
from frappe.utils.file_manager import save_file

def attach_pdf(path, company="Nutrich Foods Pvt Ltd"):
    if not os.path.isfile(path):
        frappe.throw(f"Documentation file not found: {path}")
    with open(path,"rb") as handle:
        content=handle.read()
    existing=frappe.get_all(
        "File",
        filters={
            "attached_to_doctype":"Company",
            "attached_to_name":company,
            "file_url":["like","%/Forex_Management_User_Process_Guide%.pdf"],
        },
        pluck="name",
    )
    for name in existing:
        frappe.delete_doc("File",name,ignore_permissions=True)
    doc=save_file("Forex_Management_User_Process_Guide.pdf",content,"Company",company,is_private=1)
    frappe.db.commit()
    return {"file":doc.name,"file_url":doc.file_url,"company":company,"is_private":doc.is_private}
