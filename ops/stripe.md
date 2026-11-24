# Stripe setup (2026-11-24)

## Today
| Product | Link | Used for |
|---|---|---|
| Founding, $59/month | https://buy.stripe.com/eVqaEZ3ZGbwjc1Qdm38Vi00 | Energy; housing with `?client_reference_id=housing` |
| Team (5 people), $249/month | https://buy.stripe.com/4gM8wRfIo9ob4zobdV8Vi01 | Energy; housing with `?client_reference_id=housing` |
| Billing portal | https://billing.stripe.com/p/login/eVqaEZ3ZGbwjc1Qdm38Vi00 | Manage or cancel, in every footer |

Subscribers are detected from Stripe receipt emails in Gmail (weekly issue task, chief of staff).

## Next, once the Stripe connector is connected in claude.ai (Huxley, one sign-in)
1. **Dedicated housing products** so checkout and receipts say "Housing": "Council Radar Housing, founding" ($59/month CAD)
   and "Council Radar Housing, team" ($249/month CAD), each with a payment link. Then swap the two URLs in
   `samples/build_housing_html.py`, `ops/weekly_task.md` and `radar/deliver.py`, rebuild site/housing.html, run tests.
2. **Enterprise pilot product**: "Council Radar Enterprise pilot", $990/month CAD, billed by invoice (no payment link).
   Invoices are drafted for a customer when a firm accepts; Huxley sends each one.
3. **Read subscriptions from Stripe directly** (customers, active subscriptions, metadata `client_reference_id`), instead of
   parsing receipt emails, in the weekly issue and chief-of-staff runs.
4. Keep all existing links and prices working; never change or archive the energy links.
