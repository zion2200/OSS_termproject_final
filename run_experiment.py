import random
import uuid
import os
import sys

# 경로 설정 (필요시)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.stimulus import generate_explanations
from modules.recorder import BehaviorRecorder
from modules.preprocessor import process_csv_to_json

def main():
    print("=== Preference Experiment Pipeline ===")
    
    # 1. 사용자 입력 (선택지 설정)
    print("고민 중인 선택지들을 입력하세요 (종료하려면 엔터만 입력)")
    user_options = []
    while True:
        opt = input(f"Option {len(user_options)+1}: ").strip()
        if not opt: break
        user_options.append(opt)
    
    if len(user_options) < 2:
        print("최소 2개 이상의 선택지가 필요합니다.")
        return

    # 2. LLM 설명 생성
    print("\n[AI] 선택지 분석 및 설명 생성 중... (잠시만 기다려주세요)")
    llm_result = generate_explanations(user_options)
    
    if not llm_result or "options" not in llm_result:
        print("[ERROR] LLM 분석 실패. API Key나 네트워크를 확인해주세요.")
        return
    
    options_data = llm_result["options"]
    
    # 3. 랜덤 순서 섞기
    random.shuffle(options_data)
    print(f"\n[SYSTEM] 실험 순서가 랜덤화되었습니다. (총 {len(options_data)}개)")
    
    # 4. 실험 세션 시작
    try:
        recorder = BehaviorRecorder()
    except Exception as e:
        print(f"[ERROR] 녹화 장치 초기화 실패: {e}")
        return

    session_id = str(uuid.uuid4())[:8]
    print(f"[SESSION] ID: {session_id}")

    # --- 실험 루프 시작 ---
    for idx, opt in enumerate(options_data):
        print(f"\n" + "="*50)
        print(f"Trial {idx+1}/{len(options_data)}: {opt['title']}")
        print("-" * 50)
        
        # [수정 완료] input() 제거됨. 
        # recorder.record_session() 안에서 'Enter' 대기 상태로 시작합니다.
        csv_path = recorder.record_session(opt, session_id)
        
        if csv_path:
            # 전처리 및 JSON 변환
            json_path = process_csv_to_json(csv_path, opt, session_id)
            if json_path:
                print(f"[SUCCESS] 처리 완료: {os.path.basename(json_path)}")
            else:
                print("[WARN] 데이터 처리 실패 (데이터 부족 등)")
        else:
            print("[WARN] 실험이 중단되었습니다.")
            break # 사용자가 'q'를 눌러 중단한 경우 루프 탈출

    print("\n" + "="*50)
    print("=== 실험 종료 ===")
    print("모든 데이터가 data/seeds 폴더에 JSON으로 저장되었습니다.")

if __name__ == "__main__":
    main()