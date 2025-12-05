import pandas as pd
import numpy as np
import json
import os
from config import SEED_DIR

# ---------------------------------------------------------
# 1. Feature Extraction Logic (Rule-based)
# ---------------------------------------------------------

def detect_head_gesture(df_vis):
    """
    코(nose)의 좌표 분산을 이용해 끄덕임(Nodding)과 가로저음(Shaking)을 감지
    """
    # 데이터가 너무 적거나 코가 안 보이면 스킵
    if len(df_vis) < 5 or df_vis['nose_vis'].mean() < 0.5:
        return "Not Detected", 0.0, 0.0

    # 노이즈 제거 (Rolling Mean)
    nose_x = df_vis['nose_x'].rolling(window=5).mean().bfill()
    nose_y = df_vis['nose_y'].rolling(window=5).mean().bfill()

    # 분산 계산 (움직임의 크기)
    var_x = float(nose_x.var() * 10000)
    var_y = float(nose_y.var() * 10000)

    # 판단 로직
    gesture = "Dynamic (Moving)"
    if var_x < 0.05 and var_y < 0.05:
        gesture = "Static (Still)"
    elif var_x > var_y * 1.5 and var_x > 0.1: # X축 움직임이 큼
        gesture = "Head Shaking (Negative/Confusion)"
    elif var_y > var_x * 1.5 and var_y > 0.1: # Y축 움직임이 큼
        gesture = "Head Nodding (Positive/Understood)"
    
    return gesture, var_x, var_y

def analyze_posture_lean(df_vis):
    """
    어깨의 Z축 변화(깊이)를 통해 몸을 기울였는지(관심) 뒤로 뺐는지(이완) 분석
    """
    if len(df_vis) < 5 or 'left_shoulder_z' not in df_vis.columns:
        return "Unknown", 0.0

    # 어깨가 잘 안 보이면 스킵
    if df_vis['left_shoulder_vis'].mean() < 0.5:
        return "Unknown", 0.0

    # 초반 30% vs 후반 30% 비교
    n = len(df_vis)
    start_z = df_vis[['left_shoulder_z', 'right_shoulder_z']].iloc[:int(n*0.3)].mean().mean()
    end_z = df_vis[['left_shoulder_z', 'right_shoulder_z']].iloc[int(n*0.7):].mean().mean()
    
    # MediaPipe Z축: 카메라에 가까울수록 값이 작아짐 (음수 방향 아님, 상대값임)
    # 하지만 보통 값의 변화량(Diff)을 봅니다.
    # start_z > end_z : 값이 작아짐 -> 카메라 쪽으로 다가옴 (Lean Forward)
    diff = start_z - end_z 

    posture = "Stable Posture"
    if diff > 0.05: 
        posture = "Leaning Forward (High Engagement)"
    elif diff < -0.05:
        posture = "Leaning Backward (Relaxed/Low Interest)"

    return posture, float(diff)

def analyze_gaze_stability(df_vis):
    """
    [New Feature] 시선의 안정성 분석.
    코의 위치 표준편차가 크면 산만함(Distracted), 작으면 집중(Focused).
    """
    if len(df_vis) < 5: return "Unknown"
    
    std_x = df_vis['nose_x'].std()
    std_y = df_vis['nose_y'].std()
    total_instability = (std_x + std_y) * 100
    
    if total_instability < 2.0:
        return "Highly Focused (Stable Gaze)"
    elif total_instability > 8.0:
        return "Distracted/Searching (Unstable Gaze)"
    else:
        return "Normal Gaze"

# ---------------------------------------------------------
# 2. Main Processing Function
# ---------------------------------------------------------

def process_csv_to_json(csv_path, option_data, session_id):
    """
    CSV 로그를 읽어 통계적 특징을 추출하고, LLM이 해석할 수 있는 
    자연어 요약(interpretation)을 포함한 JSON Seed를 생성합니다.
    """
    try:
        df = pd.read_csv(csv_path)
        df.replace(-999, np.nan, inplace=True)
    except Exception as e:
        print(f"[ERR] Failed to load CSV: {e}")
        return None

    # [방어 코드 추가] 필수 컬럼 확인
    required_cols = ['nose_x', 'nose_vis', 'left_shoulder_z']
    for col in required_cols:
        if col not in df.columns:
            print(f"[ERR] Missing column '{col}' in CSV. Skipping this file.")
            return None

    if len(df) < 5:
        print("[WARN] CSV data too short.")
        return None

    # Pose 유효 데이터 필터링
    df_vis = df.dropna(subset=['nose_x'])
    has_pose = len(df_vis) > len(df) * 0.5

    # --- A. 감정 분석 (Emotion Stats) ---
    emotion_cols = [c for c in df.columns if c.startswith("prob_")]
    avg_emotions = df[emotion_cols].mean()
    
    # Dominant Emotion (Neutral 제외)
    sorted_emos = avg_emotions.drop("prob_Neutral", errors='ignore').sort_values(ascending=False)
    dom_emo_name = sorted_emos.index[0].replace("prob_", "") if not sorted_emos.empty else "None"
    dom_emo_score = sorted_emos.iloc[0] if not sorted_emos.empty else 0.0

    # --- B. 행동 분석 (Pose Analysis) ---
    gesture, nose_var_x, nose_var_y = ("Not Detected", 0, 0)
    posture, posture_diff = ("Unknown", 0)
    gaze_stability = "Unknown"

    if has_pose:
        gesture, nose_var_x, nose_var_y = detect_head_gesture(df_vis)
        posture, posture_diff = analyze_posture_lean(df_vis)
        gaze_stability = analyze_gaze_stability(df_vis)

    # --- C. Rule-based Interpretation (LLM Input용 핵심 요약) ---
    # 나중에 행동 심리학자 에이전트가 이 문장을 참고합니다.
    interpretations = []
    
    # 1. 자세 해석
    if "Forward" in posture:
        interpretations.append("The user leaned forward, indicating active interest or cognitive engagement.")
    elif "Backward" in posture:
        interpretations.append("The user leaned backward, suggesting a relaxed state or potential disinterest.")
    
    # 2. 제스처 해석
    if "Nodding" in gesture:
        interpretations.append("Frequent head nodding was observed, a strong sign of agreement or understanding.")
    elif "Shaking" in gesture:
        interpretations.append("Head shaking was detected, indicating confusion, disagreement, or rejection.")
    
    # 3. 감정 해석
    if dom_emo_name in ["Happiness", "Surprise"]:
        interpretations.append(f"Positive micro-expressions ({dom_emo_name}) were detected.")
    elif dom_emo_name in ["Anger", "Disgust", "Contempt"]:
        interpretations.append(f"Negative micro-expressions ({dom_emo_name}) suggest dissatisfaction.")
    elif dom_emo_name == "Sadness":
        interpretations.append("Traces of 'Sadness' were found, which in this context often implies deep concentration.")
        
    # 4. 시선/집중 해석
    if "Distracted" in gaze_stability:
        interpretations.append("Gaze was unstable, suggesting the user was skimming or looking for information.")
    
    final_interpretation = " ".join(interpretations) if interpretations else "User showed neutral behavior with no significant signals."

    # --- D. JSON 구조화 ---
    seed_data = {
        "meta": {
            "session_id": session_id,
            "option_id": option_data.get('id', 'unknown'),
            "timestamp": pd.Timestamp.now().isoformat(),
            "csv_source": os.path.basename(csv_path),
            "user_context": option_data.get('user_context', 'Unknown Context')
        },
        "stimulus_content": {
            "title": option_data.get('title', ''),
            "summary": option_data.get('summary', ''),
            "buying_point": option_data.get('buying_point', ''),
            "pros": option_data.get('pros', []),
            "cons": option_data.get('cons', [])
        },
        "behavior_metrics": {
            "duration_sec": float(df['t'].max()),
            "fps_mean": float(df['fps'].mean()),
            "dominant_emotion": {
                "emotion": dom_emo_name,
                "score": float(dom_emo_score)
            },
            "emotion_full_stats": {k.replace("prob_", ""): float(v) for k, v in avg_emotions.items()},
            "posture": {
                "label": posture,
                "z_diff": float(posture_diff)
            },
            "gesture": {
                "label": gesture,
                "var_x": nose_var_x,
                "var_y": nose_var_y
            },
            "gaze": {
                "label": gaze_stability
            }
        },
        "rule_based_interpretation": final_interpretation,
        "expert_analysis": None  # Placeholder for Step 2
    }

    # --- E. 저장 ---
    out_name = f"seed_{session_id}_{option_data.get('id', 'opt')}.json"
    out_path = os.path.join(SEED_DIR, out_name)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)

    print(f"[PROCESS] JSON Seed created: {out_path}")
    return out_path