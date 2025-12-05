# run_analysis.py
import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.guideline_maker import create_guideline
from modules.judge import evaluate_session

def main():
    print("=== CLONE Analysis & Recommendation System ===")
    
    while True:
        print("\n[Menu]")
        print("1. 가이드라인 생성/업데이트 (Stage 2)")
        print("2. 특정 세션 분석 및 추천 (Stage 3)")
        print("3. 종료")
        
        choice = input("선택: ").strip()
        
        if choice == "1":
            print("\n[1] 모든 Seed 데이터를 기반으로 가이드라인을 합성합니다...")
            guideline = create_guideline()
            if guideline:
                print("\n--- 생성된 가이드라인 (일부) ---")
                print(guideline[:500] + "...\n(전체 내용은 guideline.md 확인)")
                
        elif choice == "2":
            session_id = input("분석할 Session ID를 입력하세요: ").strip()
            if not session_id:
                print("ID를 입력해야 합니다.")
                continue
                
            print(f"\n[2] Session {session_id}의 데이터를 분석합니다...")
            result = evaluate_session(session_id)
            
            if result:
                print("\n" + "="*50)
                print(f"🏆 최종 추천: {result.get('final_recommendation')}")
                print("="*50)
                print(f"💡 선정 이유: {result.get('winning_reason')}")
                print("-" * 30)
                print("📊 옵션별 분석:")
                for opt, reason in result.get('analysis_per_option', {}).items():
                    print(f" - {opt}: {reason}")
                    
        elif choice == "3":
            print("종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")

if __name__ == "__main__":
    main()