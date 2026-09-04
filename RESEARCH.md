# Research Sources & Regulatory Citations

This document compiles the external market research, statutory acts, central bank directions, and payment network frameworks that shaped the design and architecture of ReClaim.

Every source listed below was used to validate a specific design decision, ground a mathematical formula, or define an operational stopping rule.

---

## 1. Strategic Thesis & Market Sizing

*   **Razorpay AI-Native Agent Studio at FTX'26:**  
    [Razorpay Newsroom: Official Launch Announcement](https://razorpay.com/newsroom/)  
    *Insight:* Razorpay announced native agents for cart conversion, dispute response, and cashflow forecasting on March 12, 2026. This led us to design ReClaim not as a naive dunning clone, but as a cross-rail statutory compliance and multi-module recovery intelligence layer that operates on top of Razorpay's infrastructure.
*   **NPCI Unified Agent Protocol (UAP):**  
    [Business Standard: India may allow agentic AI-led UPI transactions under new NPCI protocol](https://www.business-standard.com/finance/news/india-may-allow-agentic-ai-led-upi-transactions-under-new-npci-protocol-126070801343_1.html)  
    *Insight:* Reported NPCI's regulatory framework enabling autonomous AI agents to execute trusted transactions across UPI rails, establishing the "why now" for autonomous financial workflows in India.
*   **Recordent Indian SME Receivables Report 2026:**  
    [Telangana Today: Indian MSMEs face mounting delayed payments](https://telanganatoday.com/indian-msmes-face-mounting-delayed-payments-recordent-report-reveals)  
    *Insight:* Sourced the macro problem metrics: ₹8.1 lakh crore locked in overdue MSME receivables, ₹3.83 crore average overdue per SME (360+ days), and a 73-day average payment cycle. Critically, 82.6% of invoices are issued with short terms (0 to 30 days), proving the crisis stems from collection bottlenecks rather than loose credit terms.
*   **E-Commerce RTO Market Analysis:**  
    [TrackVid: Why Indian Sellers Lose Rs 8,000 Crore to RTO](https://trackvid.in/blogs/rto-in-ecommerce-india.html)
    *Insight:* Researched Return to Origin (RTO) as an alternate hackathon track, but deprioritized it after verifying that RTO is already heavily served by specialized logistics vendors (GoKwik, Shipmozo, HillTeck). In contrast, B2B compliance-driven recovery was severely underserved and offered substantially higher recovery value per case.

---

## 2. Statutory Legal Grounding & Central Bank Regulations

*   **MSMED Act 2006 (Act No. 27 of 2006):**  
    [Ministry of MSME Official PDF: Full Act Text](https://www.msmediagra.gov.in/writereaddata/msmedact.pdf)  
    *Insight:* Provided the non-negotiable statutory foundation for Module B:
    *   **Section 15:** Caps credit terms at 45 days (if written agreement exists) or 15 days (default / day of acceptance).
    *   **Section 16:** Mandates monthly compounding penal interest at three times the RBI Bank Rate for every day overdue.
    *   **Section 18:** Governs formal dispute filing before the Micro and Small Enterprises Facilitation Council (MSEFC).
*   **MSME Samadhaan Official Tribunal Portal:**  
    [Ministry of MSME: Delayed Payment Monitoring System](https://samadhaan.msme.gov.in/)  
    *Insight:* The official quasi-judicial arbitration portal targeted in Rung 4, where legal filing packets are drafted by the system and held at Rule 10 for human sign-off.
*   **MSMED Section 16 Compound Interest Mechanics:**  
    [Lexology: Delayed Payments to MSEs under the MSME Act, 2006](https://www.lexology.com/library/detail.aspx?g=dc0c35e8-d98e-4e84-a05f-fa7a5213c3bd) | [Udyamita Helpline: Statutory Interest Computation](https://www.udyamitahelpline.com/)  
    *Insight:* Validated the exact legal formula: monthly compounding with monthly rests at 3x the RBI Bank Rate, implemented in `domain_logic/msmed.py`.
*   **Reserve Bank of India (RBI) Bank Rate Policy Benchmark:**  
    [IndiaBonds: August 2026 RBI Monetary Policy Highlights](https://www.indiabonds.com/bonduni/news/august-2026-rbi-monetary-policy-highlights/) | [Reserve Bank of India Official Portal](https://www.rbi.org.in/)  
    *Insight:* Grounded the Bank Rate at 5.50% p.a. (established at the August 2026 Monetary Policy Committee meeting), yielding the effective penal rate of 16.50% p.a. ($3 \times 5.50\%$).
*   **RBI Master Directions on Prepaid Payment Instruments (PPIs):**  
    [Argus Partners: RBI Issues Master Directions on Prepaid Payment Instruments](https://www.argus-p.com/updates/updates/rbi-issues-master-directions-on-prepaid-payment-instruments/) | [Reserve Bank of India Official Portal](https://www.rbi.org.in/)  
    *Insight:* Defined the 12-month Min-KYC limit and regulatory requirements governing the `wallet_kyc_lapsed` root cause in Module A.

---

## 3. Payment Rails & Operational Constraints

*   **NPCI AutoPay Execution Windows:**  
    [Republic World: Why Morning EMIs and SIPs Fail in 2026](https://www.republicworld.com/business/upi-autopay-failure-morning-peak-hours-npci-new-rules-2026) | [PwC India: UPI AutoPay Guidelines](https://www.pwc.in/)  
    *Insight:* Sourced the morning peak banking switch throttle (10:00 to 13:00 IST), which accounts for high recurring UPI drop rates. Directly informed Stopping Rule 2, which blocks retries during this window and reschedules them to 13:00:01 IST.
*   **NPCI UPI AutoPay Retry Caps & Non-Peak Boundaries:**  
    [Razorpay Blog: Master Recurring Payments with UPI 2.0](https://razorpay.com/blog/upi-autopay/) | [Yuno Payment Docs: UPI AutoPay Specifications](https://www.yuno.company/)  
    *Insight:* Confirmed the regulatory cap of 1 original attempt plus a maximum of 3 retries, as well as permitted off-peak windows (before 10:00, 13:00 to 17:00, and after 21:30 IST).
*   **Razorpay Platform Fee vs. MDR Nuances:**  
    [Razorpay Official Pricing](https://razorpay.com/pricing/) 
    *Insight:* Verified that Razorpay charges a 2.00% platform fee on UPI (despite 0% statutory MDR) plus 18% GST on the fee, resulting in a 2.36% net deduction. Also confirmed the 2.15% rate on RuPay credit on UPI and 3% on Cardless EMI.
*   **Halted Subscription Lifecycle:**  
    [Razorpay Subscriptions Documentation](https://razorpay.com/docs/payments/subscriptions/)  
    *Insight:* Confirmed that when a subscription reaches `halted` status, Razorpay stops automatic retries entirely. Recovery must be executed by issuing a fresh Payment Link for the unpaid invoice.

---

## 4. Empirical Benchmarks & Market Trajectory

*   **Dunning Recovery Industry Benchmarks:**  
    [Baremetrics: Subscription Payment Recovery Benchmarks](https://baremetrics.com/blog/subscription-payment-recovery-benchmarks) | [Digital Applied: The Dunning Playbook](https://www.digitalapplied.com/)  
    *Insight:* Established that the industry median recovery rate for recurring dunning is 47.6%.