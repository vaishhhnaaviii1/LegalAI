import httpx #This is a library used to make network requests,perfect for FastAPI because it supports async
import logging
from app.core.config import settings
from app.schemas.precedent import ReferenceCase
from app.decorators import with_api_retry

logger = logging.getLogger(__name__)

class KanoonService:
    def __init__(self):
        # We are now using the OFFICIAL API endpoint
        self.url = "https://api.indiankanoon.org/search/"
        
        # Format the token exactly how Kanoon expects it
        api_key = settings.KANOON_API_TOKEN.replace('"', '').replace("'", "").strip()
        auth_header = f"Token {api_key}" if not api_key.startswith("Token ") else api_key
        
        #You are telling Kanoon, "When you reply, please only speak to me in JSON format
        self.headers = {
            "Authorization": auth_header,
            "Accept": "application/json"
        }
    @with_api_retry
    async def fetch_precedents(self, search_query: str, max_results: int = 3) -> list[ReferenceCase]:
        # Clean the query slightly (remove "Section" and quotes)
        clean_query = search_query.replace('"', '').replace('Section', '').strip()
        
        # This is what we were missing: Kanoon API expects a POST data payload!
        data_payload = {
            "formInput": clean_query,
            "pagenum": 0
        }
        
        print(f"\n🚀 Sending POST request to Kanoon API: {data_payload}")

        try:
            # Send the POST request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.url, headers=self.headers, data=data_payload)
            
            print(f"📊 LIVE API STATUS CODE RECEIVED: {response.status_code}\n")
            
            if response.status_code != 200:
                print(f"⚠️ Non-200 status code from Indian Kanoon: {response.text}")
                return []
                
            data = response.json()
            docs = data.get("docs", [])
            cases = []
            
            for doc in docs[:max_results]:
                # Extract and clean the data
                title = doc.get("title", "Unknown Case").replace("<b>", "").replace("</b>", "").strip()
                headline = doc.get("headline", "").replace("<b>", "").replace("</b>", "").strip()
                doc_id = str(doc.get("tid", ""))
                
                cases.append(ReferenceCase(
                    title=title,
                    doc_id=doc_id,
                    snippet=headline,
                    url=f"https://indiankanoon.org/doc/{doc_id}/" if doc_id else ""
                ))
                
            return cases

        except Exception as e:
            logger.error(f"❌ CRITICAL EXCEPTION DURING HTTP CALL: {e}", exc_info=True)
            return []
        




# 1. Prepares for the Trip (Setup): It defines the destination URL and formats your secret API token into a strict "VIP pass" header so the Kanoon server will accept the request.

# 2. Fills Out the Form (The Payload): It takes the legal search term, cleans it up, and packs it into a digital form. It uses a POST request (like a sealed FedEx box) to keep the search secure from server logs and bypass URL size limits.

# 3. Makes the Call (Execution): It uses the httpx library to securely send that form across the internet and waits for Kanoon to reply, doing so asynchronously so the rest of your app doesn't freeze.

# 4. Cleans the Mess (Data Parsing): Kanoon sends back raw, messy data filled with HTML formatting tags. Your code surgically extracts just the titles, snippets, and IDs, scrubbing the text perfectly clean.

# 5. Packages the Results (Return): It takes that clean data, shapes it perfectly into your ReferenceCase blueprint, and hands the neat package back to the rest of your app.

# 6. Employs a Safety Net (Error Handling): The entire mission is wrapped in a try/except block. If the internet drops or Kanoon's API crashes, your code catches the error, logs it silently, and returns an empty list so your main server stays alive.