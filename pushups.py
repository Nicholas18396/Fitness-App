import cv2
import mediapipe as mp
import numpy as np

from collections import deque


# ============================================================
# MEDIAPIPE
# ============================================================

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


# ============================================================
# VARIABLES
# ============================================================

counter = 0
stage = "UP"

quit_app = False
back_to_menu = False

angle_history = deque(maxlen=5)

POSITION_FRAMES_REQUIRED = 5

down_frames = 0
up_frames = 0


# ============================================================
# ANGLE CALCULATION
# ============================================================

def calculate_angle(a, b, c):

    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    c = np.array(c, dtype=np.float32)

    ba = a - b
    bc = c - b

    denominator = (
        np.linalg.norm(ba)
        * np.linalg.norm(bc)
    )

    if denominator == 0:
        return 0

    cosine_angle = np.dot(
        ba,
        bc
    ) / denominator

    cosine_angle = np.clip(
        cosine_angle,
        -1.0,
        1.0
    )

    angle = np.degrees(
        np.arccos(cosine_angle)
    )

    return angle


# ============================================================
# GET LANDMARK
# ============================================================

def get_point(landmarks, landmark):

    point = landmarks[landmark.value]

    return [
        point.x,
        point.y
    ]


# ============================================================
# VISIBILITY
# ============================================================

def landmark_visible(
    landmarks,
    landmark,
    threshold=0.5
):

    return (
        landmarks[landmark.value].visibility
        > threshold
    )


# ============================================================
# RESET
# ============================================================

def reset():

    global counter
    global stage
    global down_frames
    global up_frames

    counter = 0
    stage = "UP"

    down_frames = 0
    up_frames = 0

    angle_history.clear()


# ============================================================
# MOUSE CALLBACK
# ============================================================

def mouse_callback(
    event,
    x,
    y,
    flags,
    param
):

    global quit_app
    global back_to_menu

    if event == cv2.EVENT_LBUTTONDOWN:

        # BACK TO MENU
        if 20 <= x <= 200 and 10 <= y <= 55:

            back_to_menu = True

        # RESET
        elif 220 <= x <= 330 and 10 <= y <= 55:

            reset()

        # EXIT
        elif 520 <= x <= 630 and 10 <= y <= 55:

            quit_app = True


# ============================================================
# PUSHUP ALGORITHM
# ============================================================

def detect_pushup(landmarks):

    global counter
    global stage
    global down_frames
    global up_frames

    left_angle = None
    right_angle = None

    # --------------------------------------------------------
    # LEFT ARM
    # --------------------------------------------------------

    if (
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.LEFT_SHOULDER
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.LEFT_ELBOW
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.LEFT_WRIST
        )
    ):

        shoulder = get_point(
            landmarks,
            mp_pose.PoseLandmark.LEFT_SHOULDER
        )

        elbow = get_point(
            landmarks,
            mp_pose.PoseLandmark.LEFT_ELBOW
        )

        wrist = get_point(
            landmarks,
            mp_pose.PoseLandmark.LEFT_WRIST
        )

        left_angle = calculate_angle(
            shoulder,
            elbow,
            wrist
        )

    # --------------------------------------------------------
    # RIGHT ARM
    # --------------------------------------------------------

    if (
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_SHOULDER
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_ELBOW
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_WRIST
        )
    ):

        shoulder = get_point(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_SHOULDER
        )

        elbow = get_point(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_ELBOW
        )

        wrist = get_point(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_WRIST
        )

        right_angle = calculate_angle(
            shoulder,
            elbow,
            wrist
        )

    # --------------------------------------------------------
    # DETERMINE ANGLE
    # --------------------------------------------------------

    if (
        left_angle is not None
        and right_angle is not None
    ):

        angle = (
            left_angle
            + right_angle
        ) / 2

    elif left_angle is not None:

        angle = left_angle

    elif right_angle is not None:

        angle = right_angle

    else:

        return None

    # --------------------------------------------------------
    # SMOOTH ANGLE
    # --------------------------------------------------------
    #
    # Raw per-frame angles are noisy, which was letting a single
    # jittery frame near the threshold count (or miss) a rep.
    # Averaging over a short history fixes that.
    #

    angle_history.append(
        angle
    )

    smoothed_angle = (
        sum(angle_history)
        / len(angle_history)
    )

    # --------------------------------------------------------
    # THRESHOLDS
    # --------------------------------------------------------

    UP_ANGLE = 155
    DOWN_ANGLE = 125

    # --------------------------------------------------------
    # STATE MACHINE (WITH DEBOUNCE)
    # --------------------------------------------------------
    #
    # Require several consecutive frames in a position before
    # switching state, same debounce approach used in situps.py.
    # This stops a single noisy frame from double-counting a rep.
    #

    if smoothed_angle < DOWN_ANGLE:

        down_frames += 1
        up_frames = 0

        if down_frames >= POSITION_FRAMES_REQUIRED:

            stage = "DOWN"

    elif smoothed_angle > UP_ANGLE:

        up_frames += 1
        down_frames = 0

        if up_frames >= POSITION_FRAMES_REQUIRED:

            if stage == "DOWN":

                counter += 1

            stage = "UP"

    return smoothed_angle


# ============================================================
# RUN PUSHUP TRACKER
# ============================================================

def run():

    global quit_app
    global back_to_menu

    quit_app = False
    back_to_menu = False

    reset()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        print("Could not open camera.")

        return

    window_name = "IRON TRACKER"

    cv2.namedWindow(window_name)

    cv2.setMouseCallback(
        window_name,
        mouse_callback
    )

    with mp_pose.Pose(
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
        model_complexity=1
    ) as pose:

        while cap.isOpened():

            success, frame = cap.read()

            if not success:
                break

            frame = cv2.flip(
                frame,
                1
            )

            image = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            image.flags.writeable = False

            results = pose.process(
                image
            )

            image.flags.writeable = True

            image = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2BGR
            )

            angle = None

            # ------------------------------------------------
            # BODY DETECTED
            # ------------------------------------------------

            if results.pose_landmarks:

                landmarks = (
                    results.pose_landmarks.landmark
                )

                try:

                    angle = detect_pushup(
                        landmarks
                    )

                except Exception:

                    pass

                mp_draw.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

            # ------------------------------------------------
            # TOP BAR
            # ------------------------------------------------

            cv2.rectangle(
                image,
                (0, 0),
                (640, 75),
                (35, 35, 35),
                -1
            )

            # BACK
            cv2.rectangle(
                image,
                (20, 10),
                (200, 55),
                (70, 70, 70),
                -1
            )

            cv2.putText(
                image,
                "BACK TO MENU",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

            # RESET
            cv2.rectangle(
                image,
                (220, 10),
                (330, 55),
                (0, 140, 255),
                -1
            )

            cv2.putText(
                image,
                "RESET",
                (242, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            # EXIT
            cv2.rectangle(
                image,
                (520, 10),
                (630, 55),
                (0, 0, 255),
                -1
            )

            cv2.putText(
                image,
                "EXIT",
                (545, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # ------------------------------------------------
            # INFORMATION
            # ------------------------------------------------

            cv2.putText(
                image,
                "PUSHUPS",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 255),
                2
            )

            cv2.putText(
                image,
                f"REPS: {counter}",
                (20, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                3
            )

            cv2.putText(
                image,
                f"STATE: {stage}",
                (20, 205),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            if angle is not None:

                cv2.putText(
                    image,
                    f"ANGLE: {int(angle)}",
                    (20, 245),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 0),
                    2
                )

            cv2.putText(
                image,
                "FRONT OR SIDE VIEW OK",
                (20, 285),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 200, 255),
                2
            )

            cv2.putText(
                image,
                "Keep shoulders and arms visible",
                (20, 320),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (200, 200, 200),
                2
            )

            # ------------------------------------------------
            # SHOW
            # ------------------------------------------------

            cv2.imshow(
                window_name,
                image
            )

            key = cv2.waitKey(10) & 0xFF

            if key == ord("q"):

                quit_app = True

            if quit_app or back_to_menu:

                break

    cap.release()

    cv2.destroyAllWindows()
