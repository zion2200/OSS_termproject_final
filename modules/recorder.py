# modules/recorder.py
import cv2
import torch
import numpy as np
import time
import os
import csv
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont  # [추가됨] 한글 출력을 위한 PIL
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
        """
        OpenCV 이미지(numpy array)를 받아 한글 텍스트를 그리고 반환하는 함수
        """
        # 1. OpenCV(BGR) -> PIL(RGB) 변환
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 2. 폰트 로드 (Windows의 맑은 고딕 사용, 없으면 기본 폰트)
        try:
            font = ImageFont.truetype("malgun.ttf", font_size)
        except OSError:
            # 맥/리눅스나 폰트가 없을 경우 기본 폰트 사용 (한글 깨질 수 있음)
            font = ImageFont.load_default()
            
        # 3. 텍스트 그리기
        draw.text(pos, text, font=font, fill=color)
        
        # 4. PIL(RGB) -> OpenCV(BGR) 변환 후 반환
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def record_session(self, option_data, session_id):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("[ERROR] Webcam not found.")
            return None

        # 텍스트 준비
        # 텍스트 준비 부분
        title_text = f"제목: {option_data.get('title', 'Option')}"
        
        # [수정] 요약문 + 결정적 한 방을 합쳐서 더 강력하게 보여줌
        summary_raw = option_data.get('summary', '')
        buying_point = option_data.get('buying_point', '')
        
        if buying_point:
            summary_text = f"{summary_raw} \n\n★핵심: {buying_point}"
        else:
            summary_text = summary_raw
        
        is_recording = False
        start_time = 0
        records = []
        
        filename = os.path.join(LOG_DIR, f"{session_id}_{option_data['id']}_{datetime.now().strftime('%H%M%S')}.csv")
        
        print(f"[READY] Webcam opened. Press ENTER to start reading '{option_data['title']}'.")

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            # 미러링 (거울 모드) - 선택 사항
            # frame = cv2.flip(frame, 1)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            display_frame = frame.copy()
            
            # --- 1. Pose ---
            pose_landmarks = None
            if self.pose:
                res = self.pose.process(frame_rgb)
                if res.pose_landmarks:
                    self.mp_drawing.draw_landmarks(display_frame, res.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    pose_landmarks = res.pose_landmarks.landmark

            # --- 2. Emotion ---
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
            
            # --- 3. UI 그리기 (한글 적용) ---
            
            if not is_recording:
                # [대기 모드]
                cv2.rectangle(display_frame, (0, 0), (640, 80), (50, 50, 50), -1)
                
                # 한글 출력 함수 사용
                display_frame = self.put_korean_text(display_frame, "대기 모드 (STANDBY)", (20, 10), 30, (0, 255, 255))
                display_frame = self.put_korean_text(display_frame, "[Enter]를 눌러 녹화 및 텍스트 시작", (20, 50), 20, (255, 255, 255))
                
            else:
                # [녹화 모드]
                curr_time = time.time()
                t_elapsed = curr_time - start_time
                fps = 1.0 / (0.001 + (t_elapsed / (len(records)+1)))

                # 상단 배경 박스
                cv2.rectangle(display_frame, (0, 0), (640, 160), (0, 0, 0), -1)
                
                # 제목 출력
                display_frame = self.put_korean_text(display_frame, title_text, (10, 20), 25, (255, 255, 255))
                
                # 요약문 줄바꿈 처리 및 출력
                y_pos = 60
                # 35글자씩 끊어서 출력
                chunk_size = 35
                for i in range(0, len(summary_text), chunk_size):
                    line = summary_text[i:i+chunk_size]
                    display_frame = self.put_korean_text(display_frame, line, (10, y_pos), 18, (200, 200, 200))
                    y_pos += 25
                
                display_frame = self.put_korean_text(display_frame, "[녹화중] 종료하려면 Space 바를 누르세요", (10, 135), 20, (0, 0, 255))

                # 데이터 수집 (CSV용)
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

            # 화면 출력
            cv2.imshow("Experiment", display_frame)
            key = cv2.waitKey(1) & 0xFF
            
            if not is_recording:
                if key == 13: # Enter
                    is_recording = True
                    start_time = time.time()
                    print(f"[REC] Started recording for '{title_text}'")
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
        # [중요] csv_fieldnames 사용
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"[SAVE] Log saved to {filename}")