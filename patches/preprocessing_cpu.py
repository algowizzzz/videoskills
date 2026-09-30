"""Display-independent CPU face boxes for the local Mac prototype."""
import os
import cv2

coord_placeholder = (0.0, 0.0, 0.0, 0.0)

def read_imgs(paths):
    images = [cv2.imread(str(path)) for path in paths]
    if any(image is None for image in images):
        raise ValueError("A presenter frame could not be decoded.")
    return images

def get_landmark_and_bbox(paths, upperbondrange=0):
    frames = read_imgs(paths)
    if not frames:
        raise ValueError("No presenter frames found.")
    detector = cv2.FaceDetectorYN.create(os.environ["YUNET_MODEL"], "", (320, 320),
                                        score_threshold=0.7)
    boxes = []
    for index, frame in enumerate(frames):
        height, width = frame.shape[:2]
        detector.setInputSize((width, height))
        _, faces = detector.detect(frame)
        if faces is None or len(faces) != 1:
            raise ValueError(f"Expected one clear face in frame {index}; choose a frontal presenter clip.")
        x, y, w, h = faces[0][:4]
        box = (max(0, int(x)), max(0, int(y) + upperbondrange),
               min(width, int(x+w)), min(height, int(y+h)))
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError("Invalid detected face box.")
        boxes.append(box)
    print(f"CPU YuNet: detected one face in all {len(frames)} frames", flush=True)
    return boxes, frames
