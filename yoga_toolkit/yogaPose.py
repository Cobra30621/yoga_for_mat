import yoga_toolkit.toolkit as toolkit
import cv2
import yoga_toolkit.AngleNodeDef as AngleNodeDef
import numpy as np

class YogaPose():
    '''
    type: WarriorII, Tree, ReversePlank, Plank ...etc
    '''
    def __init__(self, type):
        self.type = type
        self.tips = ""
        self.roi, self.angle_def, self.jsonfile_path, self.samplefile_path = self.initialize(type)
        self.angle_dict = self.initialAngleDict()
        self.sample_angle_dict = {}
        self.imagePath = "./data/image/WarriorIIRulePic/8.JPG" # temporary use to demo, skip it
        
    def initialize(self, type):
        roi = {}
        angle_def = None
        jsonfile_path = ""
        samplefile_path = ""
        if type == 'Tree':
            roi = {
                'LEFT_KNEE': False,
                'LEFT_HIP': False,
                'RIGHT_FOOT_INDEX': False,
                'RIGHT_KNEE': False,
                'RIGHT_HIP': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_INDEX': False,
                'RIGHT_INDEX': False,
            }
            angle_def = AngleNodeDef.TREE_ANGLE
            jsonfile_path = f"yoga_toolkit/JsonFile/TreePose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/TreePose/sample.mp4"
        elif type == 'WarriorII':
            roi = {
                'RIGHT_ANKLE': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False
            }
            angle_def = AngleNodeDef.WARRIOR_II_ANGLE
            jsonfile_path = f"yoga_toolkit/JsonFile/WarriorIIPose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/WarriorIIPose/sample.mp4"
        elif type == 'ReversePlank':
            roi = {
                'NOSE': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_INDEX': False,
                'RIGHT_INDEX': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'LEFT_KNEE': False,
                'RIGHT_KNEE': False
            }
            angle_def = AngleNodeDef.REVERSE_PLANK_ANGLE
            jsonfile_path = f"yoga_toolkit/JsonFile/ReversePlankPose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/ReversePlankPose/sample.mp4"
        elif type == "Plank":
            roi = {
                'NOSE': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'LEFT_KNEE': False,
                'RIGHT_KNEE': False,
                'LEFT_ANKLE': False,
                'RIGHT_ANKLE': False,
            }
            angle_def = AngleNodeDef.PLANK_ANGLE
            jsonfile_path = f"yoga_toolkit/JsonFile/PlankPose/sample_v3.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/PlankPose/sample_v1.mp4"
        elif type == 'Childs':
            roi = {
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'LEFT_ANKLE': False,
                'RIGHT_ANKLE': False,
            }
            angle_def = AngleNodeDef.CHILDS_ANGLE
            jsonfile_path = f"yoga_toolkit/JsonFile/ChildsPose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/ChildsPose/sample.mp4"
        elif type == "DownwardDog":
            roi = {
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'RIGHT_ANKLE':False,
                'LEFT_ANKLE':False,
                'LEFT_HEEL': False,
                'RIGHT_HEEL': False,
            }
            angle_def = AngleNodeDef.DOWNWARDDOG_ANGLE 
            jsonfile_path = f"yoga_toolkit/JsonFile/DownwardDogPose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/DownwardDogPose/sample.mp4"
        elif type == "LowLunge":
            roi = {
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'RIGHT_ANKLE':False,
                'LEFT_ANKLE':False,
            }
            angle_def = AngleNodeDef.LOWLUNGE_ANGLE 
            jsonfile_path = f"yoga_toolkit/JsonFile/LowLungePose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/LowLungePose/sample.mp4"
        elif type == "SeatedForwardBend":
            roi = {
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'RIGHT_ANKLE':False,
                'LEFT_ANKLE':False,
                'RIGHT_FOOT_INDEX':False,
                'LEFT_FOOT_INDEX':False,
            }
            angle_def = AngleNodeDef.SEATEDFORWARDBEND_ANGLE 
            jsonfile_path = f"yoga_toolkit/JsonFile/SeatedForwardBendPose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/SeatedForwardBendPose/sample.mp4"
        elif type == "Bridge":
            roi = {
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'RIGHT_ANKLE':False,
                'LEFT_ANKLE':False,
                'RIGHT_FOOT_INDEX':False,
                'LEFT_FOOT_INDEX':False,
            }
            angle_def = AngleNodeDef.BRIDGE_ANGLE 
            jsonfile_path = f"yoga_toolkit/JsonFile/BridgePose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/BridgePose/sample.mp4"
        elif type == "Pyramid":
            roi = {
                'NOSE': False,
                'LEFT_SHOULDER': False,
                'RIGHT_SHOULDER': False,
                'LEFT_ELBOW': False,
                'RIGHT_ELBOW': False,
                'LEFT_WRIST': False,
                'RIGHT_WRIST': False,
                'LEFT_HIP': False,
                'RIGHT_HIP': False,
                'RIGHT_KNEE': False,
                'LEFT_KNEE': False,
                'RIGHT_ANKLE':False,
                'LEFT_ANKLE':False,
                'RIGHT_FOOT_INDEX':False,
                'LEFT_FOOT_INDEX':False,
                'LEG': False,
            }
            angle_def = AngleNodeDef.PYRAMID_ANGLE 
            jsonfile_path = f"yoga_toolkit/JsonFile/PyramidPose/sample.json"
            samplefile_path = f"yoga_toolkit/SampleVideo/PyramidPose/sample.mp4"

        return roi, angle_def, jsonfile_path, samplefile_path
    
    def initialAngleDict(self, dict={}):
        index = 0
        for key,_ in self.angle_def.items():
            dict[key] = 0
            index+=1
        return dict
    
    def initialDetect(self):
        self.sample_angle_dict = toolkit.readSampleJsonFile(self.jsonfile_path)
        if self.sample_angle_dict == None:
            self.sample(self.samplefile_path, self.jsonfile_path)
            self.sample_angle_dict = toolkit.readSampleJsonFile(self.jsonfile_path)
        
    def sample(self, video_path, storage_path):
        '''
        Sample angle and storage to json
        return: None
        '''
        print(f"Sampling {video_path}...")
        sum_angle = np.zeros(len(self.angle_def))
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Video not open")
            exit()
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Sample Video end")
                break
            point2d, point3d = toolkit.getMediapipeResult(frame)
            if type(point3d) == int:
                print("sample video detect pose error")
                break
            perFrameOfAngle = []
            # for _,value in self.angle_def.items():
            #     angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
            #                                 list(toolkit.getLandmarks(point3d[value[1]])), 
            #                                 list(toolkit.getLandmarks(point3d[value[2]])))
            #     perFrameOfAngle.append(angle)
            if self.type == 'Tree' or self.type == 'WarriorII':
                for _,value in self.angle_def.items():
                    angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                                list(toolkit.getLandmarks(point3d[value[1]])), 
                                                list(toolkit.getLandmarks(point3d[value[2]])))
                    perFrameOfAngle.append(angle)
            elif self.type == 'Plank' or self.type == 'ReversePlank':
                for _,value in self.angle_def.items():
                    angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]]))[:2], 
                                                list(toolkit.getLandmarks(point3d[value[1]]))[:2], 
                                                list(toolkit.getLandmarks(point3d[value[2]]))[:2])
                    perFrameOfAngle.append(angle)
            sum_angle+=perFrameOfAngle
            print(perFrameOfAngle)
            cv2.imshow('sample', self.draw(frame.shape[1], frame.shape[0], frame, point2d))
            cv2.waitKey(1)
        print(sum_angle/frame_count) # 平均角度
        sum_angle/=frame_count
        toolkit.writeSampleJsonFile(sum_angle, self.angle_def, storage_path)
        print("Sample Done.")
        cap.release()
        
    def detect(self, frame, w, h, mode):
        '''
        detect incoming frame
        return draw frame
        '''
        self.tips = ""
        point2d, point3d = toolkit.getMediapipeResult(frame, mode)
        if type(point2d) == int and type(point3d) == int:
            self.tips = "無法偵測到完整骨架"
            # 水平翻轉影片
            frame = cv2.flip(frame, 180)
            return frame
        # for key,value in self.angle_def.items():
        #     angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
        #                             list(toolkit.getLandmarks(point3d[value[1]])), 
        #                             list(toolkit.getLandmarks(point3d[value[2]])))
        #     self.angle_dict[key] = angle
        # print(self.sample_angle_dict)
        # print(self.angle_dict)
        if(self.type == 'Tree'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.treePoseRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'WarriorII'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips, self.imagePath = toolkit.warriorIIPoseRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'ReversePlank'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]]))[:2], 
                                        list(toolkit.getLandmarks(point3d[value[1]]))[:2], 
                                        list(toolkit.getLandmarks(point3d[value[2]]))[:2])
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.reversePlankPoseRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'Plank'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]]))[:2], 
                                        list(toolkit.getLandmarks(point3d[value[1]]))[:2], 
                                        list(toolkit.getLandmarks(point3d[value[2]]))[:2])
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.plankPoseRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'Childs'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]]))[:2], 
                                        list(toolkit.getLandmarks(point3d[value[1]]))[:2], 
                                        list(toolkit.getLandmarks(point3d[value[2]]))[:2])
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.ChildsPoseRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'DownwardDog'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.DownwardDogRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'LowLunge'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.LowLungeRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'SeatedForwardBend'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.SeatedForwardBendRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'Bridge'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.BridgeRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)
        elif(self.type == 'Pyramid'):
            for key,value in self.angle_def.items():
                angle = toolkit.computeAngle(list(toolkit.getLandmarks(point3d[value[0]])), 
                                        list(toolkit.getLandmarks(point3d[value[1]])), 
                                        list(toolkit.getLandmarks(point3d[value[2]])))
                self.angle_dict[key] = angle
            self.roi, self.tips = toolkit.PyramidRule(self.roi, self.tips, self.sample_angle_dict, self.angle_dict, point3d)

        frame = self.draw(w, h, frame, point2d)
        return frame
    
    def draw(self, w, h, frame, point2d):
        # draw body connection
        # for m in toolkit.pose_connection:
        #     cv2.line(frame, toolkit.getLandmarks(point2d[m[0]], w, h), list(toolkit.getLandmarks(point2d[m[1]], w, h)), (0, 0, 255), 1)
        
        # draw points
        point_color = (0,0,0)
        for node in toolkit.nodeList:
            point = toolkit.getLandmarks(point2d[node.value], w, h)
            if node.name in self.roi:
                if self.roi[node.name]:
                    point_color = (0,255,0)
                else:
                    point_color = (255,0,0)
                    cv2.circle(frame, point, 7, point_color, 4)
            # else:
            #     point_color = (255,255,255)
            
            # draw result angle
            # if node.name in self.angle_def:
            #     text_size, _ = cv2.getTextSize(str(round(self.angle_dict[node.name], 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            #     cv2.putText(frame, str(round(self.angle_dict[node.name], 1)), (point[0]-text_size[0]//2, point[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (6, 211, 255), 1)
            
            # cv2.circle(frame, point, 3, point_color, -1)
        
        # draw sample angle
        # draw_y = 30
        # for key, value in self.sample_angle_dict.items():
        #     text = f"{key}: {value}"
        #     cv2.putText(frame, text, (10, draw_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (6, 211, 255), 1)
        #     draw_y+=20
        
        # 水平翻轉影片
        frame = cv2.flip(frame, 180)
        return frame