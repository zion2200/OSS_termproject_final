# config.py
import os

# 1. API KEY (환경 변수에서 가져오거나 직접 입력)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY")
# YOUR_API_KEY
# 2. 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
SEED_DIR = os.path.join(DATA_DIR, "seeds")

# 폴더 자동 생성
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SEED_DIR, exist_ok=True)

# 3. 모델 설정
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# 4. 녹화 설정
USE_POSE = True  # MediaPipe Pose 사용 여부