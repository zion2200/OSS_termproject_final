import random
import uuid
import os
import sys
import time

# 모듈 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.stimulus import generate_explanations
from modules.recorder import BehaviorRecorder
from modules.preprocessor import process_csv_to_json
from modules.judge import evaluate_session  # [New] 판사 에이전트 가져오기

def main():
    print("\n" + "="*60)
    print("      🧠 CLONE Real-time Preference Analysis System      ")
    print("="*60)

    # 0. 사전 체크
    if not os.path.exists("guideline.md"):
        print("\n[CRITICAL ERROR] 'guideline.md' 파일이 없습니다!")
        print("이 시스템을 실행하기 전에 'stage2_make_guideline.py'를 먼저 실행해서")
        print("행동 분석 가이드라인을 생성해야 합니다.")
        return
    
    # ---------------------------------------------------------
    # 1. 입력 단계
    # ---------------------------------------------------------
    print("\n[Step 1] 실험 설정을 입력해주세요.")
    
    print("\nQ1. 현재 어떤 상황인가요? (의사결정의 맥락)")
    print("   예) 주말에 넷플릭스 뭐 볼지 고민 중 / 여자친구 생일 선물 고르는 중")
    user_context = input(">> 상황(Context): ").strip()
    if not user_context:
        user_context = "일반적인 상황"

    print("\nQ2. 고민 중인 선택지들을 하나씩 입력해주세요. (입력을 마치려면 그냥 Enter)")
    user_options = []
    while True:
        opt = input(f">> 선택지 {len(user_options)+1}: ").strip()
        if not opt: break
        user_options.append(opt)
    
    if len(user_options) < 2:
        print(f"\n[ERROR] 선택지가 {len(user_options)}개뿐입니다. 최소 2개 이상 입력해주세요.")
        return

    # ---------------------------------------------------------
    # 2. LLM 설명 생성 (Context 반영)
    # ---------------------------------------------------------
    print("\n" + "-"*60)
    print("[AI] 🤖 큐레이터가 상황에 맞춰 선택지를 분석 중입니다... (잠시만 기다려주세요)")
    
    llm_result = generate_explanations(user_options, user_context)
    
    if not llm_result or "options" not in llm_result:
        print("[ERROR] LLM 분석 실패. 네트워크 상태나 API Key를 확인하세요.")
        return
    
    options_data = llm_result["options"]
    
    # ---------------------------------------------------------
    # 3. 실험 세션 준비
    # ---------------------------------------------------------
    random.shuffle(options_data) # 순서 섞기
    session_id = str(uuid.uuid4())[:8]
    print(f"[SYSTEM] 세션 ID 생성됨: {session_id}")
    
    try:
        recorder = BehaviorRecorder()
    except Exception as e:
        print(f"[ERROR] 녹화 장치 초기화 실패: {e}")
        return

    # ---------------------------------------------------------
    # 4. 측정 루프 (Recorder)
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print("   🎥 실험 시작 (웹캠 및 텍스트 창이 뜹니다)   ")
    print("   1. [Enter]를 눌러 읽기 시작 (녹화 ON)")
    print("   2. [Space]를 눌러 읽기 종료 (녹화 OFF & 저장)")
    print("="*60)

    # 데이터가 정상적으로 최소 1개 이상 저장되었는지 확인하는 플래그
    data_collected = False

    for idx, opt in enumerate(options_data):
        print(f"\n[Trial {idx+1}/{len(options_data)}] 주제: {opt['title']}")
        
        # Context 정보 주입
        opt['user_context'] = user_context
        
        # 녹화 실행
        csv_path = recorder.record_session(opt, session_id)
        
        if csv_path:
            # 전처리 및 JSON 생성
            json_path = process_csv_to_json(csv_path, opt, session_id)
            if json_path:
                print(f"   -> [데이터 확보 완료]")
                data_collected = True
            else:
                print("   -> [주의] 유효한 데이터가 생성되지 않았습니다 (너무 짧음 등).")
        else:
            print("\n[STOP] 사용자에 의해 실험이 중단되었습니다.")
            break

    # ---------------------------------------------------------
    # 5. 최종 추론 및 추천 (The Judge)
    # ---------------------------------------------------------
    if data_collected:
        print("\n" + "="*60)
        print("   🧠 행동 데이터 정밀 분석 중... (CLONE Agent)   ")
        print("   (가이드라인에 따라 무의식적 선호도를 계산하고 있습니다)")
        print("="*60)
        
        # 판사 에이전트 호출
        result = evaluate_session(session_id)
        
        if result:
            print("\n" + "★"*60)
            print(f"🏆 최종 추천: {result.get('final_recommendation', 'Unknown')}")
            print("★"*60)
            print(f"\n💡 선정 이유 (Rationale):\n{result.get('winning_reason', 'N/A')}")
            
            print("\n📊 옵션별 상세 분석:")
            for opt_title, reason in result.get('analysis_per_option', {}).items():
                print(f"  - [{opt_title}]: {reason}")
            
            print("\n" + "-"*60)
            print("실험이 성공적으로 종료되었습니다. 감사합니다.")
        else:
            print("\n[ERROR] 분석 결과를 가져오지 못했습니다.")
    else:
        print("\n[WARN] 분석할 데이터가 없어 추천을 건너뜁니다.")

if __name__ == "__main__":
    main()