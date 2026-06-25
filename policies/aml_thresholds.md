# AML Policy & Thresholds (sample — synthetic, for the RAG evidence step)

> Illustrative only. Not legal/compliance advice. Used so the agent grounds its
> reasoning in policy text rather than inventing thresholds.

## Reporting thresholds
- **Cash Transaction Report (CTR):** aggregate cash transactions exceeding **INR 10,00,000**
  in a month for a single account must be reviewed.
- **Suspicious Transaction Report (STR):** file when activity has no apparent lawful
  purpose or economic rationale, regardless of amount.

## Typologies to detect
- **Structuring / smurfing:** multiple deposits kept **just under INR 50,000** to avoid
  reporting, often across several accounts that funnel to one beneficiary within days.
- **Layering (circular transfers):** funds moved through a chain of accounts (A→B→C→A)
  to obscure origin, with little economic substance.
- **Shared-device / linked-identity rings:** multiple ostensibly unrelated accounts
  transacting from the **same device or IP** in a short window.

## Risk factors
- Customer is a **PEP** or in a high-risk occupation.
- Counterparty in a high-risk jurisdiction or flagged by sanctions screening.
- Velocity: many transactions in a short window inconsistent with KYC profile.

## Recommended dispositions
- **CLEAR** — benign, documented rationale.
- **ESCALATE** — warrants a case + analyst review; insufficient evidence to file.
- **FILE** — typology matched with sufficient evidence; draft STR narrative and route
  account-freeze + STR filing to the MLRO for approval.
