#!/usr/bin/env python
'''
@package middle-ware package to communicate with graspit and convert it to ros message
'''

import roslib
roslib.load_manifest( "graspit_python_node" )
import rospy
import socket, time
import graspit_msgs.msg
import geometry_msgs.msg
import tf, tf_conversions, tf.transformations
from numpy import pi, eye, dot, cross, linalg, sqrt, ceil, size
from numpy import hstack, vstack, mat, array, arange, fabs
import pdb
from graspit_commands import *


#def main():
#   pass




#if __name__ == "__main__":
#    main()

test_string = '{0.588131 0.742387 -0.160745 -0.277714 -109.514 48.7265 10.208 0 1.58644 0.690816 0.783941 -5.38901e+305 -5.38901e+305,}\n'

class graspit_barrett_params(object):
    def __init__(self, grasp_pose_list, grasp_joints_list, quality_scores):
        self.spread_angle = grasp_joints_list[-1]
        self.finger_1 = grasp_joints_list[0]
        self.finger_2 = grasp_joints_list[1]
        self.finger_3 = grasp_joints_list[2]
        self.joint_angles = [self.spread_angle, self.finger_1, self.finger_2, self.finger_3]
        self.grasp_pose = geometry_msgs.msg.Pose( grasp_pose_list[:3] , tf_conversions.Quaternion(w = grasp_pose_list[3], x = grasp_pose_list[4], y = grasp_pose_list[5], z = grasp_pose_list[6]))
        self.quality_scores = quality_scores
        
        
class graspit_barrett_grasp(object):
    def __init__(self, pre_grasp_grasp, final_grasp_grasp):
        self.pre_grasp = pre_grasp_grasp
        self.final_grasp = final_grasp_grasp

    def get_quality(self):
        return self.final_grasp.quality_scores

    def get_pregrasp_qualities(self):
        return self.pre_grasp.quality_scores

    def to_grasp_msg(self):
        return graspit_msgs.msg.Grasp(
                  pre_grasp_pose = self.pre_grasp.pose,
                  final_grasp_pose = self.final_grasp.pose,
                  pre_grasp_dof = self.pre_grasp.joint_angles,
                  final_grasp_dof = self.final_grasp.joint_angles,
                  grasp_source = 0,
                  epsilon_quality = self.final_grasp.quality_scores[0],
                  volume_quality = self.final_grasp.quality_scores[1],
                  secondary_qualities = self.final_grasp.quality_scores[2:]
            )
    
                                      
            
                                      

def parse_db_grasp_string(grasp_string):
    unstructured_grasp_list = [x.lstrip('[').split(',') for x in grasp_string.rstrip('{').lstrip('}').split(']')]
    def grasp_list_to_barrett_grasp(grasp_item_list):
        return graspit_barrett_params(grasp_item_list[:4], grasp_item_list[4:8], grasp_item_list[8:])

    structured_grasp_list = [grasp_list_to_barrett_grasp(x) for x in unstructured_grasp_list]
    full_structured_grasp_list = [graspit_barret_grasp(structured_grasp_list[ind], structured_grasp_list[ind+1]) for x in range(0,len(pregrasp_grasp_list),2)]  
    return full_structured_grasp_list

        
def parse_unstructured_grasp_string(grasp_string):
    #clean the string from extraneous characters    
    gs = grasp_string.strip('{').rstrip('\n').rstrip('}').rstrip(',')
    grasp_list = gs.split(',')
    g = list()
    for grasp in grasp_list:
        #split into unstructured list
        gs_list = grasp.split(' ')
        #extract grasp fields
        quat_list = [float(x) for x in gs_list[0:4]]
        tran_list = [float(x) for x in gs_list[4:7]]
    
        dof_list = [float(x) for x in gs_list[7:11]]
        epsilon_quality = float(gs_list[11])
        volume_quality = float(gs_list[12])
        quality_list = []
        if len(gs_list) > 13:
            quality_list = [float(x) for x in gs_list[13:-1]]
    
        q = geometry_msgs.msg.Quaternion(w = quat_list[0], x = quat_list[1], y = quat_list[2], z = quat_list[3])
        p = geometry_msgs.msg.Point(x = tran_list[0], y = tran_list[1], z = tran_list[2])
        grasp_pose_msg = geometry_msgs.msg.Pose(orientation = q, position = p)
        g.append(graspit_msgs.msg.Grasp(epsilon_quality = epsilon_quality, pre_grasp_pose = grasp_pose_msg, final_grasp_pose = grasp_pose_msg, pre_grasp_dof = dof_list, final_grasp_dof = dof_list, secondary_qualities = [0.0]))
        
    return g
        
    
    

class GraspitExecutionListener( object ):
    def __init__(self, hostname):
        self.socket = socket.socket()
        self.socket.connect(hostname)        
        self.grasp_pub = rospy.Publisher('/graspit/grasps', graspit_msgs.msg.Grasp)
        self.graspit_commander = graspitManager(self.socket)
        self.graspit_commander.connect_world_planner()
        self.transform_listener = tf.TransformListener()
        
        
    def try_read(self):
        received_string = self.socket.recv(4096)
        #try:
        grasp_msg = parse_unstructured_grasp_string(received_string)
        self.grasp_pub.publish(grasp_msg[0])
        #except Exception as e:
        #    print e
        return received_string, grasp_msg

    def update_table(self):
        try:
            trans = tf_conversions.toMatrix(tf_conversions.fromTf(self.transform_listener('world','object', rospy.Time(0))))
            self.graspit_commander.set_body_trans('experiment_table', trans)

        except:
            pass
        


 if __name__ == '__main__':
     try:
         rospy.init_node('graspit_python_server')
         g = GraspitExecutionListener(('tonga.cs.columbia.edu',4765))
         g.graspit_commander.get_graspit_objects()
         table_ind = g.object_ind('experiment_table')
         if not table_ind:
             g.add_obstacle('experiment_table')            
         loop = rospy.Rate(10)
         while not rospy.is_shutdown():
             s,grasp_msg = g.try_read()
             g.update_table()
             print grasp_msg
             loop.sleep()
     except rospy.ROSInterruptException: pass
    
            




                        
