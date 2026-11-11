"""HM55 original motions, authored as keyframed poses in armature axes (no motion data is imported).
Rotation convention (degrees, relative to the A-pose rest, expressed in the parent's frame):
  x: for upward bones (Spine/Chest/Neck/Head) + = lean / nod forward; for hanging limbs - = swing forward
  y: roll about the forward axis (left arm + = toward the body, right arm - = toward the body)
  z: yaw, + = turn toward the character's left
30 frames per second. Speeds are authored estimates for review, not measured match data."""
import bpy
from mathutils import Quaternion
import hm_assemble as ha

FPS = 30
ARMS = {'UpperArm_L': (0, 8, 0), 'UpperArm_R': (0, -8, 0), 'LowerArm_L': (-12, 0, 0), 'LowerArm_R': (-12, 0, 0)}
READY = dict(ARMS, **{'UpperLeg_L': (-5, 0, 0), 'UpperLeg_R': (-5, 0, 0), 'LowerLeg_L': (9, 0, 0), 'LowerLeg_R': (9, 0, 0), 'Foot_L': (-4, 0, 0), 'Foot_R': (-4, 0, 0)})


def mirror(pose):
    out = {}
    for k, (x, y, z) in pose.items():
        n = k[:-2] + ('_R' if k.endswith('_L') else '_L') if k[-2:] in ('_L', '_R') else k
        out[n] = (x, -y, -z)
    return out


def P(base=None, **kw):
    d = dict(base or {}); d.update(kw); return d


RUN_A = {'UpperLeg_R': (-40, 0, 0), 'LowerLeg_R': (14, 0, 0), 'Foot_R': (-10, 0, 0), 'UpperLeg_L': (24, 0, 0), 'LowerLeg_L': (58, 0, 0), 'Foot_L': (28, 0, 0),
         'UpperArm_L': (-40, 8, 0), 'LowerArm_L': (-78, 0, 0), 'UpperArm_R': (34, -8, 0), 'LowerArm_R': (-62, 0, 0),
         'Hips': (0, 0, -6), 'Spine': (9, 0, 5), 'Chest': (3, 0, 8), 'Neck': (-4, 0, -3), 'Head': (-7, 0, -4)}
RUN_B = {'UpperLeg_R': (2, 0, 0), 'LowerLeg_R': (20, 0, 0), 'Foot_R': (2, 0, 0), 'UpperLeg_L': (-28, 0, 0), 'LowerLeg_L': (98, 0, 0), 'Foot_L': (12, 0, 0),
         'UpperArm_L': (-4, 8, 0), 'LowerArm_L': (-72, 0, 0), 'UpperArm_R': (-2, -8, 0), 'LowerArm_R': (-72, 0, 0),
         'Hips': (0, 0, 0), 'Spine': (10, 0, 0), 'Chest': (3, 0, 0), 'Neck': (-4, 0, 0), 'Head': (-8, 0, 0)}

ACTIONS = {
    'Idle': dict(loop=True, keys=[(1, READY, (0, 0, -0.012)), (31, P(READY, Spine=(1.5, 0, 1.5), Chest=(-1.5, 0, 0), Head=(-1, 0, -3), UpperArm_L=(0, 7, 0), UpperArm_R=(0, -7, 0)), (0.006, 0, -0.012)), (61, READY, (0, 0, -0.012))]),
    'Run': dict(loop=True, keys=[(1, RUN_A, (0, 0, -0.025)), (6, RUN_B, (0, 0, -0.050)), (11, mirror(RUN_A), (0, 0, -0.025)), (16, mirror(RUN_B), (0, 0, -0.050)), (21, RUN_A, (0, 0, -0.025))]),
    'Kick': dict(loop=False, keys=[
        (1, READY, (0, 0, -0.012)),
        (9, P(ARMS, UpperLeg_L=(-24, 0, 0), LowerLeg_L=(20, 0, 0), Foot_L=(-4, 0, 0), UpperLeg_R=(28, 0, 0), LowerLeg_R=(38, 0, 0), Foot_R=(22, 0, 0), UpperArm_L=(18, -30, 0), UpperArm_R=(-24, -10, 0),
              LowerArm_L=(-25, 0, 0), LowerArm_R=(-40, 0, 0), Spine=(6, 0, 8), Head=(12, 0, 0)), (0, -0.05, -0.035)),
        (15, P(ARMS, UpperLeg_L=(-18, 0, 0), LowerLeg_L=(30, 0, 0), Foot_L=(-10, 0, 0), UpperLeg_R=(44, 0, 0), LowerLeg_R=(98, 0, 0), Foot_R=(32, 0, 0), UpperArm_L=(8, -52, 0), UpperArm_R=(-36, -12, 0),
               LowerArm_L=(-20, 0, 0), LowerArm_R=(-50, 0, 0), Hips=(0, 0, 10), Spine=(2, 0, 10), Chest=(0, 0, 8), Neck=(6, 0, -4), Head=(12, 0, -6)), (0, -0.09, -0.045)),
        (20, P(ARMS, UpperLeg_L=(-12, 0, 0), LowerLeg_L=(22, 0, 0), Foot_L=(-8, 0, 0), UpperLeg_R=(-30, 0, 0), LowerLeg_R=(22, 0, 0), Foot_R=(40, 0, 0), UpperArm_L=(-6, -48, 0), UpperArm_R=(24, -18, 0),
               LowerArm_L=(-20, 0, 0), LowerArm_R=(-30, 0, 0), Hips=(0, 0, -4), Spine=(12, 0, -6), Chest=(4, 0, -8), Neck=(8, 0, 0), Head=(14, 0, 0)), (0, -0.11, -0.035)),
        (26, P(ARMS, UpperLeg_L=(6, 0, 0), LowerLeg_L=(8, 0, 0), Foot_L=(20, 0, 0), UpperLeg_R=(-80, 0, 0), LowerLeg_R=(28, 0, 0), Foot_R=(32, 0, 0), UpperArm_L=(-30, -28, 0), UpperArm_R=(40, -24, 0),
               LowerArm_L=(-30, 0, 0), LowerArm_R=(-25, 0, 0), Hips=(0, 0, -12), Spine=(4, 0, -10), Chest=(0, 0, -10), Neck=(0, 0, 6), Head=(2, 0, 8)), (0, -0.14, 0.015)),
        (41, READY, (0, -0.16, -0.012))]),
    'LookAround': dict(loop=False, keys=[
        (1, READY, (0, 0, -0.012)), (16, P(READY, Chest=(0, 0, 6), Neck=(0, 0, 28), Head=(0, 0, 38)), (0, 0, -0.012)), (31, READY, (0, 0, -0.012)),
        (46, P(READY, Chest=(0, 0, -6), Neck=(0, 0, -28), Head=(0, 0, -38)), (0, 0, -0.012)), (61, READY, (0, 0, -0.012)),
        (71, P(READY, Neck=(-16, 0, 0), Head=(-26, 0, 0)), (0, 0, -0.012)), (81, P(READY, Neck=(22, 0, 0), Head=(28, 0, 0)), (0, 0, -0.012)),
        (91, P(READY, Neck=(0, 14, 10), Head=(0, 18, 12)), (0, 0, -0.012)), (101, READY, (0, 0, -0.012))]),
    'ThrowIn': dict(loop=False, keys=[
        (1, P(READY, UpperArm_L=(-70, 8, 0), UpperArm_R=(-70, -8, 0), LowerArm_L=(-70, 0, 0), LowerArm_R=(-70, 0, 0)), (0, 0, -0.012)),
        (14, P(UpperArm_L=(-168, 6, 0), UpperArm_R=(-168, -6, 0), LowerArm_L=(-85, 0, 0), LowerArm_R=(-85, 0, 0), Spine=(-12, 0, 0), Chest=(-9, 0, 0), Neck=(-5, 0, 0), Head=(-6, 0, 0),
               UpperLeg_L=(-14, 0, 0), UpperLeg_R=(-14, 0, 0), LowerLeg_L=(30, 0, 0), LowerLeg_R=(30, 0, 0), Foot_L=(-6, 0, 0), Foot_R=(-6, 0, 0)), (0, 0.02, -0.035)),
        (21, P(UpperArm_L=(-128, 6, 0), UpperArm_R=(-128, -6, 0), LowerArm_L=(-18, 0, 0), LowerArm_R=(-18, 0, 0), Spine=(13, 0, 0), Chest=(8, 0, 0), Neck=(2, 0, 0), Head=(4, 0, 0),
               UpperLeg_L=(-6, 0, 0), UpperLeg_R=(-6, 0, 0), LowerLeg_L=(8, 0, 0), LowerLeg_R=(8, 0, 0), Foot_L=(14, 0, 0), Foot_R=(14, 0, 0)), (0, -0.03, 0.0)),
        (30, P(ARMS, UpperArm_L=(-62, 10, 0), UpperArm_R=(-62, -10, 0), LowerArm_L=(-12, 0, 0), LowerArm_R=(-12, 0, 0), Spine=(17, 0, 0), Chest=(8, 0, 0), UpperLeg_L=(-8, 0, 0), UpperLeg_R=(-8, 0, 0),
               LowerLeg_L=(12, 0, 0), LowerLeg_R=(12, 0, 0)), (0, -0.04, -0.015)),
        (46, READY, (0, -0.04, -0.012))]),
    'Header': dict(loop=False, keys=[
        (1, READY, (0, 0, -0.012)),
        (10, P(UpperLeg_L=(-48, 0, 0), UpperLeg_R=(-48, 0, 0), LowerLeg_L=(86, 0, 0), LowerLeg_R=(86, 0, 0), Foot_L=(-30, 0, 0), Foot_R=(-30, 0, 0), Spine=(18, 0, 0), Chest=(6, 0, 0), Neck=(-8, 0, 0), Head=(-12, 0, 0),
               UpperArm_L=(30, -8, 0), UpperArm_R=(30, 8, 0), LowerArm_L=(-35, 0, 0), LowerArm_R=(-35, 0, 0)), (0, 0.02, -0.165)),
        (18, P(UpperLeg_L=(10, 0, 0), UpperLeg_R=(-12, 0, 0), LowerLeg_L=(42, 0, 0), LowerLeg_R=(34, 0, 0), Foot_L=(32, 0, 0), Foot_R=(32, 0, 0), Spine=(-13, 0, 0), Chest=(-9, 0, 0), Neck=(-12, 0, 0), Head=(-12, 0, 0),
               UpperArm_L=(-55, -28, 0), UpperArm_R=(-55, 28, 0), LowerArm_L=(-70, 0, 0), LowerArm_R=(-70, 0, 0)), (0, 0, 0.30)),
        (22, P(UpperLeg_L=(-6, 0, 0), UpperLeg_R=(-22, 0, 0), LowerLeg_L=(48, 0, 0), LowerLeg_R=(44, 0, 0), Foot_L=(30, 0, 0), Foot_R=(30, 0, 0), Spine=(11, 0, 0), Chest=(9, 0, 0), Neck=(20, 0, 0), Head=(22, 0, 0),
               UpperArm_L=(8, -34, 0), UpperArm_R=(8, 34, 0), LowerArm_L=(-55, 0, 0), LowerArm_R=(-55, 0, 0)), (0, -0.03, 0.27)),
        (31, P(UpperLeg_L=(-34, 0, 0), UpperLeg_R=(-34, 0, 0), LowerLeg_L=(62, 0, 0), LowerLeg_R=(62, 0, 0), Foot_L=(-20, 0, 0), Foot_R=(-20, 0, 0), Spine=(14, 0, 0), Chest=(4, 0, 0), Head=(-6, 0, 0),
               UpperArm_L=(-12, 4, 0), UpperArm_R=(-12, -4, 0), LowerArm_L=(-45, 0, 0), LowerArm_R=(-45, 0, 0)), (0, -0.05, -0.095)),
        (43, READY, (0, -0.05, -0.012))]),
}


def make_actions(arm):
    """Create one Action per motion on the armature and stash them on NLA tracks (so glTF exports all of them)."""
    sc = bpy.context.scene; sc.render.fps = FPS; arm.animation_data_create(); made = {}
    for name, spec in ACTIONS.items():
        act = bpy.data.actions.new('TM_HM55_' + name); arm.animation_data.action = act; prev = {}
        for frame, pose, loc in spec['keys']:
            frame = frame - 1                                   # clips start at frame 0 (time 0 in glTF)
            ha.set_pose(arm, pose, location=loc)
            for pb in arm.pose.bones:
                q = pb.rotation_quaternion.copy()
                if pb.name in prev and prev[pb.name].dot(q) < 0:
                    q.negate(); pb.rotation_quaternion = q
                prev[pb.name] = q; pb.keyframe_insert('rotation_quaternion', frame=frame)
                if pb.name == 'Hips':
                    pb.keyframe_insert('location', frame=frame)
        act['hm55_provenance'] = 'Original keyframed motion authored in hm_anim.py; speed is an authored estimate.'; act['hm55_loop'] = bool(spec['loop']); act.use_fake_user = True
        made[name] = {'frames': [int(spec['keys'][0][0]) - 1, int(spec['keys'][-1][0]) - 1], 'seconds': round((spec['keys'][-1][0] - spec['keys'][0][0])/FPS, 3), 'loop': spec['loop'], 'keys': len(spec['keys'])}
    arm.animation_data.action = None
    for name in ACTIONS:
        act = bpy.data.actions['TM_HM55_' + name]; tr = arm.animation_data.nla_tracks.new(); tr.name = act.name; tr.strips.new(act.name, int(act.frame_range[0]), act); tr.mute = True
    ha.set_pose(arm, {})
    return made


def apply_action_frame(arm, name, frame):
    """Evaluate one action at a frame (for renders / verification)."""
    arm.animation_data.action = bpy.data.actions['TM_HM55_' + name]; bpy.context.scene.frame_set(int(frame)); bpy.context.view_layer.update()
