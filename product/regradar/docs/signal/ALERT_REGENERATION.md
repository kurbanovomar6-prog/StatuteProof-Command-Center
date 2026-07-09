# ALERT_REGENERATION — verification gate (signal-max)

## Case A — DFSA title flip 2026-07-05T12:54 (run 17d38737)

**BEFORE (what the old stack actually did, from the real trail):**
- change_status=CHANGED, risk_level=HIGH
- risk_reason: High risk: a strong regulatory risk indicator was detected alongside supporting compliance context (such as a deadline, penalty, or mandatory obligation). Compliance review is required.
- alert queued: data/alert_queue/…-17d38737-*.json (status PENDING_REVIEW)

**AFTER (full new stack):** UNCHANGED (hashes equal after v2 normalization — heartbeat, NO customer alert)

## Case B — DFSA title flip 2026-07-05T13:28 (run 4bc2127d)

**BEFORE (what the old stack actually did, from the real trail):**
- change_status=CHANGED, risk_level=HIGH
- risk_reason: High risk: a strong regulatory risk indicator was detected alongside supporting compliance context (such as a deadline, penalty, or mandatory obligation). Compliance review is required.
- alert queued: data/alert_queue/…-4bc2127d-*.json (status PENDING_REVIEW)

**AFTER (full new stack):** UNCHANGED (hashes equal after v2 normalization — heartbeat, NO customer alert)

## Case C1 — UAEFIU publications count 61→62 (2026-06-11T22:33)

The closest thing to a genuine change in the whole trail: the FIU
publications facet count incremented (a new publication). Honest
expectation: metadata-level, small delta.

**BEFORE:** change_status=CHANGED, risk_level=None (none recorded at run time)
**AFTER (full new stack):** LOW (rule LOW_NO_KEYWORDS)

Rendered Telegram body:
```
🚨 *StatuteProof alert — LOW*

*Severity:* LOW — severity basis not recorded for this run; review the excerpt and the source directly
*Source:* UAE Financial Intelligence Unit (UAEFIU) (AE)
*Checked:* 2026-06-11 22:33 UTC
*What changed (excerpt):*
+ نتج عن بحثك نتائج البحث ترتيب حسب الملاءمة الأحدث عنوان استعلامات البحث المقترحة وحدة 62 المنشورات 2 إعادة ضبط أهلا بكم في وحدة المعلومات المالية لدولة الإمارات العربية المتحدة نساعد على حماية الاقتصاد الإماراتي والعالمي من غسل الأمول وتمويل الإرهاب ومختلف الجرائم المالية. من نحن اخر تعديل للموقع في 09 فبراير 2024 مجالات تركيزنا المعلومات نوفّر معلومات استخباراتية قابلة للتنفيذ لتحقيق مهامنا وو…

🔗 https://www.uaefiu.gov.ae/
_Monitoring information only. Not legal advice._
```

## Case C2 — SYNTHETIC genuine regulatory change (SAMPLE / FAKE)

**SAMPLE / FAKE — the appended circular below is invented for the
verification gate; the base page is the real DFSA snapshot.** History
contains no unambiguous genuine regulatory change to replay (Phase-0
finding), so the positive path is proven on labeled synthetic content.

**AFTER (full new stack):** HIGH (rule HIGH_MULTIPLE_STRONG)

Rendered Telegram body (SAMPLE / FAKE):
```
🚨 *StatuteProof alert — HIGH*

*Severity:* HIGH — matched: penalty, sanctions; context: penalty (rule: multiple strong indicators)
*Source:* DFSA Financial Crime Prevention Notices and MLRO Letters (AE)
*Checked:* 2026-07-06 12:00 UTC
*What changed (excerpt):*
+ Financial Crime Prevention Notices and MLRO Letters | DFSA Overview of DFSA AML/CTF & Sanctions Obligations Standard-Setters / International Organisations Followed Financial Crime Prevention Notices and MLRO Letters Operational & Technology Risk Supervision DFSA Administered Law Climate and Environmental Risk Management Amendments to the DFSA AML and Glossary Modules and the AML FAQ document Op…
*Summary:* High risk: multiple strong regulatory indicators matched in the changed text: penalty, sanctions. Compliance review is required.
*Detected in this change:*
• Deadline: no later than 30 September 2026
• Effective date: Effective from 15 August 2026
• Instrument: Circular No. 12 of 2026
• Instrument: Federal Decree-Law No. (20) of 2018
• Amount: AED 250,000
*Deadline stated in source:* no later than 30 September 2026

🔗 https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters
_Monitoring information only. Not legal advice._
```

Rendered email/markdown body (SAMPLE / FAKE):
```
## StatuteProof alert — HIGH

**Severity:** HIGH — matched: penalty, sanctions; context: penalty (rule: multiple strong indicators)
**Source:** DFSA Financial Crime Prevention Notices and MLRO Letters (AE)
**Checked:** 2026-07-06 12:00 UTC

**What changed (excerpt):**
> + Financial Crime Prevention Notices and MLRO Letters | DFSA Overview of DFSA AML/CTF & Sanctions Obligations Standard-Setters / International Organisations Followed Financial Crime Prevention Notices and MLRO Letters Operational & Technology Risk Supervision DFSA Administered Law Climate and Environmental Risk Management Amendments to the DFSA AML and Glossary Modules and the AML FAQ document Op…

**Summary:** High risk: multiple strong regulatory indicators matched in the changed text: penalty, sanctions. Compliance review is required.

**Detected in this change:**
- Deadline: no later than 30 September 2026
- Effective date: Effective from 15 August 2026
- Instrument: Circular No. 12 of 2026
- Instrument: Federal Decree-Law No. (20) of 2018
- Amount: AED 250,000
**Deadline stated in source:** no later than 30 September 2026

Proof URL: https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters

_Monitoring information only. Not legal advice._
```
