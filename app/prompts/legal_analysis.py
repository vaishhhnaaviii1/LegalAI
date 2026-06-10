def get_draft_summary_prompt(case_description: str) -> str:
    return f"""
        You are an expert legal assistant. Read the following incident description.
        1. Create a short, professional title for the case along with the names of parties (party A vs. Party B )  involved if mentioned in the description.
        2. Write a clear, objective, one-sentence summary of the facts.
        
        Return ONLY valid JSON in this exact format:
        {{
            "title": "...(... vs. ...)",
            "summary": "..."
        }}
        
        Incident: {case_description}
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