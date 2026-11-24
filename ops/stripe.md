# Stripe (live account "Council Radar", acct_1UcGeeRLMaRmZSCy)

Set up 2026-11-24 with Huxley. All prices CAD, monthly, no Stripe Tax (Huxley: match Energy; revisit if registered for HST),
Managed Payments off on every link (it adds a 3.5% fee).

| Product | Product ID | Price | Payment link | Used on |
|---|---|---|---|---|
| Council Radar: Ontario Energy | prod_VdY5rD12wg7xvY | $59 founding (price_1UcGznRLMaRmZSCyRQE7BpLY) | https://buy.stripe.com/eVqaEZ3ZGbwjc1Qdm38Vi00 | index.html, sample.html, brief.html, start.js, energy trial lines |
| | | $249 team (price_1UcGznRLMaRmZSCyZauc9nHS) | https://buy.stripe.com/4gM8wRfIo9ob4zobdV8Vi01 | same |
| Council Radar: Ontario Housing | prod_Vgjik3VMtFI1Oy | $59 founding (price_1UfMF6RLMaRmZSCyk74R9N86) | https://buy.stripe.com/eVqeVfcwceIv5Ds4Px8Vi02 (+ `?client_reference_id=housing`) | housing.html, housing trial lines |
| | | $249 team | https://buy.stripe.com/4gM00l67O6bZ5DschZ8Vi03 (+ `?client_reference_id=housing`) | same |
| Council Radar: Enterprise pilot | prod_Vgjj64cuGFPyKl | $990/month (price_1UfMFaRLMaRmZSCygz0SMw83) | none: invoiced | ops/approvals.md, template E |

Billing portal (manage or cancel, any product): https://billing.stripe.com/p/login/eVqaEZ3ZGbwjc1Qdm38Vi00

## How agents use it
- **Which edition someone bought:** the product on their subscription (Energy vs Housing), or `client_reference_id=housing`.
- **Detecting subscribers:** Stripe receipt emails in Gmail today. Sessions that have the Stripe connector can list
  subscriptions by product instead (read-only; the connector has read scope only).
- **Enterprise pilot invoices:** the chief of staff prepares customer, product and terms; Huxley creates and sends each
  invoice in the Stripe dashboard (charging customers is reserved for him, `ops/approvals.md`).
- Never change, archive or deactivate existing products, prices or links.
