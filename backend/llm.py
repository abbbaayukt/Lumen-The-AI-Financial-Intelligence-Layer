import json
import re
import google.generativeai as genai

class LLM:
    def __init__(self, api_key: str, model="gemini-2.5-flash", max_tokens=1000):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _call(self, prompt: str) -> str:
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=self.max_tokens,
            )
        )
        return response.text.strip()

    def _force_json(self, text: str) -> dict:
        text = text.replace("```json", "").replace("```", "")
        blocks = re.findall(r"\{[\s\S]*?\}", text)

        for block in blocks:
            try:
                return json.loads(block)
            except:
                continue
        return {}


    def extract_bill_info(self, bill_text: str) -> dict:
        prompt = (
            "Extract structured data from the bill text and return ONLY a compact JSON with EXACTLY these keys:\n"
            "{\n"
            "  \"item_name\": \"\",\n"
            "  \"amount\": 0,\n"
            "  \"category\": \"\",\n"
            "  \"payment_mode\": \"\",\n"
            "  \"transaction_date\": \"\",\n"
            "  \"vendor\": \"\",\n"
            "  \"description\": \"\",\n"
            "  \"tags\": \"\",\n"
            "  \"legitimacy\": \"\",\n"
            "  \"legitimacy_report\": \"\",\n"
            "  \"gst_number\": \"\"\n"
            "}\n\n"
            "STRICT RULES:\n"
            "- The JSON MUST be complete and MUST end with a closing brace '}'.\n"
            "- NEVER cut off fields or values. If space is low, reduce description, not structure.\n"
            "- category MUST be one of: [\"food\",\"groceries\",\"travel\",\"bills\",\"entertainment\",\"health\",\"education\",\"other\"]. If unclear use \"other\".\n"
            "- payment_mode MUST be one of: [\"cash\", \"card\", \"upi\", \"netbanking\", \"wallet\"]. If unclear use \"cash\".\n"
            "- legitimacy MUST be exactly \"verified\" or \"rejected\".\n"
            "- legitimacy_report MUST include a confidence percentage + short reason.\n"
            "- amount > 0 for payments, < 0 for refunds.\n"
            "- Missing fields default to \"\" or 0.\n"
            "- Output ONLY raw JSON.\n\n"
            f"BILL TEXT:\n{bill_text}"
        )

        raw = self._call(prompt)
        print(raw)
        parsed = self._force_json(raw)

        def get(k, default=""):
            return parsed[k] if k in parsed and parsed[k] not in [None, "null"] else default

        # legitimacy
        legitimacy = get("legitimacy").lower()
        if legitimacy not in ["verified", "rejected"]:
            legitimacy = "verified"

        # categories
        allowed_categories = {
            "food", "groceries", "travel", "bills",
            "entertainment", "health", "education", "other"
        }
        category = get("category").lower()
        if category not in allowed_categories:
            category = "other"

        # payment modes
        allowed_payment_modes = {
            "cash", "card", "upi", "netbanking", "wallet"
        }
        payment_mode = get("payment_mode").lower().strip()
        if payment_mode not in allowed_payment_modes:
            payment_mode = "cash"

        return {
            "item_name": get("item_name"),
            "amount": float(get("amount", 0)),
            "category": category,
            "payment_mode": payment_mode,
            "transaction_date": get("transaction_date"),
            "vendor": get("vendor"),
            "description": get("description"),
            "tags": get("tags"),
            "legitimacy": legitimacy,
            "legitimacy_report": get("legitimacy_report"),
            "gst_number": get("gst_number"),
        }
