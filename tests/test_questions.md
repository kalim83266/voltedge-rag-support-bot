# VoltEdge Electronics — Chatbot Test Questions

> All store data, contact details and policies are fictional, created for demo purposes.

Sections: **A** = answerable from one section, **B** = not in the documents (fallback), **C** = needs several sections or documents.

## A) Questions That CAN Be Answered

### A1. Return Window
**Question:** How long do customers normally have to request a return?

**Exact Correct Answer:** Eligible returns must normally be requested within 30 calendar days of the delivery date.

**Source:** Document 1, Section 1 — Standard Return Window.

---

### A2. Opened Laptop Return
**Question:** How long does a customer have to return an opened laptop?

**Exact Correct Answer:** An opened laptop must be returned within 14 calendar days of delivery.

**Source:** Document 1, Section 3 — Product-Specific Rules.

---

### A3. Smartphone Restocking Fee
**Question:** What restocking fee applies to an opened smartphone returned because the customer changed their mind about the model?

**Exact Correct Answer:** A 15% restocking fee applies, calculated from the item purchase price before tax and shipping charges.

**Source:** Document 1, Section 4 — Restocking Fee.

---

### A4. Refund Timing
**Question:** How quickly does VoltEdge process an approved refund after receiving a return?

**Exact Correct Answer:** Inspection is normally completed within 3 business days after the return arrives, and the approved refund is submitted within 2 business days after inspection. Most banks and card issuers then post the credit within 3–7 additional business days.

**Source:** Document 1, Section 7 — Refund Method and Timing.

---

### A5. Standard Shipping
**Question:** How much does Standard Shipping cost and how long does it normally take?

**Exact Correct Answer:** Standard Shipping costs $6.95 and normally arrives 3–5 business days after the order ships.

**Source:** Document 2, Section 3 — Shipping Options and Prices.

---

### A6. Free Shipping Threshold
**Question:** How much must a customer spend to receive free Standard Shipping?

**Exact Correct Answer:** The merchandise subtotal must be $75.00 or more after promotional discounts and before sales tax.

**Source:** Document 2, Section 4 — Free Shipping.

---

### A7. Same-Day Processing Cutoff
**Question:** What is the same-day processing cutoff time?

**Exact Correct Answer:** Orders placed before 2:00 p.m. Central Time on a business day normally enter processing the same day.

**Source:** Document 2, Section 2 — Order Processing Time.

---

### A8. Missing Delivered Package
**Question:** If tracking says "Delivered" but the customer cannot find the package, how long do they have to report it?

**Exact Correct Answer:** The customer must report the missing package within 5 calendar days of the delivery scan.

**Source:** Document 2, Section 7 — Lost Packages.

---

### A9. Saturday Support Hours
**Question:** What are VoltEdge Customer Support's Saturday hours?

**Exact Correct Answer:** Saturday from 10:00 a.m. to 4:00 p.m. Central Time.

**Source:** Document 3, Section 4 — Customer Support Hours.

---

### A10. Password Reset Link
**Question:** How long is a password-reset link valid?

**Exact Correct Answer:** The password-reset link expires after 30 minutes.

**Source:** Document 3, Section 3 — Account and Sign-In Help.

---

## B) Questions That CANNOT Be Answered

For B1 and B3–B7, the expected chatbot behavior is to clearly state that the information is not available in the provided VoltEdge Electronics documents and not invent an answer.

### B1. Warranty
**Question:** How long is the warranty on a VoltEdge laptop?

**Expected Behavior:** That information is not available in the provided VoltEdge Electronics documents.

---

### B2. International Shipping (partial answer)
**Question:** Does VoltEdge offer international shipping to Canada or other countries?

**Expected Behavior:** The documents only describe shipping to the 50 U.S. states and Washington, D.C. (Document 2, Section 1) and do not mention international shipping. The bot must NOT claim that international shipping is offered, and should say that no information about it is available in the documents. Mentioning the U.S.-only service area is correct and acceptable.

---

### B3. Gift Wrapping
**Question:** Can VoltEdge gift wrap an order?

**Expected Behavior:** That information is not available in the provided VoltEdge Electronics documents.

---

### B4. Price Matching
**Question:** Does VoltEdge offer price matching against another electronics retailer?

**Expected Behavior:** That information is not available in the provided VoltEdge Electronics documents.

---

### B5. Installment or Financing Plans
**Question:** Can customers pay using an installment or financing plan?

**Expected Behavior:** That information is not available in the provided VoltEdge Electronics documents.

---

### B6. Trade-In Program
**Question:** Can I trade in my old phone when buying a new one from VoltEdge?

**Expected Behavior:** That information is not available in the provided VoltEdge Electronics documents.

---

### B7. Student Discount
**Question:** Does VoltEdge offer a student discount?

**Expected Behavior:** That information is not available in the provided VoltEdge Electronics documents.

---

## C) Questions That Need Several Sections or Documents

### C1. Opened Laptop After 20 Days
**Question:** I opened my laptop 20 days ago. Can I still return it?

**Exact Correct Answer:** No. Once opened, a laptop must be returned within 14 calendar days of delivery, and requests after the applicable return window are not accepted. (An unopened laptop would still be eligible within 30 days.)

**Source:** Document 1, Section 1 and Section 3.

---

### C2. Unopened Headphones After 25 Days
**Question:** My unopened headphones arrived 25 days ago. Can I return them, and is there a restocking fee?

**Exact Correct Answer:** Yes, unopened headphones can be returned within 30 calendar days of delivery, and no restocking fee applies to eligible unopened items. A return authorization must be requested before sending the item back.

**Source:** Document 1, Section 3, Section 4 and Section 5.

---

### C3. Expedited Shipping on an $80 Order
**Question:** I ordered $80 of items with Expedited Shipping. Is my shipping free?

**Exact Correct Answer:** No. The $75.00 free-shipping threshold applies only to Standard Shipping. Expedited Shipping still costs $14.95 even if the order is over $75.00.

**Source:** Document 2, Section 3 and Section 4.

---

### C4. Opened Smartphone Returned for a Different Color
**Question:** If I return an opened smartphone because I want a different color, what happens to my refund?

**Exact Correct Answer:** A 15% restocking fee applies (calculated before tax and shipping), the customer is responsible for return shipping (a prepaid label's cost is deducted from the refund), and the original shipping charges are not refunded. The refund goes to the original payment method after inspection (about 3 business days), submission (within 2 business days) and the bank posting time (3–7 additional business days).

**Source:** Document 1, Section 4, Section 6 and Section 7.

---

### C5. Wrong Item Delivered
**Question:** I received the wrong item. What should I do and who pays for the return shipping?

**Exact Correct Answer:** Contact Customer Support within 5 calendar days of delivery with the order number and clear photos of the item and packaging. If VoltEdge shipped the wrong item, VoltEdge provides a prepaid return label at no charge.

**Source:** Document 2, Section 10 and Document 1, Section 6.
