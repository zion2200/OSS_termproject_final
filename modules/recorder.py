# modules/recorder.py
import cv2
import torch
import numpy as np
import time
import os
import csv
from datetime import datetime
from facenet_pytorch import MTCNN
from emotiefflib.facial_analysis import EmotiEffLibRecognizer
import mediapipe as mp
from config import LOG_DIR, USE_POSE

class BehaviorRecorder:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[INFO] Initializing Recorder on {self.device}...")
        
        # 모델 로드
        self.mtcnn = MTCNN(keep_all=True, device=self.device)
        self.rec = EmotiEffLibRecognizer(engine="torch", model_name="enet_b0_8_best_vgaf", device=self.device)
        
        # MediaPipe Pose
        self.pose = None
        if USE_POSE:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.emotion_labels = ["Anger", "Contempt", "Disgust", "Fear", "Happiness", "Neutral", "Sadness", "Surprise"]
        self.landmark_names = ["nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder"] # 필요한 것만 정의하거나 전체 정의

    def record_session(self, option_data, session_id):
        """
        특정 선택지(option_data)를 화면에 띄우고 사용자가 확인(Space/Enter)할 때까지 녹화.
        저장된 CSV 파일 경로를 반환.
        """
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("[ERROR] Webcam not found.")
            return None

        # 화면에 띄울 텍스트 준비 (제목 및 요약)
        title = option_data.get('title', 'Option')
        summary = option_data.get('summary', '')[:50] + "..." # 너무 길면 자름

        # 로깅 변수
        records = []
        start_time = time.time()
        filename = os.path.join(LOG_DIR, f"{session_id}_{option_data['id']}_{datetime.now().strftime('%H%M%S')}.csv")
        
        print(f"[REC] Recording started for: {title}. Press 'SPACE' to confirm and next.")

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            curr_time = time.time()
            fps = 1.0 / (curr_time - start_time + 1e-6) # 단순 계산
            
            # --- 1. 분석 (Pose & Emotion) ---
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            display_frame = frame.copy()
            
            # Pose
            pose_landmarks = None
            if self.pose:
                res = self.pose.process(frame_rgb)
                if res.pose_landmarks:
                    self.mp_drawing.draw_landmarks(display_frame, res.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    pose_landmarks = res.pose_landmarks.landmark

            # Emotion
            boxes, _ = self.mtcnn.detect(frame_rgb)
            faces = self.mtcnn(frame_rgb)
            
            top_emo = "none"
            probs = np.zeros(8)
            
            if faces is not None:
                # (간략화) 첫 번째 얼굴만 처리
                if isinstance(faces, torch.Tensor) and faces.ndim == 4:
                    face_np = faces[0].permute(1, 2, 0).cpu().numpy()
                    face_np = (face_np * 128 + 127.5).clip(0, 255).astype(np.uint8)
                    _, scores = self.rec.predict_emotions([face_np], logits=False)
                    probs = np.array(scores)[0]
                    top_emo = self.emotion_labels[np.argmax(probs)]

            # --- 2. 데이터 수집 ---
            row = {
                "t": curr_time - start_time,
                "fps": fps,
                "top_emotion": top_emo,
            }
            for i, label in enumerate(self.emotion_labels):
                row[f"prob_{label}"] = probs[i] * 100
            
            # Pose Data (필요한 코, 어깨 등만 저장 예시)
            if pose_landmarks:
                row["nose_x"] = pose_landmarks[0].x
                row["nose_y"] = pose_landmarks[0].y
                row["left_shoulder_z"] = pose_landmarks[11].z
                row["left_shoulder_vis"] = pose_landmarks[11].visibility
                # ... 필요한 랜드마크 추가 ...
            else:
                row["nose_x"] = -999
                row["left_shoulder_z"] = -999
                row["left_shoulder_vis"] = 0

            records.append(row)

            # --- 3. UI 표시 ---
            # 상단에 LLM 내용 표시 (OpenCV는 한글 지원 미흡하므로 영문 ID나 간단한 표시 권장, 혹은 PIL로 한글 그리기)
            cv2.putText(display_frame, f"Read: {option_data['id']}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Emotion: {top_emo}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(display_frame, "Press SPACE to Confirm", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Experiment", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '): # 스페이스바로 종료
                break
            elif key == ord('q'): # 강제 종료
                cap.release()
                cv2.destroyAllWindows()
                return None

        cap.release()
        cv2.destroyAllWindows()
        
        # CSV 저장
        self.save_csv(filename, records)
        return filename

    def save_csv(self, filename, records):
        if not records: return
        keys = records[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
        print(f"[SAVE] Log saved to {filename}")