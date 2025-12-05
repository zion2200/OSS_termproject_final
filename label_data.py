
import os
import json
import glob
import google.generativeai as genai
from config import GEMINI_API_KEY, SEED_DIR

# 설정
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are a senior Behavioral Psychologist. 
Your task is to write a "Ground Truth Analysis" based on the Subject's self-reported preference and their observed non-verbal behavior.

INPUT:
1. Observed Behavior: (Posture, Gaze, Emotions detected by AI)
2. Subject's Actual Preference: (Score 1-5 and their comment)

OUTPUT:
Write a professional, 3-4 sentence analysis in KOREAN.
- Connect the observed behavior to the actual preference.
- If the behavior matched the preference (e.g., liked it + nodded), explain it as a strong signal.
- If there was a discrepancy (e.g., liked it + frowned), interpret it carefully (e.g., "Despite the serious expression indicating concentration...").
- Tone: Clinical, Objective, Insightful.
"""

def generate_expert_analysis(seed_data, user_score, user_comment):
    # LLM에게 줄 문맥 구성
    behavior_summary = seed_data.get('rule_based_interpretation', 'No behavioral data')
    metrics = seed_data.get('behavior_metrics', {})
    
    prompt = f"""
    ### Content Info
    Option: {seed_data['stimulus_content']['title']}
    
    ### Observed Behavior (AI detected)
    - Summary: {behavior_summary}
    - Key Metrics: {json.dumps(metrics, indent=2)}
    
    ### Subject's Self-Report (Ground Truth)
    - Preference Score: {user_score} / 5  (1=Hate, 5=Love)
    - Subject's Comment: "{user_comment}"
    
    Based on this, write the 'expert_analysis' paragraph.
    """
    
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT)
    
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        print(f"[ERROR] LLM generation failed: {e}")
        return "분석 생성 실패"

def main():
    files = sorted(glob.glob(os.path.join(SEED_DIR, "*.json")))
    print(f"=== Expert Labeling Tool (Total {len(files)} files) ===")
    print("본인이 느꼈던 실제 선호도를 입력해주세요. AI가 이를 바탕으로 분석지를 작성합니다.\n")

    for idx, fpath in enumerate(files):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 이미 분석이 있으면 스킵할지 물어보기 (여기선 덮어쓰기 모드로 진행)
        if data.get("expert_analysis"):
            print(f"⚠️ 이미 분석된 파일입니다: {os.path.basename(fpath)}")
            continue # 스킵하고 싶으면 주석 해제

        print(f"\n[{idx+1}/{len(files)}] {os.path.basename(fpath)}")
        print(f"제목: {data['stimulus_content']['title']}")
        print(f"요약: {data['stimulus_content']['summary']}")
        print(f"행동 요약: {data.get('rule_based_interpretation', 'N/A')}")
        print("-" * 30)

        # 사용자 입력 (Ground Truth 주입)
        while True:
            try:
                score = int(input("Q1. 실제 이 선택지가 얼마나 맘에 드셨나요? (1~5): "))
                if 1 <= score <= 5: break
            except: pass
            print("1에서 5 사이의 숫자를 입력해주세요.")
            
        comment = input("Q2. 간단한 이유나 당시 기분은? (선택/엔터): ").strip()
        if not comment: comment = "별다른 이유 없음."

        print("🔄 AI가 전문가 소견을 작성 중입니다...")
        expert_text = generate_expert_analysis(data, score, comment)
        
        # 결과 보여주기
        print(f"\n[작성된 분석]\n{expert_text}")
        
        # 데이터 업데이트
        data['expert_analysis'] = expert_text
        data['ground_truth_preference'] = score # 나중에 정확도 측정용으로 저장해두면 좋음
        
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("✅ 저장 완료!")

    print("\n=== 모든 라벨링 작업 완료 ===")

if __name__ == "__main__":
    main()