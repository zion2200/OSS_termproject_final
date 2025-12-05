import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME

# 초기화
genai.configure(api_key=GEMINI_API_KEY)

# 의사결정 컨설턴트 프롬프트 (노트북 버전 개선)
SYSTEM_PROMPT = """
You are a wise 'Decision Consultant' AI. Your goal is to help a user compare multiple options and make the best choice.

TASKS:
1. Analyze each option provided by the user.
2. Provide a structured analysis in KOREAN.
3. Be objective but insightful. Highlight unique trade-offs.

OUTPUT FORMAT (JSON ONLY):
You must output a single valid JSON object. Do not include markdown formatting.
Structure:
{
  "options": [
    {
      "id": "opt1", 
      "original_text": "User input text",
      "title": "Short, catchy title in Korean",
      "summary": "2-3 sentences explaining what this is",
      "pros": ["Pro1", "Pro2", "Pro3"],
      "cons": ["Con1", "Con2"],
      "fit_for": "Type of person or mood this suits best",
      "rating": 5 (Integer 1-5 score)
    }
  ]
}

RULES:
- All values (title, summary, pros, cons, fit_for) MUST be in KOREAN.
- 'id' should be unique (opt1, opt2...).
"""

def generate_explanations(options: list) -> dict:
    """
    사용자의 선택지 목록(List[str])을 받아
    LLM이 분석한 구조화된 JSON 데이터를 반환합니다.
    """
    if not options:
        return {}

    # 프롬프트 구성
    options_block = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    user_prompt = f"Analyze these options based on the system instructions:\n\n{options_block}"
    
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME, 
        system_instruction=SYSTEM_PROMPT
    )
    
    try:
        response = model.generate_content(
            user_prompt, 
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.4,
                "max_output_tokens": 4096 # 잘림 방지
            }
        )
        text = response.text.strip()
        
        # 마크다운 방어 로직
        if text.startswith("```"):
            text = re.sub(r"^```json\s*|^```\s*|```\s*$", "", text, flags=re.MULTILINE).strip()
            
        return json.loads(text)
    
    except Exception as e:
        print(f"[LLM Error] {e}")
        # 에러 시 빈 구조 반환하여 프로그램 죽는 것 방지
        return {"options": []}