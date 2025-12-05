import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)

# [수정됨] Context-Aware Curator 프롬프트
SYSTEM_PROMPT = """
You are a 'Context-Aware Curator'. 
Your goal is to explain options specifically tailored to the user's CURRENT SITUATION (Context).

TASKS:
1. Analyze the user's [Context] first.
2. For each [Option], explain why it is good or bad *given that context*.
   - Example: If context is "Low Budget", for a "Taxi" option, the Con should strongly emphasize "High Cost".
3. Write persuasive 'Summary' and 'Buying Point' that resonate with the user's specific needs.

OUTPUT FORMAT (JSON ONLY):
{
  "options": [
    {
      "id": "opt1", 
      "original_text": "...",
      "title": "<String: Short Title in Korean>",
      "summary": "<String: Persuasive explanation fitting the context (Korean)>",
      "buying_point": "<String: The strongest reason to choose this IN THIS SITUATION>",
      "pros": ["<String: Context-relevant Pro>", "..."],
      "cons": ["<String: Context-relevant Con>", "..."]
    }
  ]
}

RULES:
- Language: KOREAN.
- Always prioritize the User's Context over general facts.
"""

def generate_explanations(options: list, context: str) -> dict:
    """
    선택지 목록 + 사용자 상황(Context)을 받아 맞춤형 설명을 생성합니다.
    """
    if not options:
        return {}

    options_block = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    # [수정됨] 프롬프트에 Context 주입
    user_prompt = f"""
    [User's Context / Situation]
    "{context}"

    [Options to Analyze]
    {options_block}
    
    Analyze these options to help the user decide in their current situation.
    """
    
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME, 
        system_instruction=SYSTEM_PROMPT
    )
    
    try:
        response = model.generate_content(
            user_prompt, 
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
                "max_output_tokens": 4096
            }
        )
        text = response.text.strip()
        
        if text.startswith("```"):
            text = re.sub(r"^```json\s*|^```\s*|```\s*$", "", text, flags=re.MULTILINE).strip()
            
        return json.loads(text)
    
    except Exception as e:
        print(f"[LLM Error] {e}")
        return {"options": []}