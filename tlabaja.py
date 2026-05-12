import time
from pathlib import Path
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from ffpyplayer.player import MediaPlayer



ALERT_DELAY_SECONDS = 2.0
MIN_DETECTION_CONFIDENCE = 0.55
MIN_TRACKING_CONFIDENCE = 0.55
GAZE_RATIO_MIN = 0.45
GAZE_RATIO_MAX = 0.65

MODEL_URL = (
	"https://storage.googleapis.com/mediapipe-models/face_landmarker/"
	"face_landmarker/float16/latest/face_landmarker.task"
)
MODEL_PATH = Path(__file__).with_name("face_landmarker.task")

RIGHT_EYE_CORNERS = (33, 133)
LEFT_EYE_CORNERS = (362, 263)
RIGHT_IRIS = (468, 469, 470, 471, 472)
LEFT_IRIS = (473, 474, 475, 476, 477)


def ensure_model(path: Path) -> Path:
	if path.exists():
		return path
	try:
		urllib.request.urlretrieve(MODEL_URL, path)
		print("Modelo descargado correctamente.")
	except Exception as exc:
		print(f"No se pudo descargar el modelo: {exc}")
	return path


def average_point(landmarks, indices):
	x = 0.0
	y = 0.0
	for idx in indices:
		x += landmarks[idx].x
		y += landmarks[idx].y
	count = float(len(indices))
	return x / count, y / count


def gaze_ratio(landmarks, corner_a, corner_b, iris_indices):
	x_a = landmarks[corner_a].x
	x_b = landmarks[corner_b].x
	left = min(x_a, x_b)
	right = max(x_a, x_b)
	width = right - left
	if width <= 1e-6:
		return None
	iris_x, _ = average_point(landmarks, iris_indices)
	return (iris_x - left) / width


def is_looking(landmarks):
	if len(landmarks) < 478:
		return False
	right_ratio = gaze_ratio(landmarks, RIGHT_EYE_CORNERS[0], RIGHT_EYE_CORNERS[1], RIGHT_IRIS)
	left_ratio = gaze_ratio(landmarks, LEFT_EYE_CORNERS[0], LEFT_EYE_CORNERS[1], LEFT_IRIS)
	if right_ratio is None or left_ratio is None:
		return False
	return (
		GAZE_RATIO_MIN <= right_ratio <= GAZE_RATIO_MAX
		and GAZE_RATIO_MIN <= left_ratio <= GAZE_RATIO_MAX
	)


class AlertVideoPlayer:
	def __init__(self, video_path: Path, window_name: str = "ALERTA"):
		self.video_path = str(video_path)
		self.window_name = window_name
		self.cap = None
		self.audio = None
		self.active = False

	def start(self):
		if self.active:
			return
		self.cap = cv2.VideoCapture(self.video_path)
		if not self.cap.isOpened():
			raise RuntimeError(f"No se pudo abrir el video: {self.video_path}")
		self.audio = MediaPlayer(self.video_path)
		self.active = True

	def stop(self):
		if not self.active:
			return
		self.active = False
		if self.cap is not None:
			self.cap.release()
			self.cap = None
		if self.audio is not None:
			try:
				self.audio.close_player()
			except AttributeError:
				try:
					self.audio.close()
				except Exception:
					pass
			self.audio = None
		cv2.destroyWindow(self.window_name)

	def update(self):
		if not self.active:
			return

		if self.audio is not None:
			_, val = self.audio.get_frame()
			if val == "eof":
				try:
					self.audio.close_player()
				except AttributeError:
					try:
						self.audio.close()
					except Exception:
						pass
				self.audio = MediaPlayer(self.video_path)

		ok, frame = self.cap.read()
		if not ok:
			self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
			ok, frame = self.cap.read()

		if ok:
			cv2.imshow(self.window_name, frame)


def main():
	video_path = Path(__file__).with_name("tlabaja.mp4")
	if not video_path.exists():
		raise FileNotFoundError(f"No se encontro el video: {video_path}")

	cap = cv2.VideoCapture(0)
	if not cap.isOpened():
		raise RuntimeError("No camera detected.")

	model_path = ensure_model(MODEL_PATH)
	base_options = python.BaseOptions(model_asset_path=str(model_path))
	options = vision.FaceLandmarkerOptions(
		base_options=base_options,
		running_mode=vision.RunningMode.VIDEO,
		num_faces=1,
		min_face_detection_confidence=MIN_DETECTION_CONFIDENCE,
		min_face_presence_confidence=MIN_DETECTION_CONFIDENCE,
		min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
	)
	landmarker = vision.FaceLandmarker.create_from_options(options)

	player = AlertVideoPlayer(video_path)
	not_looking_since = None

	try:
		while True:
			success, frame = cap.read()
			if not success:
				break

			frame = cv2.flip(frame, 1)
			rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
			timestamp_ms = int(time.monotonic() * 1000)
			results = landmarker.detect_for_video(mp_image, timestamp_ms)

			looking = False
			if results.face_landmarks:
				face_landmarks = results.face_landmarks[0]
				looking = is_looking(face_landmarks)

			now = time.monotonic()
			if looking:
				not_looking_since = None
				if player.active:
					player.stop()
			else:
				if not_looking_since is None:
					not_looking_since = now
				elif (now - not_looking_since) >= ALERT_DELAY_SECONDS:
					if not player.active:
						player.start()

			if player.active:
				player.update()

			status = "MIRANDO" if looking else "NO MIRANDO"
			cv2.putText(
				frame,
				status,
				(20, 40),
				cv2.FONT_HERSHEY_SIMPLEX,
				1.0,
				(0, 255, 0) if looking else (0, 0, 255),
				2,
			)

			cv2.imshow("Camara", frame)

			if cv2.waitKey(1) & 0xFF == 27:
				break
	finally:
		landmarker.close()
		player.stop()
		cap.release()
		cv2.destroyAllWindows()


if __name__ == "__main__":
	main()
