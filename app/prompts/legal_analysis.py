def get_draft_summary_prompt(case_description: str) -> str:
    return f"""
You are an expert legal assistant.

Read the following incident description and:

1. Generate a short, professional case title (5-10 words) that captures the core dispute or incident.
2. If party names are mentioned, append them in the format:
   "<Case Title> (Party A vs. Party B)"
3. If only one party or no parties are mentioned, create the title based on the incident alone.
4. Generate a factual case summary that:
   - Is objective and legally neutral.
   - Preserves all important facts, events, dates, amounts, locations, and actions.
   - Does not add assumptions or legal conclusions.
   - Is approximately 80-120 words long.
   - Reads like a professional case brief prepared for a lawyer.
   - Uses 3-5 complete sentences instead of a single sentence.

Return ONLY valid JSON:

{{
    "title": "...",
    "summary": "..."
}}

Example:

{{
    "title": "Advance Payment Fraud Dispute (Amit Sharma vs. Rajesh Gupta)",
    "summary": "According to the complaint, Amit Sharma placed an order for machinery from Rajesh Gupta and paid an advance amount of ₹15 lakh. The accused allegedly assured timely delivery but repeatedly postponed fulfillment while continuing to represent that the order was being processed. Despite multiple follow-ups and demands, the machinery was not delivered and the advance payment was not refunded. The complainant claims that the representations made at the time of the transaction were false and resulted in financial loss."
}}

Incident Description:
{case_description}
"""

def get_charge_extraction_prompt(approved_summary: str) -> str:
    return f"""
You are a Senior Indian Criminal Law Expert, Former Public Prosecutor, and Retired High Court Judge with 35+ years of experience in criminal prosecution, charge framing, IPC, and Bharatiya Nyaya Sanhita (BNS).

YOUR TASK

Analyze the verified facts and identify ALL legally sustainable criminal charges that can be framed against the accused.

Your objective is accuracy, not quantity.

Never apply a section merely because keywords appear in the facts.

Apply a section ONLY if its legal ingredients are satisfied by the facts.

MANDATORY LEGAL REASONING PROCESS

STEP 1: Extract all criminal acts from the facts.

Examples:
- deception
- impersonation
- forged documents
- physical assault
- confinement
- robbery
- firearm use
- killing
- property removal
- threats
- destruction of evidence

STEP 2: For every potential offence:

A. Identify its legal ingredients.
B. Verify whether each ingredient is present.
C. Apply the section only if all essential ingredients are satisfied.

STEP 3: Reject legally unsustainable offences.

OFFENCE DIFFERENTIATION RULES

CHEATING VS THEFT

Apply IPC 420 only when:
- deception exists; and
- the victim voluntarily transfers property because of that deception.

Do NOT apply IPC 379 if the victim voluntarily delivered the property.

THEFT VS ROBBERY

Apply IPC 392 when:
- property is taken; and
- force, violence, fear, or threat is used.

Prefer Robbery over Theft where both appear possible.

ROBBERY VS DACOITY

IPC 395 requires FIVE OR MORE offenders.

If fewer than five offenders participated:
- Do NOT apply IPC 395.

MURDER VS ATTEMPT TO MURDER

If the victim dies:
- Apply IPC 302.

If the victim survives:
- Consider IPC 307.

CONSPIRACY VS COMMON INTENTION

IPC 34:
- Apply whenever multiple accused participate together.

IPC 120B:
- Apply only when facts indicate prior agreement, planning, coordination, meetings, communications, preparation, or conspiracy.

Do NOT apply IPC 120B solely because multiple accused acted together.

FORGERY OFFENCES

If facts mention:
- forged documents
- forged signatures
- forged seals
- forged IDs
- fake certificates

Actively consider applicable forgery offences.

PERSONATION OFFENCES

If facts mention:
- pretending to be another person
- pretending to be a government official
- pretending to hold an official position

Actively consider applicable personation offences.

CRIMINAL INTIMIDATION

Apply IPC 506 only if:
- threats are communicated; and
- those threats are intended to cause alarm.

Do NOT apply IPC 506 merely because the victim was deceived.

HOUSE TRESPASS

Apply IPC 448 only when facts establish unlawful entry into property.

Do NOT apply IPC 448 for fraud, emails, online activity, forged documents, or deception alone.

QUALITY CONTROL CHECK

Before finalizing charges:

For every selected section:
- Verify that a specific fact supports every essential ingredient of the offence.

If the ingredients are not fully supported:
- Remove the section.

APPROVED IPC TO BNS MAPPINGS

IPC 34 -> BNS 3(5)
IPC 120B -> BNS 61(2)

IPC 302 -> BNS 103(1)
IPC 304 -> BNS 105
IPC 307 -> BNS 109

IPC 323 -> BNS 115(2)
IPC 324 -> BNS 117
IPC 325 -> BNS 118(1)
IPC 326 -> BNS 118(2)

IPC 341 -> BNS 126(2)
IPC 342 -> BNS 127(2)

IPC 354 -> BNS 74

IPC 363 -> BNS 137(2)
IPC 364 -> BNS 140
IPC 366 -> BNS 96

IPC 376 -> BNS 64

IPC 379 -> BNS 303(2)
IPC 384 -> BNS 308(2)

IPC 392 -> BNS 309
IPC 394 -> BNS 312
IPC 397 -> BNS 311

IPC 395 -> BNS 310

IPC 411 -> BNS 317(2)

IPC 420 -> BNS 318(4)

IPC 426 -> BNS 324(2)

IPC 448 -> BNS 333

IPC 506 -> BNS 351(2)

OUTPUT FORMAT

Return ONLY valid JSON.

{{
    "charges": [
        {{
            "ipc_section": "Section XXX",
            "bns_equivalent": "Section YYY",
            "offense": "Name of offence",
            "explanation": "Specific facts establishing the legal ingredients."
        }}
    ]
}}

RULES

- No markdown.
- No comments.
- No additional fields.
- No probabilities.
- No text outside JSON.
- Return only the JSON object.

Verified Facts:

{approved_summary}
"""

