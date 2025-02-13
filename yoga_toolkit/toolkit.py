import mediapipe as mp
import cv2
import json
import math as m
import yoga_toolkit.AngleNodeDef as AngleNodeDef

mp_pose = mp.solutions.pose
pose_connection = mp_pose.POSE_CONNECTIONS
nodeList = mp.solutions.pose.PoseLandmark
mp_sample_pose = mp_pose.Pose(static_image_mode=True,
                                        model_complexity=2,
                                        min_detection_confidence=0.5)
mp_result_pose = mp_pose.Pose(static_image_mode=False,
                                        model_complexity=2,
                                        min_detection_confidence=0.5)

def getMediapipeResult(frame, mode=True):
    """Get mediapipe result of this frame

    Args:
        frame (image array):  process frame
        mode (bool): set mediapipe args [static_image_mode]
            True -> use to different image
            False -> use to video

    Returns:
        2D & 3D result of mediapipe
        (if process error return 0,0)

    """
    try:
        if mode:
            results = mp_sample_pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            results = mp_result_pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        point2d = results.pose_landmarks.landmark
        point3d = results.pose_world_landmarks.landmark
        return point2d, point3d
    except:
        return 0, 0

def getLandmarks(landmark, w=None, h=None):
    """Get skeleton landmark x,y,z respectively
    
    Args:
        landmark (mediapipe landmark): skeleton landmark
        w (int): image w
        h (int): image h

    Returns:
        2D relative coordinates(image) landmark(x,y) || 3D real coordinates landmark(x,y,z)
    
    """
    if w == None or h == None:
        return landmark.x, landmark.y, landmark.z
    else:
        return int(landmark.x*w), int(landmark.y*h)

def readSampleJsonFile(path):
    """read joint angle sample json file
    
    Args:
        path (str): json file path

    Returns:
        sample angle in json(dict) format
        (if process error return None)
    """
    try:
        with open(path, 'r') as file:
            sample_angle = json.load(file)
            return sample_angle
    except:
        return None

def writeSampleJsonFile(angle_array, angle_def, path):
    """write sample joint angle in json file
    
    Args:
        angle_array (numpy array): sample angle array
        angle_def (list): joint points defined by AngleNodeDef.py
        path (str): json file storage path

    Returns:
        No return
    """
    data = {}
    index = 0
    for key,_ in angle_def.items():
        data[key] = angle_array[index]
        index+=1
    print(data)
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)

def computeAngle(point1, centerPoint, point2):
    """compute joint poins angle
        
    Args:
        point1 (list): joint points contains x,y,z
        centerPoint (list): joint points contains x,y,z
        point2 (list): joint points contains x,y,z
        
        centerPoint--->point1 = vector1
        centerPoint--->point2 = vector2
        use vector1 & vector2 compute angle
        
    Returns:
        degree (float)
    """
    p1_x, pc_x, p2_x = point1[0], centerPoint[0], point2[0]
    p1_y, pc_y, p2_y = point1[1], centerPoint[1], point2[1] 

    if len(point1) == len(centerPoint) == len(point2) == 3:
        # 3 dim
        p1_z, pc_z, p2_z = point1[2], centerPoint[2], point2[2]
    else:
        # 2 dim
        p1_z, pc_z, p2_z = 0,0,0

    # vector
    x1,y1,z1 = (p1_x-pc_x),(p1_y-pc_y),(p1_z-pc_z)
    x2,y2,z2 = (p2_x-pc_x),(p2_y-pc_y),(p2_z-pc_z)

    # angle
    cos_b = (x1*x2 + y1*y2 + z1*z2) / (m.sqrt(x1**2 + y1**2 + z1**2) *(m.sqrt(x2**2 + y2**2 + z2**2)))
    B = m.degrees(m.acos(cos_b))
    return B

def treePoseRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """tree pose rule 
        
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        if key == 'LEFT_KNEE' or key == 'LEFT_HIP':
            tolerance_val = 8
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi[key] = True
            elif angle_dict[key]<min_angle:
                roi[key] = False
                tips = "將左腳打直平均分配雙腳重量，勿將右腳重量全放在左腳大腿" if tip_flag else tips
            else:
                roi[key] = False
                tips = "請勿將右腳重量全放在左腳大腿，避免傾斜造成左腳負擔" if tip_flag else tips
        elif key == 'RIGHT_FOOT_INDEX':
            _,foot_y,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_FOOT_INDEX])
            _,knee_y,_ = getLandmarks(point3d[AngleNodeDef.LEFT_KNEE])
            if foot_y <= knee_y:
                roi[key] = True
            else:
                roi[key] = False
                if tip_flag == True:
                    tips = "請將右腳抬至高於左腳膝蓋的位置，勿將右腳放在左腳膝蓋上，\n避免造成膝蓋負擔"
        elif key == 'RIGHT_KNEE':
            _,_,knee_z = getLandmarks(point3d[AngleNodeDef.RIGHT_KNEE])
            _,_,hip_z = getLandmarks(point3d[AngleNodeDef.RIGHT_HIP])
            if angle_dict[key]<=65 and ((hip_z-knee_z)*100)<=17:
                roi[key] = True
            elif angle_dict[key]>65:
                roi[key] = False
                tips = "請將右腳再抬高一些，不可壓到左腳膝蓋" if tip_flag else tips
            elif ((hip_z-knee_z)*100)>17:
                roi[key] = False
                tips = "將臂部往前推，打開左右骨盆，右腳膝蓋不可向前傾" if tip_flag else tips
            else:
                roi[key] = False
                tips = "右腳膝蓋不可向前傾，須與髖關節保持同一平面" if tip_flag else tips
        elif key == 'RIGHT_HIP':
            if angle_dict[key]>=100:
                roi[key] = True
            else:
                roi[key] = False
                tips = "請確認右腳膝蓋是否已經抬至左腳膝蓋以上" if tip_flag else tips
        elif key == 'LEFT_SHOULDER' or key == 'RIGHT_SHOULDER':
            if angle_dict[key]>=120:
                roi[key] = True
            else:
                roi[key] = False
                tips = "請將雙手合掌並互相施力，往上伸展至頭頂正上方" if tip_flag else tips
        elif key == 'LEFT_ELBOW' or key == 'RIGHT_ELBOW':
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            if angle_dict[key]>=min_angle:
                roi[key] = True
            else:
                roi[key] = False
                tips = "請將雙手再往上伸展，使手軸貼近耳朵" if tip_flag else tips
            # if angle_dict[key]>=90:
            #     roi[key] = True
            # else:
            #     roi[key] = False
            #     tips = "請將手再抬高一些，並保持在頭頂正上方" if tip_flag else tips
        elif key == 'LEFT_INDEX' or key == 'RIGHT_INDEX':
            index_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_INDEX]) if key == 'LEFT_INDEX' else getLandmarks(point3d[AngleNodeDef.RIGHT_INDEX])
            left_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
            right_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
            if index_x>=right_shoulder_x and index_x<=left_shoulder_x:
                roi[key] = True
            elif index_x<right_shoulder_x:
                roi[key] = False
                tips = "請將雙手往左移動，保持在頭頂正上方" if tip_flag else tips
            elif index_x>left_shoulder_x:
                roi[key] = False
                tips = "請將雙手往右移動，保持在頭頂正上方" if tip_flag else tips
    if tips == "":
        tips = "動作正確"
    return roi, tips

def warriorIIPoseRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """warriorII pose rule 
        
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
        imagePath(str): temporary use to demo, skip it
    """
    
    # imageFolder temporary use to demo
    imageFolder = "./data/image/WarriorIIRulePic"
    imagePath = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
            # imagePath = f"{imageFolder}/8.JPG"
        if key == 'RIGHT_ANKLE': #1
            tolerance_val = 5
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            else:
                roi[key] = False
                tips = "請將右腳腳尖朝向右手邊" if tip_flag else tips
                imagePath = f"{imageFolder}/1.JPG" if tip_flag else imagePath
        elif key == 'RIGHT_KNEE': #2
            ankle_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_ANKLE])
            knee_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_KNEE])
            if angle_dict[key]>=90 and angle_dict[key]<=150 and abs((ankle_x-knee_x)*100)<=10:
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            elif abs((ankle_x-knee_x)*100)>10:
                roi[key] = False
                tips = "請將右腳膝蓋往右腳腳踝的方向移動，直到小腿與地面呈垂直" if tip_flag else tips
                imagePath = f"{imageFolder}/2.JPG" if tip_flag else imagePath
            elif angle_dict[key]<90:
                roi[key] = False
                tips = "臀部不可低於右腳膝蓋，請將左腳往內收回使臀部高於右腳膝蓋" if tip_flag else tips
                imagePath = f"{imageFolder}/2.JPG" if tip_flag else imagePath
            elif angle_dict[key]>150:
                roi[key] = False
                tips = "請將左腳再往後一些，讓臀部有空間可以下壓" if tip_flag else tips
                imagePath = f"{imageFolder}/2.JPG" if tip_flag else imagePath
        elif key == 'LEFT_KNEE': #3
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            # if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
            if angle_dict[key]>=min_angle:
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            else:
                roi[key] = False
                tips = "請將左腳膝蓋打直，並將左腳腳尖朝向前方" if tip_flag else tips
                imagePath = f"{imageFolder}/3.JPG" if tip_flag else imagePath
        elif key == 'LEFT_HIP' or key == 'RIGHT_HIP': #4
            if angle_dict[key]>=100:
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            else:
                roi[key] = False
                tips = "請將雙腳再拉開一些距離，臀部向前推並挺胸" if tip_flag else tips
                imagePath = f"{imageFolder}/4.JPG" if tip_flag else imagePath
        elif key == 'NOSE': #5
            nose_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_HIP])
            right_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_HIP])
            if nose_x>=(right_hip_x-0.1) and nose_x<=(left_hip_x+0.1):
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            else:
                roi[key] = False
                tips = "請將頭轉向彎曲腳的方向並直視前方" if tip_flag else tips
                imagePath = f"{imageFolder}/5.JPG" if tip_flag else imagePath
        elif key == 'LEFT_SHOULDER' or key == 'RIGHT_SHOULDER': #6
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            direction = "右" if key == 'RIGHT_SHOULDER' else "左"
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            elif angle_dict[key]<min_angle:
                roi[key] = False
                tips = f"請將{direction}手抬高，與肩膀呈水平，\n並將身體挺直朝向前方" if tip_flag else tips
                imagePath = f"{imageFolder}/6.JPG" if tip_flag else imagePath
            elif angle_dict[key]>max_angle:
                roi[key] = False
                tips = f"請將{direction}手放低，與肩膀呈水平，\n並將身體挺直朝向前方" if tip_flag else tips
                imagePath = f"{imageFolder}/6.JPG" if tip_flag else imagePath
        elif key == 'LEFT_ELBOW' or key == 'RIGHT_ELBOW': #7
            tolerance_val = 5
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            direction = "右" if key == 'RIGHT_ELBOW' else "左"
            # if angle_dict[key]>=140 and (angle_dict[key]>=min_angle and angle_dict[key]<=max_angle):
            if angle_dict[key]>=min_angle:
                roi[key] = True
                imagePath = f"{imageFolder}/8.JPG" if tip_flag else imagePath
            else:
                roi[key] = False
                tips = f"請將{direction}手手心朝下平放並打直{direction}手" if tip_flag else tips
                imagePath = f"{imageFolder}/7.JPG" if tip_flag else imagePath
    if tips == "":
        tips = "動作正確 ! "
        imagePath = f"{imageFolder}/8.JPG"
    return roi, tips, imagePath

def plankPoseRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """plank pose rule 
        
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    side = ''
    for key, value in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True

        if key == 'NOSE':
            if point3d[AngleNodeDef.NOSE].x > point3d[AngleNodeDef.LEFT_HIP].x and point3d[AngleNodeDef.NOSE].x > point3d[AngleNodeDef.RIGHT_HIP].x:
                roi['NOSE'] = True
                side = 'RIGHT_'
            elif tip_flag == True:
                roi['NOSE'] = True
                side = 'LEFT_'
        if key == side + 'EYE':
            if side == 'RIGHT_':
                eye_shoulder_distance = abs(point3d[AngleNodeDef.RIGHT_SHOULDER].y - point3d[AngleNodeDef.RIGHT_EYE].y)
                forearm_distance = abs(point3d[AngleNodeDef.RIGHT_SHOULDER].y - point3d[AngleNodeDef.RIGHT_ELBOW].y)
            else:
                eye_shoulder_distance = abs(point3d[AngleNodeDef.LEFT_SHOULDER].y - point3d[AngleNodeDef.LEFT_EYE].y)
                forearm_distance = abs(point3d[AngleNodeDef.LEFT_SHOULDER].y - point3d[AngleNodeDef.LEFT_ELBOW].y)

            if eye_shoulder_distance >= forearm_distance * 0.05:
                roi['LEFT_EYE'] = True
                roi['RIGHT_EYE'] = True
            elif tip_flag == True:
                tips = "請將頭抬起，保持頸椎平行於地面"

        elif key == side + 'ELBOW':
            if side == 'RIGHT_':
                elbow_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_ELBOW])
                shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
                hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_HIP])
            else:
                elbow_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_ELBOW])
                shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
                hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_HIP])
            
            if abs(elbow_x - shoulder_x) < abs(hip_x - shoulder_x) * 0.1:
                roi['RIGHT_ELBOW'] = True
                roi['LEFT_ELBOW'] = True
            elif tip_flag == True:
                roi['RIGHT_ELBOW'] = False
                roi['LEFT_ELBOW'] = False
                if elbow_x > shoulder_x:
                    tips = "請將手肘向後縮並確認手肘位置在肩關節下方"
                else:
                    tips = "請將手肘向前移並確認手肘位置在肩關節下方"

        elif key == side + 'SHOULDER':
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi['RIGHT_SHOULDER'] = True
                roi['LEFT_SHOULDER'] = True
            elif tip_flag == True:
                roi['RIGHT_SHOULDER'] = False
                roi['LEFT_SHOULDER'] = False
                if angle_dict[key] < min_angle:
                    tips = "請將手肘向前移並維持頸椎、胸椎、腰椎維持一直線平行於地面"
                else:
                    tips = "請將手肘向後縮並維持頸椎、胸椎、腰椎維持一直線平行於地面"

        elif key == side + 'HIP':
            tolerance_val = 5
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi['RIGHT_HIP'] = True
                roi['LEFT_HIP'] = True
            elif angle_dict[key] < min_angle and tip_flag == True:
                roi['RIGHT_HIP'] = False
                roi['LEFT_HIP'] = False
                tips = "請將屁股稍微放下"
            elif tip_flag == True:
                roi['RIGHT_HIP'] = False
                roi['LEFT_HIP'] = False
                tips = "請將屁股稍微抬起"

        elif key == side + 'KNEE':
            tolerance_val = 5
            min_angle = sample_angle_dict[key]-tolerance_val
            if angle_dict[key]>=min_angle:
                roi['RIGHT_KNEE'] = True
                roi['LEFT_KNEE'] = True
            elif tip_flag == True:
                roi['RIGHT_KNEE'] = False
                roi['LEFT_KNEE'] = False
                tips = "請將腳向前移，膝蓋伸直並讓腳踝到膝蓋成一直線"

        elif key == side + 'ANKLE':
            tolerance_val = 15
            min_angle = 30
            if angle_dict[key]>=min_angle:
                roi['RIGHT_ANKLE'] = True
                roi['LEFT_ANKLE'] = True
            elif angle_dict[key] < min_angle and tip_flag == True:
                roi['RIGHT_ANKLE'] = False
                roi['LEFT_ANKLE'] = False
                tips = "請用前腳掌將身體撐起"

    if tips == "":
        tips = "動作正確"
    return roi, tips
    
def reversePlankPoseRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """reverse plank pose rule 
        
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    side = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        if key == 'NOSE':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_HIP])
            right_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_HIP])
            if node_x>left_hip_x and node_x>right_hip_x:
                roi[key] = True
                side = "LEFT"
            elif node_x<left_hip_x and node_x<right_hip_x:
                roi[key] = True
                side = "RIGHT"
            else:
                roi[key] = False
                tips = "請將身體面向右方或左方坐下，並將雙手撐在肩膀下方，\n使上半身呈現斜線" if tip_flag else tips
                break
        if key == f"{side}_ELBOW":
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            # min_angle = sample_angle_dict[f"{sample_side}_ELBOW"]-tolerance_val
            # max_angle = sample_angle_dict[f"{sample_side}_ELBOW"]+tolerance_val
            if angle_dict[key]>=min_angle:
                roi["LEFT_ELBOW"] = True
                roi["RIGHT_ELBOW"] = True
            else:
                roi["LEFT_ELBOW"] = False
                roi["RIGHT_ELBOW"] = False
                tips = "請將雙手手軸打直" if tip_flag else tips
        elif key == f"{side}_INDEX":
            index_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_INDEX])
            shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
            if side == "LEFT":
                index_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_INDEX])
                shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
            if index_x < shoulder_x and side == "LEFT":
                roi["LEFT_INDEX"] = True
                roi["RIGHT_INDEX"] = True
            elif index_x > shoulder_x and side == "RIGHT":
                roi["LEFT_INDEX"] = True
                roi["RIGHT_INDEX"] = True
            else:
                roi["LEFT_INDEX"] = False
                roi["RIGHT_INDEX"] = False
                tips = "請將雙手手指朝向臀部，並將手臂打直，垂直於地面" if tip_flag else tips
        elif key == f"{side}_WRIST":
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            # min_angle = sample_angle_dict[f"{sample_side}_WRIST"]-tolerance_val
            # max_angle = sample_angle_dict[f"{sample_side}_WRIST"]+tolerance_val
            # if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
            if angle_dict[key]<=max_angle:
                roi["LEFT_WRIST"] = True
                roi["RIGHT_WRIST"] = True
            else:
                roi["LEFT_WRIST"] = False
                roi["RIGHT_WRIST"] = False
                tips = "請將手掌平貼於地面，\n讓肩膀、手軸、手腕成一直線垂直於地面" if tip_flag else tips
        elif key == f"{side}_SHOULDER":
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            # min_angle = sample_angle_dict[f"{sample_side}_SHOULDER"]-tolerance_val
            # max_angle = sample_angle_dict[f"{sample_side}_SHOULDER"]+tolerance_val
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "將臀部抬起，胸往前挺，使脊椎保持一直線" if tip_flag else tips
        elif key == f"{side}_HIP":
            tolerance_val = 5
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            # min_angle = sample_angle_dict[f"{sample_side}_HIP"]-tolerance_val
            # max_angle = sample_angle_dict[f"{sample_side}_HIP"]+tolerance_val
            if angle_dict[key]>=min_angle:
                roi["LEFT_HIP"] = True
                roi["RIGHT_HIP"] = True
            else:
                roi["LEFT_HIP"] = False
                roi["RIGHT_HIP"] = False
                tips = "請將臀部抬高一些，使身體保持一直線" if tip_flag else tips
        elif key == f"{side}_KNEE":
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            # min_angle = sample_angle_dict[f"{sample_side}_KNEE"]-tolerance_val
            # max_angle = sample_angle_dict[f"{sample_side}_KNEE"]+tolerance_val
            if angle_dict[key]>=min_angle:
                roi["LEFT_KNEE"] = True
                roi["RIGHT_KNEE"] = True
            else:
                roi["LEFT_KNEE"] = False
                roi["RIGHT_KNEE"] = False
                tips = "請將雙腳膝蓋打直，使身體保持一直線" if tip_flag else tips
    if tips == "":
        tips = "動作正確"
    return roi, tips

def ChildsPoseRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """child's pose rule 
    Args:
        roi (list): region of interesting joint for child's pose
		tips (str): tips
  		sample_angle_dict (dict): sample angle dict
		angle_dict (dict): angle dict
		point3d (mediapipe): mediapipe detect result
    Returns:
		roi (dict)
		tips (str)
    """
    side = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        #detect the side for the pose
        if key == 'NOSE':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_HIP])
            right_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_HIP])
            if node_x>left_hip_x and node_x>right_hip_x:
                roi[key] = True
                side = "LEFT"
            elif node_x<left_hip_x and node_x<right_hip_x:
                roi[key] = True
                side = "RIGHT"
            else:
                roi[key] = False
                tips = "請將身體面向右方或左方趴下，並用雙手將臀部向前伸直" if tip_flag else tips
                break
        if key == f'{side}_ELBOW':
            if angle_dict[key]>=150:
                roi["LEFT_ELBOW"] = True
                roi["RIGHT_ELBOW"] = True
            else:
                roi["LEFT_ELBOW"] = False
                roi["RIGHT_ELBOW"] = False
                tips = "請確認手掌是否已經貼至地面"   if tip_flag else tips
        elif key == f'{side}_SHOULDER':
            if angle_dict[key]>=150:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "請確認是否已經將手臂向前伸直" if tip_flag else tips
        elif key == f'{side}_HIP':
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]<=max_angle and min_angle<=angle_dict[key]:
                roi["LEFT_HIP"] = True
                roi["RIGHT_HIP"] = True
            else:
                roi["LEFT_HIP"] = False
                roi["RIGHT_HIP"] = False
                tips = "請確認是否已經將身體向前趴下" if tip_flag else tips	
        elif key == f'{side}_KNEE':
            if angle_dict[key]<=45:
                roi["LEFT_KNEE"] = True
                roi["RIGHT_KNEE"] = True
            else:
                roi["LEFT_KNEE"] = False
                roi["RIGHT_KNEE"] = False
                tips = "請確認雙腿是否已經屈膝向前" if tip_flag else tips		
    if tips == "":
        tips = "動作正確 ! "
    return roi, tips

def DownwardDogRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """Downward dog's pose rule 
    Args:
        roi (list): region of interesting joint for child's pose
		tips (str): tips
  		sample_angle_dict (dict): sample angle dict
		angle_dict (dict): angle dict
		point3d (mediapipe): mediapipe detect result
    Returns:
		roi (dict)
		tips (str)
    """
    side = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        #detect the side for the pose
        if key == 'NOSE':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_HIP])
            right_hip_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_HIP])
            if node_x>left_hip_x and node_x>right_hip_x:
                roi[key] = True
                side = "LEFT"
            elif node_x<left_hip_x and node_x<right_hip_x:
                roi[key] = True
                side = "RIGHT"
            else:
                roi[key] = False
                tips = "請將身體面向右方或左方，並用雙手將臀部向上撐起成倒V字型" if tip_flag else tips
                break
        if key == f'{side}_ELBOW':
            if angle_dict[key]>=100:
                roi["LEFT_ELBOW"] = True
                roi["RIGHT_ELBOW"] = True
            else:
                roi["LEFT_ELBOW"] = False
                roi["RIGHT_ELBOW"] = False
                tips = "請確認手掌是否已經貼至地面"   if tip_flag else tips
        elif key == f'{side}_SHOULDER':
            if angle_dict[key]>=150:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "請確認是否已經將手臂打直" if tip_flag else tips	
        elif key == f'{side}_HIP':
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]>=min_angle and angle_dict[key]<=max_angle:
                roi["LEFT_HIP"] = True
                roi["RIGHT_HIP"] = True
            else:
                roi["LEFT_HIP"] = False
                roi["RIGHT_HIP"] = False
                tips = "請確認是否已經將身體向下伸展且把背打直, 呈現倒v字型" if tip_flag else tips	
        elif key == f'{side}_KNEE':
            if angle_dict[key]>=150:
                roi["LEFT_KNEE"] = True
                roi["RIGHT_KNEE"] = True
            else:
                roi["LEFT_KNEE"] = False
                roi["RIGHT_KNEE"] = False
                tips = "請確認雙腿是否已經打直" if tip_flag else tips	
        elif key == f'{side}_ANKLE':
            if angle_dict[key]<=180:
                roi["LEFT_ANKLE"] = True
                roi["RIGHT_ANKLE"] = True
            else:
                roi["LEFT_ANKLE"] = False
                roi["RIGHT_ANKLE"] = False
                tips = "請確認腳跟是否已經貼地" if tip_flag else tips	
    if tips == "":
        tips = "動作正確 ! "
    return roi, tips

def LowLungeRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """Low Lunge pose rule   
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    side = ""
    side_back = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        #detect the side for the pose
        if key == 'NOSE':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
            right_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
            if node_x>left_shoulder_x and node_x>right_shoulder_x:
                roi[key] = True
                side = "LEFT"
                side_back = "RIGHT"
            elif node_x<left_shoulder_x and node_x<right_shoulder_x:
                roi[key] = True
                side = "RIGHT"
                side_back = "LEFT"
            else:
                roi[key] = False
                tips = "請將身體面向右方或左方，並將雙手向上舉起" if tip_flag else tips
                break
        if key == f'{side}_ELBOW':
            tolerance_val = 10
            min_angle = sample_angle_dict[key]-tolerance_val
            if angle_dict[key]>=min_angle:
                roi["LEFT_ELBOW"] = True
                roi["RIGHT_ELBOW"] = True
            else:
                roi["LEFT_ELBOW"] = False
                roi["RIGHT_ELBOW"] = False
                tips = "請確認手掌是否已經舉高過頭"   if tip_flag else tips
        elif key == f'{side}_SHOULDER':
            if angle_dict[key]>=150:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "請確認是否已經將手臂打直" if tip_flag else tips
        elif key == f'{side}_HIP':
            if angle_dict[key]<=100:
                roi[f"{side}_HIP"] = True
            else:
                roi[f"{side}_HIP"] = False
                tips = "請確認是否已經將重心壓低" if tip_flag else tips
        elif key == f'{side}_KNEE':
            if angle_dict[key]<=115:
                roi[f"{side}_KNEE"] = True
            else:
                #print(f"{side}_KNEE: ",angle_dict[key])
                roi[f"{side}_KNEE"] = False
                tips = "請確認是否已經將其中一只腳屈膝" if tip_flag else tips
        elif key == f"{side_back}_KNEE":
            if angle_dict[key]>=115:
                roi[f"{side_back}_KNEE"] = True
            else:
                roi[f"{side_back}_KNEE"] = False
                #print(f"{side_back}_KNEE: ", angle_dict[key])
                tips = "請確認是否將另一隻腳向後伸" if tip_flag else tips
    if tips == "":
        tips = "動作正確"
    return roi, tips

def SeatedForwardBendRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """Seated Forward Bend pose rule   
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    side = "LEFT"
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        #detect the side for the pose
        if key == 'LEFT_FOOT_INDEX':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_FOOT_INDEX])
            left_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
            right_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
            if node_x>left_shoulder_x and node_x>right_shoulder_x:
                roi[key] = True
                side = "LEFT"
            elif node_x<left_shoulder_x and node_x<right_shoulder_x:
                roi[key] = True
                side = "RIGHT"
            else:
                roi[key] = False
                tips = "請將身體面向右方或左方坐下，並將腳伸直" if tip_flag else tips
                break
        elif key == f'{side}_SHOULDER':
            if angle_dict[key]>=90:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "請確認是否已經將手臂向前伸" if tip_flag else tips
        elif key == f'{side}_HIP':
            tolerance_val = 20
            min_angle = sample_angle_dict[key]-tolerance_val
            max_angle = sample_angle_dict[key]+tolerance_val
            if angle_dict[key]<=max_angle and min_angle<=angle_dict[key]:
                roi["LEFT_HIP"] = True
                roi["RIGHT_HIP"] = True
            else:
                roi["LEFT_HIP"] = False
                roi["RIGHT_HIP"] = False
                tips = "請確認是否已經將身體向前彎，盡量碰觸到腳板" if tip_flag else tips
        elif key == f'{side}_KNEE':
            if angle_dict[key]>=150:
                roi["LEFT_KNEE"] = True
                roi["RIGHT_KNEE"] = True
            else:
                roi["LEFT_KNEE"] = False
                roi["RIGHT_KNEE"] = False
                tips = "請確認是否已經將雙腳向前伸直" if tip_flag else tips
        elif key == f"{side}_ANKLE":
            if angle_dict[key]<=145:
                roi["LEFT_ANKLE"] = True
                roi["RIGHT_ANKLE"] = True
            else:
                roi["LEFT_ANKLE"] = False
                roi["RIGHT_ANKLE"] = False
                tips = "請確認是否將腳踝輕微勾回" if tip_flag else tips
    if tips == "":
        tips = "動作正確"
    return roi, tips

def BridgeRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """Bridge pose rule   
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    side = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        #detect the side for the pose
        if key == 'NOSE':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
            right_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
            if node_x>left_shoulder_x and node_x>right_shoulder_x:
                roi[key] = True
                side = "LEFT"
            elif node_x<left_shoulder_x and node_x<right_shoulder_x:
                roi[key] = True
                side = "RIGHT"
            else:
                roi[key] = False
                tips = "請將身體平躺下，並將雙手放置於身體兩側" if tip_flag else tips
                break
        if key == f'{side}_ELBOW':
            tolerance_val = 25
            min_angle = sample_angle_dict[key]-tolerance_val
            if angle_dict[key]>=min_angle:
                roi["LEFT_ELBOW"] = True
                roi["RIGHT_ELBOW"] = True
            else:
                roi["LEFT_ELBOW"] = False
                roi["RIGHT_ELBOW"] = False
                #print(angle_dict[key])
                tips = "請確認手掌是否已經貼至地面"   if tip_flag else tips
        elif key == f'{side}_KNEE':
            if angle_dict[key]<=80:
                roi["LEFT_KNEE"] = True
                roi["RIGHT_KNEE"] = True
            else:
                roi["LEFT_KNEE"] = False
                roi["RIGHT_KNEE"] = False
                tips = "請確認是否已經將雙腳屈膝" if tip_flag else tips
        elif key == f'{side}_SHOULDER':
            if angle_dict[key]<=45:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "請確認是否已經將手臂放置於身體兩側" if tip_flag else tips
        elif key == f'{side}_HIP':
            if angle_dict[key]>=150:
                roi["LEFT_HIP"] = True
                roi["RIGHT_HIP"] = True
            else:
                roi["LEFT_HIP"] = False
                roi["RIGHT_HIP"] = False
                tips = "請確認是否已經將身體挺直，並與大腿形成一條直線" if tip_flag else tips
    if tips == "":
        tips = "動作正確"
    return roi, tips

def PyramidRule(roi, tips, sample_angle_dict, angle_dict, point3d):
    """Pyramid pose rule   
    Args:
        roi (list): region of interesting joint for tree pose
        tips (str): tips
        sample_angle_dict (dict): sample angle dict
        angle_dict (dict): angle dict
        point3d (mediapipe): mediapipe detect result
        
    Returns:
        roi (dict)
        tips (str)
    """
    side = ""
    for key, _ in roi.items():
        tip_flag = False
        if tips == "":
            tip_flag = True
        #detect the side for the pose
        if key == 'NOSE':
            node_x,_,_ = getLandmarks(point3d[AngleNodeDef.NOSE])
            left_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.LEFT_SHOULDER])
            right_shoulder_x,_,_ = getLandmarks(point3d[AngleNodeDef.RIGHT_SHOULDER])
            if node_x>left_shoulder_x and node_x>right_shoulder_x:
                roi[key] = True
                side = "LEFT"
            elif node_x<left_shoulder_x and node_x<right_shoulder_x:
                roi[key] = True
                side = "RIGHT"
            else:
                roi[key] = False
                tips = "請將雙腿呈現弓箭步姿，並將身體向前腳彎曲" if tip_flag else tips
                break
        if key == f'{side}_ELBOW':
            if angle_dict[key]>=90:
                roi["LEFT_ELBOW"] = True
                roi["RIGHT_ELBOW"] = True
            else:
                roi["LEFT_ELBOW"] = False
                roi["RIGHT_ELBOW"] = False
                #print(angle_dict[key])
                tips = "請確認手掌是否已經抓到腳踝"   if tip_flag else tips
        elif key == f'{side}_KNEE':
            tolerance_val = 20
            min_angle = sample_angle_dict[key]-tolerance_val
            if angle_dict[key]>=min_angle:
                roi["LEFT_KNEE"] = True
                roi["RIGHT_KNEE"] = True
            else:
                roi["LEFT_KNEE"] = False
                roi["RIGHT_KNEE"] = False
                #print(angle_dict[key])
                tips = "請確認是否已經將雙腳打直" if tip_flag else tips
        elif key == f'{side}_SHOULDER':
            if angle_dict[key]>=85:
                roi["LEFT_SHOULDER"] = True
                roi["RIGHT_SHOULDER"] = True
            else:
                roi["LEFT_SHOULDER"] = False
                roi["RIGHT_SHOULDER"] = False
                tips = "請確認是否已經將手臂放置於前腳兩側" if tip_flag else tips
        elif key == f'{side}_HIP':
            if angle_dict[key]<=110:
                roi["LEFT_HIP"] = True
                roi["RIGHT_HIP"] = True
            else:
                #print(angle_dict[key])
                roi["LEFT_HIP"] = False
                roi["RIGHT_HIP"] = False
                tips = "請確認是否已經將身體向前腳彎曲" if tip_flag else tips
        elif key == 'LEG_ANKLE':
            if angle_dict[key]<=90:
                roi["LEG"] = True
            else:
                roi["LEG"] = False
                tips = "請確認是否已經將一隻腳向後伸直" if tip_flag else tips
    if tips == "":
        tips = "動作正確"
    return roi, tips
