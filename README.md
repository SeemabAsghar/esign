### Esignatures

Esignatures Integration

### Server Tests
![Server Tests](https://github.com/SeemabAsghar/esign/actions/workflows/ci.yml/badge.svg)
![Server Tests](https://github.com/SeemabAsghar/esign/actions/workflows/linter.yml/badge.svg)

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app esign https://github.com/SeemabAsghar/esign
bench --site your-site.com install-app esign
```

### License

[MIT](https://opensource.org/licenses/MIT)

# Getting Started
Follow these steps to quickly set up Esignatures in ERPNext:

## Create free account
→ https://esignatures.io/signup
## Get API Token
→ Dashboard → Automation & API → Copy "Your Secret token"
## ERPNext Setup
→ Go to eSignatures Settings

→ Paste API token (Password field)

→ Add placeholders like {{quotation_id}}, {{signer_name}}, etc. 
  (these should match the fields you mapped in ERPNext)

## Create Template on esignatures.io
→ Templates → New Template

→ Add placeholders like {{quotation_id}}, {{signer_name}}, etc. (match your mappings with erpnext fields)

## Set Webhook

→ esignatures.io Dashboard → Automation & API

→ "Your default website webhook" 

→ https://your-site.com/api/method/esign.api.esignature_webhook

⚠️ Note: Make sure to replace your-site.com with your actual ERPNext site URL.
