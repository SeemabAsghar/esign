### Esignatures

Esignatures Integration

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app esign
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/esign
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

### Setup Guide

# Create free account
→ https://esignatures.io/signup
# Get API Token
→ Dashboard → Automation & API → Copy "Your Secret token"
# ERPNext Setup
→ Go to eSignatures Settings
→ Paste API token (Password field)
→ Add Placeholder Mappings (e.g., name → quotation_id, grand_total → total_amount)
# Create Template on esignatures.io
→ Templates → New Template
→ Add placeholders like {{quotation_id}}, {{signer_name}}, etc. (match your mappings)
→ Add signature field
# Set Webhook
→ esignatures.io Dashboard → Automation & API
→ "Your default website webhook" 
→ https://your-site.com/api/method/esign.api.esignature_webhook
