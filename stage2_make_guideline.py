# stage2_make_guideline.py
import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.guideline_maker import create_guideline

def main():
    print("==================================================")
    print("   📘 CLONE Stage 2: Guideline Synthesis Tool     ")
    print("==================================================")
    print("전문가 라벨링이 완료된 Seed 데이터를 기반으로")
    print("행동 분석 가이드라인(guideline.md)을 생성합니다.\n")

    confirm = input("시작하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("작업을 취소합니다.")
        return

    print("\n[Processing] 데이터 분석 및 가이드라인 합성 중...")
    
    # 가이드라인 생성 함수 호출 (modules/guideline_maker.py)
    guideline = create_guideline()
    
    if guideline:
        print("\n" + "="*50)
        print("✅ 가이드라인 생성 완료!")
        print("파일 위치: guideline.md")
        print("="*50)
        print("\n--- 생성된 가이드라인 미리보기 (상위 500자) ---")
        print(guideline[:500] + "...")
        print("-----------------------------------------------")
        print("이제 stage3_inference.py를 실행하여 추천 시스템을 사용할 수 있습니다.")
    else:
        print("\n[ERROR] 가이드라인 생성에 실패했습니다.")
        print("데이터 폴더(data/seeds)에 라벨링된(expert_analysis 포함) 파일이 있는지 확인해주세요.")

if __name__ == "__main__":
    main()