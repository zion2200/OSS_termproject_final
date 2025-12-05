import os
import json
import glob
import google.generativeai as genai
from config import GEMINI_API_KEY, SEED_DIR, BASE_DIR

genai.configure(api_key=GEMINI_API_KEY)

# [수정됨] 한국어 출력을 강제하는 시스템 프롬프트
JUDGE_SYSTEM_PROMPT = """
당신은 "행동 분석 심판관(Behavioral Judge Agent)"입니다. 
제공된 "진단 가이드라인(Diagnostic Guideline)"을 엄격히 준수하여 사용자의 무의식적 선호도를 평가하는 것이 임무입니다.

[규칙]
1. 당신의 주관적인 의견을 배제하고, 오직 가이드라인에 정의된 해석 규칙(Interpretation Rules)만 따르십시오.
2. 각 선택지(Option)별로 관찰된 행동 데이터를 분석하여 근거를 제시하십시오.
3. 가이드라인에 근거하여 가장 높은 선호도(Preference Score)가 예측되는 선택지를 추천하십시오.
4. **결과 출력(JSON 값)의 모든 언어는 반드시 '한국어'여야 합니다.** (전문적인 어조 사용)

[출력 형식 (JSON)]
{
  "analysis_per_option": {
    "선택지 제목 1": "가이드라인의 Step X에 따르면, 사용자의 ~~한 행동은 ~~한 신호로 해석된다. 따라서...",
    "선택지 제목 2": "..."
  },
  "final_recommendation": "최종 추천 선택지 제목",
  "winning_reason": "이 선택지가 선정된 결정적 이유 (다른 선택지 대비 긍정 신호의 우위 등 요약)"
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
        print("[Judge] 가이드라인 파일(guideline.md)이 없습니다. stage2를 먼저 실행하세요.")
        return None

    # 3. LLM 판결 요청
    prompt = f"""
    ### Reference Document (Guideline)
    {guideline}
    
    ### Task
    Session {session_id}에서 사용자가 본 {len(session_data)}개의 선택지를 비교 분석하십시오.
    가이드라인에 따라 사용자가 무의식적으로 가장 선호했을 선택지를 예측하고, 그 이유를 **한국어**로 설명하십시오.
    
    [Observed Options Data]
    {json.dumps(session_data, indent=2, ensure_ascii=False)}
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=JUDGE_SYSTEM_PROMPT)
    
    try:
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"[Judge Error] {e}")
        return None