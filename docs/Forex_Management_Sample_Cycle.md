# Forex Management — Completed Sample Cycle

This document records one end-to-end training example created on site
`nutrichdev.erpkey.in` on 19 August 2026. Values are deliberately small and all
sample references start with `SAMPLE-`.

## Source documents

| Purpose | Document | Relevant value |
|---|---|---:|
| Foreign-currency exposure | Sales Order `E/SO/2526/78` | USD 66,750.00 |
| Invoice being realized | Sales Invoice `E/SI2627/7` | USD 46,911.90 outstanding |
| Customer | `CUST-00493` | Same on order and invoice |
| Bank | `Axis Bank` | Same on contract and settlement |

## Completed cycle

1. **Book the hedge — Forward Contract**
   - ERPNext document: `FC-2026-00001`
   - Contract reference: `SAMPLE-FX-CYCLE-2026-001`
   - Type: Export
   - Amount: USD 1,000.00
   - Booking date: 19 August 2026
   - Maturity date: 18 September 2026
   - Forward rate: INR 92.50/USD
   - Submit result: status `Open`, available USD 1,000.00.

2. **Utilize the hedge — Forward Contract Utilization**
   - ERPNext document: `FCU-2026-00001`
   - Link the contract, Sales Order, and Sales Invoice shown above.
   - Utilized amount: USD 1,000.00
   - Invoice/reference rate: INR 92.10/USD
   - Settlement/realization rate: INR 92.80/USD
   - Submit result: contract status `Fully Utilized`, utilized USD 1,000.00,
     available USD 0.00.
   - Recorded forex gain/loss: `1,000 × (92.80 − 92.10) = INR 700.00`.

3. **Settle the hedge — Forward Contract Settlement**
   - ERPNext document: `FCS-2026-00001`
   - Settlement amount: USD 1,000.00
   - Forward value: `1,000 × 92.50 = INR 92,500.00`
   - Actual value: `1,000 × 92.80 = INR 92,800.00`
   - Reference value: `1,000 × 92.10 = INR 92,100.00`
   - Forex gain/loss: `92,800 − 92,100 = INR 700.00`
   - Hedge gain/loss: `92,500 − 92,800 = INR -300.00`

4. **Close the contract**
   - Use **Close Contract** only after available amount reaches zero.
   - Final state: submitted (`docstatus = 1`), status `Closed`, available amount
     USD 0.00. Closing does not cancel the contract or its audit trail.

## Accounting and valuation branch

For `Nutrich Foods Pvt Ltd`, **Automatic Forward Settlement GL** and **Forward
MTM GL** were disabled when this sample was created, and the required forex/MTM
accounts were not configured. Therefore this cycle correctly creates no Journal
Entry and no submitted MTM valuation.

If accounting is required, first configure the Company forex gain, loss, bank
charge, MTM gain/loss, MTM balance, cost center, and linked contract Bank Account;
then enable the relevant switch. Submit an MTM valuation while the contract still
has an open amount (before full utilization). Settlement will create its Journal
Entry automatically only when its GL switch and accounts are configured.

## Controls verified from the implementation

- Contract amount and rate must be positive; maturity cannot precede booking.
- Company, customer, and currency must match the submitted Sales Order.
- Total submitted hedges cannot exceed the Sales Order unless overhedging is enabled.
- Utilization cannot exceed either contract availability or invoice outstanding.
- Settlement cannot exceed the utilized-but-unsettled contract amount.
- A contract cannot be closed while an available balance remains.
- Submitted utilization blocks cancellation of its parent contract.

## Where to verify

Open **Forex Management** and inspect Forward Contract, Forward Contract
Utilization, and Forward Contract Settlement. The Forward Contract Register,
Utilization Report, Gain/Loss Report, and Bank-wise Summary provide the reporting
views of the same records.
