    frappe.ui.form.on('Quotation', {
        refresh(frm) {
            frappe.call({
                method: "esign.api.get_esignature_templates",
                callback: function (r) {
                    if (r.message) {
                        frm.set_df_property("custom_esignature_template", "options", r.message);
                    }
                }
            });

            if (!frm.is_new() && frm.doc.docstatus === 0 && !frm.doc.custom_document_signed) {
                frm.add_custom_button("Send for Signature", () => {
                    frappe.call({
                        method: "esign.api.send_for_signature",
                        args: {
                            quotation_id: frm.doc.name,
                            signer_name: frm.doc.customer_name,
                            signer_email: frm.doc.contact_email,
                            template_id: frm.doc.template_id  
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.msgprint("E-signature request sent.");
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }

            if (frm.doc.custom_signed_pdf_url) {
                frm.add_custom_button("View Signed PDF", () => {
                    window.open(frm.doc.custom_signed_pdf_url, "_blank");
                }, __("View"));
            }

            if (frm.doc.custom_document_signed) {
                frm.dashboard.set_headline_alert('This document has been signed.', 'green');
            }
        }
    });
