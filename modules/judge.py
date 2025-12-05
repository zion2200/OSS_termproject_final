# modules/judge.py
import os
import json
import glob
import google.generativeai as genai
from config import GEMINI_API_KEY, SEED_DIR, BASE_DIR

genai.configure(api_key=GEMINI_API_KEY)

JUDGE_SYSTEM_PROMPT = """
You are a "Behavioral Judge Agent". 
Your job is to strictly follow the provided "Diagnostic Guideline" to evaluate user preferences.

RULES:
1. Do NOT use your own subjective opinion. Use the Interpretation Rules in the Guideline.
2. Analyze the user's behavior for EACH option provided.
3. Compare the options and select the one with the highest predicted preference.
4. Explain your reasoning based on the specific signals defined in the Guideline.

OUTPUT FORMAT (JSON):
{
  "analysis_per_option": {
    "Option A Title": "Reasoning based on guideline...",
    "Option B Title": "Reasoning based on guideline..."
  },
  "final_recommendation": "Title of the best option",
  "winning_reason": "Why this option won (referencing behavioral signals)"
}
"""

def load_guideline():
    path = os.path.join(BASE_DIR, "guideline.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def evaluate_session(session_id):
    # 1. 해당 세션의 모든 선택지 데이터 로드
    # 파일명 패턴: seed_{session_id}_{option_id}.json
    pattern = os.path.join(SEED_DIR, f"seed_{session_id}_*.json")
    files = glob.glob(pattern)
    
    if not files:
        print(f"[Judge] Session ID {session_id}에 해당하는 데이터가 없습니다.")
        return None
        
    session_data = []
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # LLM에게 줄 요약 데이터 구성
            summary = {
                "option_title": data['stimulus_content']['title'],
                "behavior_metrics": data['behavior_metrics'],
                "rule_based_interpretation": data['rule_based_interpretation']
            }
            session_data.append(summary)
            
    # 2. 가이드라인 로드
    guideline = load_guideline()
    if not guideline:
        print("[Judge] 가이드라인 파일이 없습니다. 먼저 guideline_maker를 실행하세요.")
        return None

    # 3. LLM 판결 요청
    prompt = f"""
    ### Reference Document
    [Diagnostic Guideline]
    {guideline}
    
    ### Task
    Compare the following {len(session_data)} options viewed by the user in Session {session_id}.
    Predict which option the user subconsciously preferred based on the Guideline.
    
    [Observed Options Data]
    {json.dumps(session_data, indent=2, ensure_ascii=False)}
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=JUDGE_SYSTEM_PROMPT)
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"[Judge Error] {e}")
        return None