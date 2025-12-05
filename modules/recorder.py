import cv2
import torch
import numpy as np
import time
import os
import csv
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
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
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5, 
                min_tracking_confidence=0.5
            )

        self.emotion_labels = ["Anger", "Contempt", "Disgust", "Fear", "Happiness", "Neutral", "Sadness", "Surprise"]
        
        self.csv_fieldnames = [
            "t", "fps", "top_emotion"
        ] + [f"prob_{emo}" for emo in self.emotion_labels] + [
            "nose_x", "nose_y", "nose_vis",
            "left_shoulder_z", "left_shoulder_vis",
            "right_shoulder_z", "right_shoulder_vis"
        ]

    def put_korean_text(self, img, text, pos, font_size, color):
        """OpenCV 이미지에 한글 텍스트 그리기"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        try:
            font = ImageFont.truetype("malgun.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        draw.text(pos, text, font=font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def create_stimulus_image(self, width=800, height=600):
        """텍스트를 보여줄 빈 캔버스(검은 배경) 생성"""
        return np.zeros((height, width, 3), dtype=np.uint8)

    def record_session(self, option_data, session_id):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("[ERROR] Webcam not found.")
            return None

        # 텍스트 데이터 준비
        title_text = f"주제: {option_data.get('title', 'Option')}"
        summary_text = option_data.get('summary', '')
        buying_point = option_data.get('buying_point', '')
        
        # 상태 변수
        is_recording = False
        start_time = 0
        records = []
        
        filename = os.path.join(LOG_DIR, f"{session_id}_{option_data['id']}_{datetime.now().strftime('%H%M%S')}.csv")
        
        print(f"[READY] Windows opened. Look at the 'Stimulus' window.")

        # 창 위치 설정을 위한 플래그
        windows_positioned = False

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            # --- 1. Monitor Window (웹캠 화면) ---
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            monitor_frame = frame.copy() # 웹캠 원본
            
            # Pose Drawing
            pose_landmarks = None
            if self.pose:
                res = self.pose.process(frame_rgb)
                if res.pose_landmarks:
                    self.mp_drawing.draw_landmarks(monitor_frame, res.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    pose_landmarks = res.pose_landmarks.landmark

            # Emotion Analysis
            faces = self.mtcnn(frame_rgb)
            top_emo = "none"
            probs = np.zeros(8)
            
            if faces is not None:
                if isinstance(faces, torch.Tensor) and faces.ndim == 4:
                    face_np = faces[0].permute(1, 2, 0).cpu().numpy()
                    face_np = (face_np * 128 + 127.5).clip(0, 255).astype(np.uint8)
                    _, scores = self.rec.predict_emotions([face_np], logits=False)
                    probs = np.array(scores)[0]
                    top_emo = self.emotion_labels[np.argmax(probs)]
            
            # Monitor 창에 감정 상태 표시 (작게)
            cv2.putText(monitor_frame, f"Emo: {top_emo}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # --- 2. Stimulus Window (텍스트 화면) ---
            stimulus_frame = self.create_stimulus_image(width=900, height=600)
            
            if not is_recording:
                # [대기 모드 UI]
                stimulus_frame = self.put_korean_text(stimulus_frame, "실험 대기 중 (STANDBY)", (300, 250), 30, (0, 255, 255))
                stimulus_frame = self.put_korean_text(stimulus_frame, "준비가 되셨으면 [Enter]를 눌러주세요.", (280, 300), 20, (255, 255, 255))
                
                # Monitor 창에도 표시
                cv2.putText(monitor_frame, "STANDBY - Press Enter", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
            else:
                # [녹화 모드 UI] - 여기에 텍스트를 예쁘게 뿌림
                curr_time = time.time()
                t_elapsed = curr_time - start_time
                fps = 1.0 / (0.001 + (t_elapsed / (len(records)+1)))

                # 1) 제목
                stimulus_frame = self.put_korean_text(stimulus_frame, title_text, (50, 50), 35, (255, 255, 255))
                
                # 2) 구분선 (그냥 텍스트로 대체하거나 cv2.line 사용)
                cv2.line(stimulus_frame, (50, 100), (850, 100), (100, 100, 100), 2)

                # 3) 요약문 출력 (줄바꿈)
                y_pos = 130
                chunk_size = 35 # 한 줄 글자 수
                for i in range(0, len(summary_text), chunk_size):
                    line = summary_text[i:i+chunk_size]
                    stimulus_frame = self.put_korean_text(stimulus_frame, line, (50, y_pos), 25, (220, 220, 220))
                    y_pos += 40
                
                # 4) Buying Point (강조)
                if buying_point:
                    y_pos += 20
                    stimulus_frame = self.put_korean_text(stimulus_frame, "★ 핵심 포인트:", (50, y_pos), 25, (100, 255, 100))
                    y_pos += 40
                    # buying point 줄바꿈
                    for i in range(0, len(buying_point), chunk_size):
                        line = buying_point[i:i+chunk_size]
                        stimulus_frame = self.put_korean_text(stimulus_frame, line, (50, y_pos), 25, (100, 255, 100))
                        y_pos += 40

                # 5) 하단 안내
                stimulus_frame = self.put_korean_text(stimulus_frame, "다 읽으셨으면 [Space]를 눌러 종료하세요.", (250, 550), 20, (100, 100, 255))

                # Monitor 창에 녹화 중 표시
                cv2.circle(monitor_frame, (30, 60), 10, (0, 0, 255), -1)
                cv2.putText(monitor_frame, "REC", (50, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # 데이터 수집
                row = {
                    "t": t_elapsed,
                    "fps": fps,
                    "top_emotion": top_emo
                }
                for i, label in enumerate(self.emotion_labels):
                    row[f"prob_{label}"] = probs[i] * 100
                
                # Pose Data Filling
                row["nose_x"] = -999; row["nose_y"] = -999; row["nose_vis"] = 0
                row["left_shoulder_z"] = -999; row["left_shoulder_vis"] = 0
                row["right_shoulder_z"] = -999; row["right_shoulder_vis"] = 0

                if pose_landmarks:
                    row["nose_x"] = pose_landmarks[0].x
                    row["nose_y"] = pose_landmarks[0].y
                    row["nose_vis"] = pose_landmarks[0].visibility

                    row["left_shoulder_z"] = pose_landmarks[11].z
                    row["left_shoulder_vis"] = pose_landmarks[11].visibility
                    
                    row["right_shoulder_z"] = pose_landmarks[12].z
                    row["right_shoulder_vis"] = pose_landmarks[12].visibility

                records.append(row)

            # --- 화면 출력 ---
            cv2.imshow("Monitor (Webcam)", monitor_frame)
            cv2.imshow("Stimulus (Text)", stimulus_frame)
            
            # 창 위치 자동 정렬 (최초 1회만)
            if not windows_positioned:
                cv2.moveWindow("Monitor (Webcam)", 10, 10)     # 모니터 왼쪽 상단
                cv2.moveWindow("Stimulus (Text)", 660, 10)     # 텍스트 오른쪽
                windows_positioned = True

            key = cv2.waitKey(1) & 0xFF
            
            if not is_recording:
                if key == 13: # Enter
                    is_recording = True
                    start_time = time.time()
                    print(f"[REC] Started recording.")
                elif key == ord('q'):
                    print("[STOP] Quit by user")
                    cap.release()
                    cv2.destroyAllWindows()
                    return None
            else:
                if key == 32: # Space
                    print("[STOP] Finished recording.")
                    break
        
        cap.release()
        cv2.destroyAllWindows()
        
        self.save_csv(filename, records)
        return filename

    def save_csv(self, filename, records):
        if not records: 
            print("[WARN] No records to save.")
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"[SAVE] Log saved to {filename}")