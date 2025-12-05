# modules/guideline_maker.py
import os
import json
import glob
import google.generativeai as genai
from config import GEMINI_API_KEY, SEED_DIR, BASE_DIR

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are a Lead Researcher in Behavioral Psychology.
Your goal is to synthesize a "Diagnostic Guideline" based on multiple case studies (Seeds).

INPUT:
A list of cases where user behavior (gaze, posture, emotion) is mapped to their actual preference (Ground Truth).

TASK:
1. Analyze the correlation between behavioral signals and actual preferences across all cases.
2. Identify consistent patterns (e.g., "Leaning forward usually implies high interest").
3. Create a structured "Step-by-Step Guideline" that future agents can use to predict preference.

OUTPUT FORMAT (Markdown):
The output must be a clean Markdown document titled "Behavioral Analysis Guideline for Preference Prediction".
It should have sections like:
- Step 1: Analyze Posture (Interpretation rules)
- Step 2: Analyze Gaze & Gestures (Interpretation rules)
- Step 3: Analyze Micro-expressions (Interpretation rules)
- Final Scoring Rubric (How to calculate a 1-5 score)
"""

def create_guideline():
    # 1. 전문가 라벨링이 완료된 파일만 로드
    files = glob.glob(os.path.join(SEED_DIR, "*.json"))
    cases = []
    
    print(f"[Guideline Maker] {len(files)}개의 Seed 파일을 분석합니다...")
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 전문가 분석(Ground Truth)이 있는 경우만 학습 데이터로 사용
        if data.get("expert_analysis"):
            case_summary = f"""
            [Case ID: {os.path.basename(fpath)}]
            - Observed Metrics: {json.dumps(data['behavior_metrics'])}
            - Expert Analysis (Ground Truth): {data['expert_analysis']}
            - Actual Preference Score: {data.get('ground_truth_preference', 'N/A')}
            """
            cases.append(case_summary)
    
    if not cases:
        print("[ERROR] 전문가 라벨링된 데이터가 없습니다. label_data.py를 먼저 실행하세요.")
        return None

    # 2. LLM에게 패턴 도출 요청
    prompt = f"""
    Here are {len(cases)} labeled case studies. 
    Synthesize a unified "Behavioral Analysis Guideline" based ONLY on these cases.
    
    [Case Studies]
    {"".join(cases)}
    
    Write the guideline in KOREAN.
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
    
    try:
        response = model.generate_content(prompt)
        guideline_text = response.text
        
        # 파일로 저장
        save_path = os.path.join(BASE_DIR, "guideline.md")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(guideline_text)
            
        print(f"[SUCCESS] 가이드라인 생성 완료: {save_path}")
        return guideline_text
        
    except Exception as e:
        print(f"[ERROR] 가이드라인 생성 실패: {e}")
        return None