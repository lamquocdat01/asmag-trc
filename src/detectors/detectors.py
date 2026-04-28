import os, time
import cv2
import numpy as np

class DetectionResult:
    def __init__(self, boxes=None, scores=None, class_ids=None, masks=None, inference_time_ms=0.0):
        self.boxes = boxes or []
        self.scores = scores or []
        self.class_ids = class_ids or []
        self.masks = masks or []
        self.inference_time_ms = inference_time_ms

class MockDetector:
    def __init__(self, name="mock_detector"):
        self.name = name

    def predict(self, frame, proposal_mask=None):
        start = time.time()
        boxes, masks, scores, class_ids = [], [], [], []
        if proposal_mask is None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, proposal_mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours((proposal_mask>0).astype(np.uint8)*255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) > 50:
                x,y,w,h = cv2.boundingRect(cnt)
                boxes.append([x,y,x+w,y+h])
                mask = np.zeros(proposal_mask.shape, dtype=np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                masks.append(mask)
                scores.append(0.9)
                class_ids.append(0)
        return DetectionResult(boxes, scores, class_ids, masks, (time.time()-start)*1000)

class YoloDetector:
    def __init__(self, model_path, name="yolo"):
        from ultralytics import YOLO
        self.name = name
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)
        else:
            self.model = YOLO(name if name.endswith(".pt") else "yolov8n.pt")

    def predict(self, frame, proposal_mask=None):
        start = time.time()
        results = self.model(frame, verbose=False)
        boxes, scores, class_ids, masks = [], [], [], []
        if results and len(results) > 0:
            r = results[0]
            if r.boxes is not None:
                for b in r.boxes:
                    xyxy = b.xyxy.cpu().numpy()[0].astype(int).tolist()
                    boxes.append(xyxy)
                    scores.append(float(b.conf.cpu().numpy()[0]) if b.conf is not None else 0.0)
                    class_ids.append(int(b.cls.cpu().numpy()[0]) if b.cls is not None else -1)
            if getattr(r, "masks", None) is not None and r.masks is not None and r.masks.data is not None:
                md = r.masks.data.cpu().numpy()
                for m in md:
                    m = cv2.resize((m>0.5).astype(np.uint8)*255, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
                    masks.append(m)
        return DetectionResult(boxes, scores, class_ids, masks, (time.time()-start)*1000)

def create_detector(mode="mock", model_path="", model_name="mock_detector"):
    if mode == "yolo":
        try:
            return YoloDetector(model_path, model_name)
        except Exception as e:
            print(f"[WARN] Cannot load YOLO, fallback to MockDetector. Error: {e}")
    return MockDetector(model_name)
