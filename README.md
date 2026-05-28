# Amazon ↔ NAV Reconciliation & Posting Engine

This project automates a real business process: reconciling Amazon payments data with Microsoft Dynamics NAV and generating NAV‑compatible general journal lines. It replaces an Excel Power Query workflow originally used to match TXT exports from Amazon. For this Python version, the TXT files were pre‑processed and loaded into SQL Server.

Companion project for order import:  
https://github.com/hbanhx/etl_amazon_orders

**Volume: ~10,000 journal lines/month, ~98% automated.**

---

## Workflow

1. Import Amazon orders into NAV  
2. Import Amazon payments  
3. Reconcile Amazon AR and generate journal lines  

---

## ETL pipeline overview

- **Main** — orchestrates the pipeline and logs a summary  
- **Extract** — loads raw data from SQL Server using `config.yaml` (databases + queries)  
- **Transform** — reconciles transactions, applies business rules, and builds journal lines  
- **Load** — exports final outputs to Excel (raw + masked variants)

---

## Reconciliation logic

The engine matches Amazon settlement data against:

- **CLE** (Customer Ledger Entry)  
- **DCLE** (Detailed Customer Ledger Entry, `Entry Type = 1` = invoice amount)

Amazon amounts:

- **Invoice Amount (ex fees)** = product charges + promotional rebates + other  
- **Net Payout** = invoice amount + Amazon fees  

Core reconciliation rule:

> **Amazon Invoice Amount (ex fees) = DCLE Amount (Entry Type 1)**

Additional constraints:

- A **CLE must exist** for customer settlements.  
- The **open/closed state** of the CLE controls whether the payment is *applied* to the document or just posted to the customer account.

---

## Posting categories

1. **Valid customer settlement**  
   - Transaction type: `Order Payment` or `Refund`  
   - Matching CLE exists  
   - If the CLE is **open**: payment is applied via `Applies-to Doc. No.`  
   - If the CLE is **closed**: payment is posted to the customer but **not applied**  
   - Posting pattern: Customer → (optional Applies‑to Document) → Bank  

2. **Invalid customer settlement**  
   - Transaction type: `Order Payment` or `Refund`  
   - **No matching CLE** in NAV  
   - Posting: none — exported to a flagged/error report for manual handling  

3. **G/L posting (fees, VAT, other)**  
   - Transaction type is not a customer settlement (e.g. fees, commingling VAT, service fees)  
   - Posting pattern: G/L Account → Bank  

---

## Journal line automation

Each valid transaction is converted into a NAV‑compatible `GenJournalLine` using:

- Template/Batch: **PMTAM**  
- Auto‑generated `Document No.` based on date and line number  
- Correct `Document Type`, `Account Type`, `Account No.`, `Applies-to Doc. Type/No.`, and balancing account  
- Signed amount based on the posting rule (`Signed` in `PMT_SETUP`)  

The mapping is driven by a declarative setup (`Mappings.PMT_SETUP`) that defines, per posting type:

- Document Type  
- Account Type / Account No. (customer, G/L, bank)  
- Applies‑to Doc. Type / No.  
- Balancing Account Type / No.  
- Sign of the amount  

A helper (`get_value`) resolves:

- Enums → their NAV string values  
- Lambdas → row‑dependent values (e.g. customer no., document no.)  
- Plain constants → as‑is  

With an additional rule:

> `Applies-to Doc. No.` is only populated if the related invoice/credit memo is **open**; otherwise it is left blank so the payment is not applied automatically.

Invalid rows (e.g. missing CLE for a customer settlement) are exported separately for manual review.

---

## Output structure

**`output/`**

- Full reconciliation dataset (`data`)  
- `journal_import` — journal lines ready for NAV import  
- `journal_flagged` — journal lines for transactions that require manual attention  

**`output_masked/`**

- Masked reconciliation dataset (`data_masked`)  
- Masked `journal_import`  
- Masked `journal_flagged`  

Masking (e.g. customer numbers, document numbers, order IDs) is applied in Python using a configurable list of columns, not in SQL.

---

## Example run

A typical weekly settlement might produce a log summary like:

```text
ETL completed | imported=2481 | flagged=54


- imported = number of journal lines ready for NAV

- flagged = number of lines that need manual review (e.g. missing CLE)


- Reconciliation uses DCLE Entry Type 1 (invoice amount) as the basis for matching.

- Customer settlements require a matching CLE; otherwise they are flagged, not posted to G/L.

- The open/closed status of the CLE controls whether the payment is applied or just posted.

- Fees, VAT, and other non‑customer transactions post directly to G/L.

- Journal lines are generated automatically from a declarative posting setup and a small rule engine.
