# 🧠 CLONE: 행동 기반 무의식 선호도 분석 시스템
> **Behavior-based Subconscious Preference Analysis System** > *"당신의 입은 거짓말을 해도, 당신의 동공과 자세는 거짓말을 하지 않습니다."*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gemini API](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange?logo=google&logoColor=white)](https://aistudio.google.com/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV-red?logo=opencv&logoColor=white)](https://opencv.org/)

![Project Demo](https://via.placeholder.com/800x400?text=Insert+Your+Demo+GIF+Here)

## 📖 프로젝트 소개 (Project Overview)
**"오늘 점심 뭐 먹지?", "이번 주말에 뭐 하지?"** 우리는 매일 수많은 선택의 기로에 서지만, 스스로가 진짜 무엇을 원하는지 모르는 '선택 장애(Decision Paralysis)'를 겪습니다.

이 프로젝트는 **사용자가 선택지를 읽는 동안의 비언어적 행동(시선, 자세, 미세 표정)**을 실시간으로 분석하여, 사용자의 무의식적 선호도를 파악하고 최적의 선택지를 추천해주는 AI 시스템입니다.

최신 행동 심리학 연구인 **CLONE (Clinical Reasoning via Neuropsychologist Emulation)** 프레임워크[1]를 응용하여, 단순 통계가 아닌 **'전문가 페르소나를 가진 AI 에이전트'**가 행동 데이터를 해석하고 추천 근거를 제시합니다.

### 🎯 핵심 목표
* **비언어적 데이터 수집:** 웹캠을 통해 Gaze(시선), Posture(자세), Micro-expression(미세 표정)을 실시간 추적
* **전문가 추론 모방:** 행동 심리학자의 진단 과정을 모방하여 데이터 해석 가이드라인 생성
* **개인화된 큐레이션:** 사용자의 현재 상황(Context)에 맞는 선택지 설명 및 최종 추천 제공

---

## 🛠️ 기술 스택 (Tech Stack)

| 분류 | 기술 | 설명 |
| :--- | :--- | :--- |
| **Language** | ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white) | 전체 시스템 구현 |
| **AI Model** | ![Gemini](https://img.shields.io/badge/-Google%20Gemini-8E75B2?logo=google&logoColor=white) | 상황별 설명 생성, 행동 데이터 해석, 가이드라인 합성 |
| **Computer Vision** | ![OpenCV](https://img.shields.io/badge/-OpenCV-5C3EE8?logo=opencv&logoColor=white) ![MediaPipe](https://img.shields.io/badge/-MediaPipe-00BACC?logo=google&logoColor=white) | 실시간 얼굴/포즈 인식, 랜드마크 추출 |
| **Emotion Analysis** | **EmotiEffLib** / **MTCNN** | 실시간 표정 인식 및 감정 확률 추출 |
| **Data Processing** | ![Pandas](https://img.shields.io/badge/-Pandas-150458?logo=pandas&logoColor=white) | 행동 로그 데이터(CSV) 전처리 및 JSON 구조화 |

---

## ⚙️ 시스템 구조 (Methodology)

본 프로젝트는 **CLONE 논문[1]의 3단계 프레임워크**를 의사결정 도메인에 맞게 변형하여 적용했습니다.

### 🔄 전체 파이프라인
1.  **Stimulus (자극 제시):** 사용자의 상황(Context)을 입력받아, LLM 큐레이터가 각 선택지의 장단점을 설득력 있게 설명합니다.
2.  **Recorder (반응 측정):** 사용자가 설명을 읽는 동안 웹캠을 통해 **자세 기울기(Leaning), 고개 끄덕임(Nodding), 감정 변화** 등을 초단위로 로깅합니다.
3.  **Preprocessor (데이터 가공):** Raw Data(CSV)를 분석하여 `Leaning Forward(관심)`, `Head Shaking(부정)` 등의 의미 있는 행동 지표로 변환합니다.
4.  **Judge Agent (추론 및 추천):** 사전에 학습된 **행동 분석 가이드라인(`guideline.md`)**을 기반으로 행동 데이터를 평가하여 최종 승자를 결정합니다.

---

## 🚀 설치 및 실행 (Getting Started)

### 1. 필수 라이브러리 설치
Python 3.10 이상의 환경에서 다음 명령어를 실행하세요.
```bash
# Repository 복제
git clone [https://github.com/YOUR_ID/YOUR_REPO_NAME.git](https://github.com/YOUR_ID/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

# 의존성 설치
pip install -r requirements.txt