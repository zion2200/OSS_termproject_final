import os
import json
import glob
import time
import google.generativeai as genai
from config import GEMINI_API_KEY, SEED_DIR, BASE_DIR

genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# -----------------------------------------------------------------------------
# Prompt 1: Drafting Phase (Appendix B.2 Table 3 참조) 
# 논문의 "Drafts of Diagnostic Guideline" 생성 부분을 행동 분석용으로 번역
# -----------------------------------------------------------------------------
DRAFT_SYSTEM_PROMPT = """
You are a professional behavioral psychologist developing step-by-step guidelines on how to interpret non-verbal behavioral data to determine a subject's preference level.
"""

DRAFT_USER_TEMPLATE = """
Below is an explanation from a fellow psychologist on why they interpreted the user's behavior in that way and why they determined such a preference score.

Based on this, please create **step-by-step guidelines** for interpreting behavioral metrics (Posture, Gaze, Emotion), focusing primarily on how to utilize objective statistical data.

**IMPORTANT RULES:**
1. **Do not use your own knowledge or experience**; only use the information provided below. 
2. Focus on the correlation between specific metrics (e.g., 'Leaning Forward') and the preference result.

### Fellow Psychologist's Explanation (Ground Truth):
{expert_analysis}

### Observed Metrics:
{metrics}

### Actual Preference:
{score} / 5
"""

# -----------------------------------------------------------------------------
# Prompt 2: Consolidating Phase (Appendix B.2 Table 3 참조) [cite: 647]
# 논문의 "Synthesized Unified Diagnostic Guideline" 생성 부분 번역
# -----------------------------------------------------------------------------
CONSOLIDATE_SYSTEM_PROMPT = """
You are a Lead Researcher. Your task is to consolidate draft guidelines into a single master guideline.
"""

CONSOLIDATE_USER_TEMPLATE = """
Please consolidate the provided draft guidelines into a unified **"Step-by-Step Behavioral Analysis Guideline"**.

**IMPORTANT RULES:**
1. **Do not use your own knowledge or experience**, only the information provided in the drafts. [cite: 647]
2. Organize the content so that no key patterns from the drafts are omitted.
3. Specifically, describe the method for making the final preference prediction (High/Low) in as much detail as possible.

### Draft Guidelines:
{drafts}

### Output Format:
## Step-by-Step Guidelines for Interpreting Behavioral Data

### Step 1: Evaluate Posture & Engagement
(Synthesized rules...)

### Step 2: Assess Gaze & Head Gestures
(Synthesized rules...)

### Step 3: Analyze Emotional Signals
(Synthesized rules...)

### Step 4: Finalize Preference Diagnosis
- **High Preference (Score 4-5):** If...
- **Low Preference (Score 1-2):** If...
"""

def create_draft_for_case(seed_data):
    # 데이터 준비
    expert_analysis = seed_data.get('expert_analysis', 'N/A')
    metrics = json.dumps(seed_data.get('behavior_metrics', {}), indent=2)
    score = seed_data.get('ground_truth_preference', 'N/A')

    # 프롬프트 조립
    prompt = DRAFT_USER_TEMPLATE.format(
        expert_analysis=expert_analysis,
        metrics=metrics,
        score=score
    )
    
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=DRAFT_SYSTEM_PROMPT)
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        print(f"[Draft Error] {e}")
        return None

def create_guideline():
    files = glob.glob(os.path.join(SEED_DIR, "*.json"))
    drafts = []
    
    print(f"\n[Guideline Maker] Stage 2-1: Drafting (Simulating Appendix B.2)...")
    
    # 1. Drafting (Case-by-Case)
    for i, fpath in enumerate(files):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if data.get("expert_analysis"):
            print(f"   -> Processing Case {i+1}...")
            draft = create_draft_for_case(data)
            if draft:
                drafts.append(f"--- Draft {i+1} ---\n{draft}")
            time.sleep(1) 
            
    if not drafts:
        print("[ERROR] 데이터 부족.")
        return None

    print(f"\n[Guideline Maker] Stage 2-2: Consolidating (Simulating Appendix B.2)...")
    
    # 2. Consolidating
    full_input = CONSOLIDATE_USER_TEMPLATE.format(drafts="\n".join(drafts))
    
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=CONSOLIDATE_SYSTEM_PROMPT)
    
    try:
        response = model.generate_content(full_input)
        guideline_text = response.text
        
        save_path = os.path.join(BASE_DIR, "guideline.md")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(guideline_text)
            
        print(f"[SUCCESS] Guideline Saved: {save_path}")
        return guideline_text
        
    except Exception as e:
        print(f"[ERROR] Consolidation Failed: {e}")
        return None