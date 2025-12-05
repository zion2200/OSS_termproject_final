import sys
import os
import glob
import json

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.judge import evaluate_session
from config import SEED_DIR

def get_available_sessions():
    """data/seeds 폴더를 스캔하여 분석 가능한 세션 ID 목록을 반환"""
    files = glob.glob(os.path.join(SEED_DIR, "seed_*.json"))
    sessions = {}
    
    for f in files:
        # 파일명 구조: seed_{session_id}_{option_id}.json
        filename = os.path.basename(f)
        try:
            parts = filename.split('_')
            if len(parts) >= 3:
                sid = parts[1] # session_id
                # 가장 최근 수정 시간을 기록
                mtime = os.path.getmtime(f)
                if sid not in sessions or mtime > sessions[sid]:
                    sessions[sid] = mtime
        except:
            continue
            
    # 시간 역순(최신순) 정렬
    sorted_sessions = sorted(sessions.items(), key=lambda x: x[1], reverse=True)
    return [s[0] for s in sorted_sessions]

def main():
    print("==================================================")
    print("   ⚖️ CLONE Stage 3: Inference & Recommendation   ")
    print("==================================================")
    
    # 1. 가이드라인 확인
    if not os.path.exists("guideline.md"):
        print("[ERROR] 'guideline.md' 파일이 없습니다.")
        print("먼저 'stage2_make_guideline.py'를 실행하여 가이드라인을 생성해주세요.")
        return

    while True:
        print("\n" + "-"*40)
        print("[메뉴 선택]")
        print("1. 최근 실험 목록에서 선택 (추천)")
        print("2. Session ID 직접 입력")
        print("q. 종료")
        
        choice = input(">> 선택: ").strip().lower()
        
        target_session_id = None
        
        if choice == '1':
            sessions = get_available_sessions()
            if not sessions:
                print("\n[WARN] 저장된 실험 데이터가 없습니다 (data/seeds 폴더 비어있음).")
                continue
                
            print("\n[최근 실험 목록]")
            for i, sid in enumerate(sessions):
                print(f"  {i+1}. Session ID: {sid}")
            
            try:
                idx = int(input("\n>> 분석할 번호를 입력하세요: ")) - 1
                if 0 <= idx < len(sessions):
                    target_session_id = sessions[idx]
                else:
                    print("잘못된 번호입니다.")
            except ValueError:
                print("숫자를 입력해주세요.")

        elif choice == '2':
            print("\n[ID 입력 가이드]")
            print("파일명이 'seed_62df57c9_opt1.json' 일 때,")
            print("ID는 가운데 있는 [ 62df57c9 ] 입니다.")
            target_session_id = input(">> Session ID 입력: ").strip()
            
        elif choice == 'q':
            print("종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")
            continue

        # 분석 실행
        if target_session_id:
            print(f"\n[Analyzing] Session '{target_session_id}' 분석 시작...")
            
            result = evaluate_session(target_session_id)
            
            if result:
                print("\n" + "★"*50)
                print(f"🏆 최종 추천: {result.get('final_recommendation', 'Unknown')}")
                print("★"*50)
                print(f"\n💡 선정 이유 (Rationale):\n{result.get('winning_reason', 'N/A')}")
                
                print("\n📊 상세 분석 (Analysis per Option):")
                for opt, reason in result.get('analysis_per_option', {}).items():
                    print(f"  - [{opt}]: {reason}")
            else:
                print(f"\n[WARN] 분석 실패. ID '{target_session_id}'에 해당하는 데이터가 없거나 에러가 발생했습니다.")

if __name__ == "__main__":
    main()