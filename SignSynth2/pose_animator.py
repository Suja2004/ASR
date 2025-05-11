import json
from direct.interval.LerpInterval import LerpPosInterval, LerpHprInterval
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import LVecBase3f

class PoseAnimator:
    def __init__(self, left_parts, right_parts):
        self.left_parts = left_parts
        self.right_parts = right_parts
        self.gesture_data = self.loadAllPoseData()
        self.current_pose = "default"
        self.pose_index = 0
        self.pose_sequence = ["j"]
        self.expanded_sequence = self.expandPoseSequence(self.pose_sequence)

    def loadAllPoseData(self):
        with open("sign_poses.json", "r") as f:
            return json.load(f)

    def expandPoseSequence(self, sequence):
        result = []
        for word in sequence:
            if word in self.gesture_data:
                result.append(word)
            else:
                result.extend([c for c in word if c in self.gesture_data])
        return result

    def loadPoseNow(self, pose_name):
        poses = self.gesture_data.get(pose_name)
        if not poses:
            return None

        if isinstance(poses, list):
            pose = poses[0]
        else:
            pose = poses

        return pose

    def applyPoseInstantly(self, pose):
        l = pose["leftHand"]
        r = pose["rightHand"]

        self.left_parts["arm"].setPos(*l["pos"])
        self.left_parts["arm"].setHpr(*l["hpr"])
        self.right_parts["arm"].setPos(*r["pos"])
        self.right_parts["arm"].setHpr(*r["hpr"])

        self._applyFingersPose(l.get("fingers", {}), self.left_parts)
        self._applyFingersPose(r.get("fingers", {}), self.right_parts)

    def _applyFingersPose(self, fingers, parts):
        for name, joints in fingers.items():
            for part, pose_data in zip(parts[name], joints):
                part.setPos(*pose_data["pos"])
                part.setHpr(*pose_data["hpr"])

    def animatePose(self, pose, time=0.05):
        sequence = []
        l = pose["leftHand"]
        r = pose["rightHand"]

        sequence += [
            LerpPosInterval(self.left_parts["arm"], time, LVecBase3f(*l["pos"])),
            LerpHprInterval(self.left_parts["arm"], time, LVecBase3f(*l["hpr"])),
            LerpPosInterval(self.right_parts["arm"], time, LVecBase3f(*r["pos"])),
            LerpHprInterval(self.right_parts["arm"], time, LVecBase3f(*r["hpr"])),
        ]

        def addFingerLerps(fingers, parts):
            for name, joints in fingers.items():
                for part, pose_data in zip(parts[name], joints):
                    sequence.append(LerpPosInterval(part, 0, LVecBase3f(*pose_data["pos"])))
                    sequence.append(LerpHprInterval(part, 0, LVecBase3f(*pose_data["hpr"])))

        addFingerLerps(l.get("fingers", {}), self.left_parts)
        addFingerLerps(r.get("fingers", {}), self.right_parts)

        Sequence(*sequence).start()
