SIMILARITY_PROMPT = """
You are an expert Indian Legal Research Assistant.

Compare the following two legal cases.

Current Case:
{current_case}

--------------------------------------

Precedent Case:
{precedent_case}

Evaluate similarity considering:

- Facts
- Nature of offence
- Criminal intention
- Modus operandi
- Victim profile
- Relevant IPC/BNS provisions

Return ONLY one integer between 0 and 100.

Example:
83

Do not explain anything.
"""