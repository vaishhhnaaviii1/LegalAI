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
        You are an expert Indian criminal lawyer. Based on the verified facts below, 
        identify the applicable Indian Penal Code (IPC) and Bharatiya Nyaya Sanhita (BNS) sections.
        
        Return ONLY valid JSON in this exact format, with a list of "charges":
        {{
            "charges": [
                {{
                    "ipc_section": "Section 378",
                    "bns_equivalent": "Section 303(2)",
                    "offense": "Theft",
                    "explanation": "Brief reason..."
                }}
            ]
        }}
        
        Verified Facts: {approved_summary}
        """
