import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME

# 초기화
genai.configure(api_key=GEMINI_API_KEY)

# [수정됨] 매력 발굴 및 설득 중심의 프롬프트
SYSTEM_PROMPT = """
You are a 'Charismatic Curator' who helps people realize the hidden value of their choices.
Your goal is not just to explain options, but to HIGHLIGHT clearly why a user should choose each one.

TASKS:
1. Identify the core "Value Proposition" (Why is this special?) of each option.
2. Write a persuasive description in KOREAN that appeals to emotions and practical benefits.
3. Make the user feel, "Wow, I really need this."

OUTPUT FORMAT (JSON ONLY):
Structure:
{
  "options": [
    {
      "id": "opt1", 
      "original_text": "...",
      "title": "<String: Short, Attractive Title in Korean>",
      "summary": "<String: A persuasive pitch (3-4 sentences). Explain the specific benefits and why this is a great choice. Don't just list facts.>",
      "buying_point": "<String: One punchline sentence summarizing the biggest reason to pick this.>",
      "pros": ["<String: Benefit 1>", "<String: Benefit 2>"],
      "cons": ["<String: Trade-off 1>", "<String: Trade-off 2>"]
    }
  ]
}

RULES:
- Language: KOREAN.
- Tone: Engaging, Insightful, and Persuasive (but not scammy).
- Focus on "Benefits" (what they get), not just "Features" (what it is).
"""

def generate_explanations(options: list) -> dict:
    """
    선택지 목록을 받아 설득력 있는 설명(JSON)을 반환합니다.
    """
    if not options:
        return {}

    # 프롬프트 구성
    options_block = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    user_prompt = f"""
    Please analyze the following options and create a persuasive guide for the user.
    Focus on WHY they should choose each one.
    
    [Options]
    {options_block}
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
                "temperature": 0.7, # 창의성 약간 높임 (더 맛깔난 표현 위해)
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