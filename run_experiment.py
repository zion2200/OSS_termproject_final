import random
import uuid
import os
import sys

# 모듈 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.stimulus import generate_explanations
from modules.recorder import BehaviorRecorder
from modules.preprocessor import process_csv_to_json

def main():
    print("\n" + "="*50)
    print("   🧠 CLONE Preference Experiment Pipeline   ")
    print("="*50)
    
    # ---------------------------------------------------------
    # 1. 입력 단계 (하나씩 입력받기)
    # ---------------------------------------------------------
    print("\n[Step 1] 실험 설정을 입력해주세요.")
    
    # (1) 상황(Context) 입력
    print("\nQ1. 현재 어떤 상황인가요? (의사결정의 맥락)")
    print("   예) 여자친구랑 1주년 기념일 / 다음 달 카드값이 걱정됨 / 부모님 효도 관광")
    user_context = input(">> 상황(Context): ").strip()
    if not user_context:
        user_context = "일반적인 상황"

    # (2) 선택지(Options) 순차 입력
    print("\nQ2. 고민 중인 선택지들을 하나씩 입력해주세요. (입력을 마치려면 그냥 Enter)")
    user_options = []
    
    while True:
        # Option 1, Option 2, ... 이렇게 번호를 붙여서 물어봅니다
        opt = input(f">> 선택지 {len(user_options)+1}: ").strip()
        
        # 아무것도 안 쓰고 엔터만 치면 입력 종료
        if not opt:
            break
            
        user_options.append(opt)
    
    # 최소 2개 이상인지 확인
    if len(user_options) < 2:
        print(f"\n[ERROR] 선택지가 {len(user_options)}개뿐입니다. 최소 2개 이상 입력해주세요.")
        return

    print(f"\n✅ 입력 완료: 총 {len(user_options)}개 선택지")

    # ---------------------------------------------------------
    # 2. LLM 설명 생성 (Context 반영)
    # ---------------------------------------------------------
    print("\n" + "-"*50)
    print("[AI] 🤖 큐레이터가 상황에 맞춰 선택지를 분석 중입니다... (잠시만 기다려주세요)")
    
    # 상황(Context)과 선택지 리스트를 넘겨서 맞춤형 설명을 생성합니다.
    llm_result = generate_explanations(user_options, user_context)
    
    if not llm_result or "options" not in llm_result:
        print("[ERROR] LLM 분석에 실패했습니다. API Key나 네트워크를 확인해주세요.")
        return
    
    options_data = llm_result["options"]
    
    # ---------------------------------------------------------
    # 3. 실험 세션 준비 (랜덤화 및 ID 생성)
    # ---------------------------------------------------------
    # 순서 효과 방지를 위한 셔플
    random.shuffle(options_data)
    
    session_id = str(uuid.uuid4())[:8]
    print(f"[SYSTEM] 실험 순서가 랜덤화되었습니다. (Session ID: {session_id})")
    
    try:
        recorder = BehaviorRecorder()
    except Exception as e:
        print(f"[ERROR] 웹캠/녹화 장치 초기화 실패: {e}")
        return

    # ---------------------------------------------------------
    # 4. 측정 루프 (Recorder)
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("   🎥 실험 시작 (웹캠 창이 뜹니다)   ")
    print("   1. 창이 뜨면 [Enter]를 눌러 녹화 및 텍스트 표시 시작")
    print("   2. 다 읽었으면 [Space]를 눌러 종료 및 다음 단계로 이동")
    print("="*50)

    for idx, opt in enumerate(options_data):
        print(f"\n[Trial {idx+1}/{len(options_data)}]")
        print(f"주제: {opt['title']}")
        
        # Recorder 실행 (웹캠 UI 제어권 이양)
        # opt 딕셔너리에 context 정보 추가 (나중에 전처리 때 저장하기 위함)
        opt['user_context'] = user_context
        
        csv_path = recorder.record_session(opt, session_id)
        
        if csv_path:
            # 전처리 및 JSON Seed 생성
            json_path = process_csv_to_json(csv_path, opt, session_id)
            if json_path:
                print(f"   -> [저장 완료] {os.path.basename(json_path)}")
            else:
                print("   -> [주의] 데이터가 너무 짧거나(5프레임 미만) 처리 중 오류 발생.")
        else:
            print("\n[STOP] 사용자에 의해 실험이 중단되었습니다.")
            break

    print("\n" + "="*50)
    print("🏁 실험이 모두 종료되었습니다.")
    print(f"데이터 위치: data/seeds/ (Session {session_id})")
    print("이제 Step 2 (전문가 라벨링, label_data.py)를 진행해주세요.")

if __name__ == "__main__":
    main()