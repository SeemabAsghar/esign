import frappe
import requests
import json
import hmac
import hashlib
from frappe.utils import nowdate
from frappe.core.doctype.communication.email import make

def get_esignature_token():
    settings = frappe.get_single("eSignatures Settings")
    api_token = settings.get_password("esignature_api_token",raise_exception=False)
    if not api_token:
        frappe.throw("E-signature API token not configured.")
    return api_token


@frappe.whitelist()
def get_esignature_templates():
    api_token = get_esignature_token()
    if not api_token:
        return []

    url = f"https://esignatures.com/api/templates?token={api_token}"
    response = requests.get(url)

    if response.status_code != 200:
        return []

    templates = response.json().get("data", [])
    return [{"label": t["title"], "value": t["template_id"]} for t in templates]


@frappe.whitelist()
def send_for_signature(quotation_id, signer_name, signer_email):
    api_token = get_esignature_token()

    quotation = frappe.get_doc("Quotation", quotation_id)
    customer_name = quotation.customer_name or signer_name
    customer_email = quotation.contact_email or signer_email
    company = quotation.company
    template_raw = quotation.custom_esignature_template
    template_id = quotation.custom_esignature_template

    if not template_id:
        frappe.throw("No e-signature template selected.")
        
    settings = frappe.get_single("eSignatures Settings") 
    mappings = settings.get("placeholder_mappings")
    
    placeholder_fields = []
    for row in mappings:
        # Frappe field se value lo (e.g., "name" → quotation.name)
        value = quotation.get(row.frappe_field)
        if value:
            placeholder_fields.append({
                "api_key": row.esignature_placeholder,
                "value": str(value)  # string mein convert
            })
    
    create_url = f"https://esignatures.com/api/contracts?token={api_token}"

    payload = {
        "template_id": template_id,
        "signers": [{
            "signature_request_delivery_methods": [],
            "name": customer_name,
            "email": customer_email
        }],
        "placeholder_fields": placeholder_fields 
        # "placeholder_fields": [
        #     {"api_key": "quotation_id", "value": quotation.name},
        #     {"api_key": "signer_name", "value": customer_name},
        #     {"api_key": "signer_email", "value": customer_email},
        #     {"api_key": "company", "value": company},
        #     ]
        }


    create_response = requests.post(create_url, json=payload)
    if create_response.status_code != 200:
        frappe.throw(f"Failed to create contract: {create_response.text}")

    response_data = create_response.json()
    contract = response_data["data"]["contract"]
    custom_contract_id = contract["id"]
    custom_signing_url = contract["signers"][0]["sign_page_url"]
    pdf_attachment = frappe.attach_print(
        doctype = "Quotation",
        name = quotation.name, 
        file_name=f"{quotation.name}.pdf",
        )
    
    company_name = frappe.get_value("Company", quotation.company, "company_name")

    frappe.sendmail(
        recipients=[customer_email],
        subject=f"Quotation {quotation.name} – Signature Request",
        message=f"""
            Dear {customer_name},<br><br>
            Please find your quotation attached.<br><br>
            To review and sign it, click the link below:<br>
            <a href="{custom_signing_url}">{custom_signing_url}</a><br><br>
            Best regards,<br>
            { company_name }
        """,
        attachments=[pdf_attachment]
    )

    quotation.db_set("custom_signature_sent", 1)
    quotation.db_set("custom_contract_id", custom_contract_id)
    quotation.db_set("custom_signing_url", custom_signing_url)

    return {
        "status": "Email sent with quotation and signing link.",
        "custom_signing_url": custom_signing_url
    }
    
@frappe.whitelist(allow_guest=True)
def esignature_webhook():
    api_token = get_esignature_token() 

    raw_data = frappe.request.data

    # Header se signature lia
    signature = frappe.request.headers.get("X-Signature-SHA256")
    if not signature:
        frappe.log_error("Missing X-Signature-SHA256 header", "Webhook Error")
        return {"error": "Missing signature"}

    # Compute HMAC
    computed_signature = hmac.new(
        api_token.encode('utf-8'),
        raw_data,
        hashlib.sha256
    ).hexdigest()

    # Secure compare
    if not hmac.compare_digest(computed_signature, signature):
        frappe.log_error("Invalid HMAC signature", "Webhook Security")
        return {"error": "Unauthorized: Invalid signature"}

    # payload parse 
    try:
        payload = frappe.request.get_json()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Webhook JSON Parse Error")
        return {"error": "Invalid JSON"}

    # Event check
    if payload.get("status") != "contract-signed":
        return {"status": "Ignored", "reason": "Not contract-signed event"}

    contract = payload.get("data", {}).get("contract", {})
    if not contract:
        return {"status": "Ignored", "reason": "No contract data"}

    contract_id = contract.get("id")
    pdf_url = contract.get("contract_pdf_url")
    
    frappe.log_error(f"Webhook received for contract: {contract_id}", "eSignature Webhook Success")
    
    if not pdf_url or not contract_id:
        return {"status": "Error", "reason": "Missing pdf_url or id"}

    # Timestamp find
    timestamp = nowdate()
    signers = contract.get("signers", [])
    if signers:
        for signer in signers:
            for event in signer.get("events", []):
                if event.get("event") == "sign_contract":
                    timestamp = event.get("timestamp", "")[:10]
                    break

    # Quotation find
    quotation_name = frappe.db.get_value("Quotation", {"custom_contract_id": contract_id})
    if not quotation_name:
        return {"status": "error", "reason": f"No Quotation found for contract ID {contract_id}"}

    # Update Quotation
    frappe.db.set_value("Quotation", quotation_name, {
        "custom_signed_pdf_url": pdf_url,
        "custom_signature_date": timestamp,
        "custom_document_signed": 1
    })

    message = f"The Quotation <b>{quotation_name}</b> has been signed."
    esign_users = frappe.get_all("Has Role", filters={"role": "e-signature"}, fields=["parent"])
    recipients = [u.parent for u in esign_users if frappe.get_value("User", u.parent, "enabled")]

    for user in recipients:
        notification = frappe.new_doc("Notification Log")
        notification.subject = f"Quotation {quotation_name} Signed"
        notification.email_content = message
        notification.for_user = user
        notification.type = "Alert"
        notification.document_type = "Quotation"
        notification.document_name = quotation_name
        notification.insert(ignore_permissions=True)

        make(
            subject=f"Quotation {quotation_name} Signed",
            content=message,
            recipients=[user],
            communication_type="Notification",
            send_email=True
        )

    return {"status": "success", "quotation": quotation_name}