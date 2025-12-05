# run_experiment.py
import random
import uuid
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
    print("\n[AI] 선택지 분석 및 설명 생성 중...")
    llm_result = generate_explanations(user_options)
    if not llm_result or "options" not in llm_result:
        print("[ERROR] LLM 분석 실패")
        return
    
    options_data = llm_result["options"]
    
    # 3. 랜덤 순서 섞기
    random.shuffle(options_data)
    print(f"\n[SYSTEM] 실험 순서가 랜덤화되었습니다. (총 {len(options_data)}개)")
    
    # 4. 실험 세션 시작
    recorder = BehaviorRecorder()
    session_id = str(uuid.uuid4())[:8] # 고유 세션 ID
    print(f"[SESSION] ID: {session_id}")

    for idx, opt in enumerate(options_data):
        print(f"\n--- Trial {idx+1}/{len(options_data)}: {opt['title']} ---")
        print(f"Summary: {opt['summary']}")
        print("준비가 되면 엔터를 눌러 녹화를 시작하세요.")
        input()
        
        # 녹화 시작 -> 확인(Space) -> 중지
        csv_path = recorder.record_session(opt, session_id)
        
        if csv_path:
            # 전처리 및 JSON 저장 바로 수행
            process_csv_to_json(csv_path, opt, session_id)
        else:
            print("[WARN] Recording failed/aborted.")

    print("\n=== 실험 종료 ===")
    print("모든 데이터가 data/seeds 폴더에 JSON으로 저장되었습니다.")

if __name__ == "__main__":
    main()