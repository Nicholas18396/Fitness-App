import cv2
import mediapipe as mp
import numpy as np


# ============================================================
# MEDIAPIPE
# ============================================================

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


# ============================================================
# VARIABLES
# ============================================================
#
# Each leg is tracked independently since the legs alternate
# driving toward the chest. The displayed counter is the sum
# of both legs' reps.
#

counter = 0
stage = "EXTENDED"

quit_app = False
back_to_menu = False

POSITION_FRAMES_REQUIRED = 3

left_stage = "EXTENDED"
right_stage = "EXTENDED"

left_extended_frames = 0
left_driven_frames = 0

right_extended_frames = 0
right_driven_frames = 0


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

    return np.degrees(
        np.arccos(cosine_angle)
    )


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
    global left_stage
    global right_stage
    global left_extended_frames
    global left_driven_frames
    global right_extended_frames
    global right_driven_frames

    counter = 0
    stage = "EXTENDED"

    left_stage = "EXTENDED"
    right_stage = "EXTENDED"

    left_extended_frames = 0
    left_driven_frames = 0

    right_extended_frames = 0
    right_driven_frames = 0


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

        # BACK
        if 20 <= x <= 200 and 10 <= y <= 55:

            back_to_menu = True

        # RESET
        elif 220 <= x <= 330 and 10 <= y <= 55:

            reset()

        # EXIT
        elif 520 <= x <= 630 and 10 <= y <= 55:

            quit_app = True


# ============================================================
# MOUNTAIN CLIMBER ALGORITHM
# ============================================================
#
# In a plank, each leg's shoulder - hip - knee angle stays near
# 180 while extended back. Driving a knee forward under the
# chest sharply lowers that angle. A rep is counted for a leg
# the moment it reaches the driven-in position.
#

def detect_mountain_climber(landmarks):

    global counter
    global stage
    global left_stage
    global right_stage
    global left_extended_frames
    global left_driven_frames
    global right_extended_frames
    global right_driven_frames

    EXTENDED_ANGLE = 150
    DRIVEN_ANGLE = 100

    left_angle = None
    right_angle = None

    # --------------------------------------------------------
    # LEFT LEG
    # --------------------------------------------------------

    if (
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.LEFT_SHOULDER
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.LEFT_HIP
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.LEFT_KNEE
        )
    ):

        shoulder = get_point(
            landmarks,
            mp_pose.PoseLandmark.LEFT_SHOULDER
        )

        hip = get_point(
            landmarks,
            mp_pose.PoseLandmark.LEFT_HIP
        )

        knee = get_point(
            landmarks,
            mp_pose.PoseLandmark.LEFT_KNEE
        )

        left_angle = calculate_angle(
            shoulder,
            hip,
            knee
        )

        if left_angle > EXTENDED_ANGLE:

            left_extended_frames += 1
            left_driven_frames = 0

            if left_extended_frames >= POSITION_FRAMES_REQUIRED:

                left_stage = "EXTENDED"

        elif left_angle < DRIVEN_ANGLE:

            left_driven_frames += 1
            left_extended_frames = 0

            if left_driven_frames >= POSITION_FRAMES_REQUIRED:

                if left_stage == "EXTENDED":

                    counter += 1

                left_stage = "DRIVEN"

    # --------------------------------------------------------
    # RIGHT LEG
    # --------------------------------------------------------

    if (
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_SHOULDER
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_HIP
        )
        and
        landmark_visible(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_KNEE
        )
    ):

        shoulder = get_point(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_SHOULDER
        )

        hip = get_point(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_HIP
        )

        knee = get_point(
            landmarks,
            mp_pose.PoseLandmark.RIGHT_KNEE
        )

        right_angle = calculate_angle(
            shoulder,
            hip,
            knee
        )

        if right_angle > EXTENDED_ANGLE:

            right_extended_frames += 1
            right_driven_frames = 0

            if right_extended_frames >= POSITION_FRAMES_REQUIRED:

                right_stage = "EXTENDED"

        elif right_angle < DRIVEN_ANGLE:

            right_driven_frames += 1
            right_extended_frames = 0

            if right_driven_frames >= POSITION_FRAMES_REQUIRED:

                if right_stage == "EXTENDED":

                    counter += 1

                right_stage = "DRIVEN"

    # --------------------------------------------------------
    # OVERALL STATE (FOR DISPLAY)
    # --------------------------------------------------------

    if left_stage == "DRIVEN" or right_stage == "DRIVEN":

        stage = "DRIVEN"

    else:

        stage = "EXTENDED"

    # --------------------------------------------------------
    # RETURN WHICHEVER ANGLE IS AVAILABLE, FOR DISPLAY
    # --------------------------------------------------------

    if left_angle is not None and right_angle is not None:

        return min(left_angle, right_angle)

    elif left_angle is not None:

        return left_angle

    elif right_angle is not None:

        return right_angle

    return None


# ============================================================
# RUN MOUNTAIN CLIMBER TRACKER
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

    cv2.namedWindow(
        window_name
    )

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

                    angle = detect_mountain_climber(
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
            # TITLE
            # ------------------------------------------------

            cv2.putText(
                image,
                "MOUNTAIN CLIMBERS",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 255),
                2
            )

            # ------------------------------------------------
            # COUNTER
            # ------------------------------------------------

            cv2.putText(
                image,
                f"REPS: {counter}",
                (20, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                3
            )

            # ------------------------------------------------
            # STATE
            # ------------------------------------------------

            cv2.putText(
                image,
                f"STATE: {stage}",
                (20, 205),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            # ------------------------------------------------
            # ANGLE
            # ------------------------------------------------

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

            # ------------------------------------------------
            # INSTRUCTIONS
            # ------------------------------------------------

            cv2.putText(
                image,
                "SIDE VIEW REQUIRED",
                (20, 285),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 200, 255),
                2
            )

            cv2.putText(
                image,
                "Shoulder - Hip - Knee (each leg)",
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
