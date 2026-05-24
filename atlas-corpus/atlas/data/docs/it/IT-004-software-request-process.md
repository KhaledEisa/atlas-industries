# Atlas Industries — Software Request Process

**Document ID:** IT-SW-004
**Owner:** IT Service Desk
**Last Updated:** 5 February 2025
**Audience:** All employees

---

## 1. Overview

Atlas Industries uses a central ServiceDesk portal to manage software installation requests on company-issued devices. This process ensures licensing compliance, security review, and accurate tracking of installed software.

## 2. When to Use This Process

Use this process whenever you need:
- A new commercial software license (IDEs, design tools, project management apps)
- An additional seat on a tool you already have access to
- A specialized open-source tool that requires admin install rights
- An upgrade to a paid tier of an existing tool

You **do not** need to use this process for:
- Tools listed in the pre-approved catalog (see `servicedesk.atlas-industries.com/catalog`)
- Browser extensions from approved publishers
- Personal-use apps installed during onboarding

## 3. How to Submit a Request

1. Log in to `servicedesk.atlas-industries.com` using your Atlas SSO.
2. Click **New Request** → **Software**.
3. Fill the form:
   - Software name and vendor
   - Business justification (one or two paragraphs)
   - License type (per-seat, floating, free/open source)
   - Estimated cost (if known)
   - Project or cost center to charge
4. Submit. Your direct manager receives an approval email automatically.

## 4. Service Level

| Request Type | SLA |
|---|---|
| Already in catalog | Same business day |
| New software, < $500 | **3 to 5 business days** |
| New software, $500 – $5,000 | 5 to 10 business days (security review required) |
| New software, > $5,000 | 10 to 20 business days (procurement + legal review) |

The SLA clock starts only after **all approvals** are received (manager + finance owner + security if applicable).

## 5. Approval Chain

- **Direct manager** approves business justification.
- **Finance** approves the cost and budget code.
- **IT Security** reviews any software that handles customer data, processes payments, or runs outside the corporate network.

## 6. After Approval

- For pre-installed software, IT pushes the package to your device via the Software Center / Self Service.
- For SaaS tools, you receive an invitation email from the vendor — sign in with your Atlas SSO email.
- License keys are stored in IT's password vault, never emailed.

## 7. Escalation

If a request is stuck for more than **5 business days past SLA**, email `it-escalation@atlas-industries.com` with the ticket number. The IT Director reviews escalations weekly.

---

*Related: IT-AUP-006 (Acceptable Use Policy), FIN-PROC-003 (Procurement Guide).*
