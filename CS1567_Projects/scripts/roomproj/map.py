#!/usr/bin/env python
import sys
import roslib
import rospy
import cv2
import copy
import math
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from cmvision.msg import Blobs, Blob
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion
from geometry_msgs.msg import Twist
from std_msgs.msg import Empty
from kobuki_msgs.msg import BumperEvent
from struct import *

pub = rospy.Publisher("kobuki_command", Twist, queue_size=10)
command = Twist()

depthData = Image();
isDepthReady = False;

degree = 0
x = 0
y = 0
stop = 0
def robostop(data):
    global stop
    if data.linear.x == 1:
        stop = 1
    if data.linear.x == -1:
        stop = -1
def resetter():
    pub = rospy.Publisher('/mobile_base/commands/reset_odometry', Empty, queue_size = 10)
    degree = 0
    x = 0
    while pub.get_num_connections() == 0:
        pass
    pub.publish(Empty())

def odomCallback(data):
    # Convert quaternion to degree
    global degree, x, y
    q = [data.pose.pose.orientation.x,
         data.pose.pose.orientation.y,
         data.pose.pose.orientation.z,
         data.pose.pose.orientation.w]
    roll, pitch, yaw = euler_from_quaternion(q)
    # roll, pitch, and yaw are in radian
    degree = yaw * 180 / math.pi
    x = data.pose.pose.position.x
    y = data.pose.pose.position.y
#    print data.pose.pose.position.x
weight_dict = {}


class Vertex:
    def __init__(self, node):
        self.id = node
        self.adjacent = {}
        # Set distance to infinity for all nodes
        self.distance = sys.maxint
        # Mark all nodes unvisited        
        self.visited = False  
        # Predecessor
        self.previous = None

    def add_neighbor(self, neighbor, weight):
        self.adjacent[neighbor] = weight
        

    def get_connections(self):
        return self.adjacent.keys()  

    def get_id(self):
        return self.id

    def get_weight(self, neighbor):

        return self.adjacent[neighbor]

    def set_distance(self, dist):
        self.distance = dist

    def get_distance(self):
        return self.distance

    def set_previous(self, prev):
        self.previous = prev

    def set_visited(self):
        self.visited = True

    def __str__(self):
        return str(self.id) + ' adjacent: ' + str([x.id for x in self.adjacent])

class Graph:
    def __init__(self):
        self.vert_dict = {}
        self.num_vertices = 0


    def __iter__(self):
        return iter(self.vert_dict.values())

    def add_vertex(self, node):
        self.num_vertices = self.num_vertices + 1
        new_vertex = Vertex(node)
        self.vert_dict[node] = new_vertex
        return new_vertex

    def get_vertex(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, frm, to, cost):
        if frm not in self.vert_dict:
            self.add_vertex(frm)
        if to not in self.vert_dict:
            self.add_vertex(to)
        weight_dict[frm + to] = cost
        weight_dict[to + frm] = cost
        self.vert_dict[frm].add_neighbor(self.vert_dict[to], cost)
        self.vert_dict[to].add_neighbor(self.vert_dict[frm], cost)

    def get_vertices(self):
        return self.vert_dict.keys()


    def set_previous(self, current):
        self.previous = current

    def get_previous(self, current):
        return self.previous

def shortest(v, path):
    ''' make shortest path from v.previous'''
    if v.previous:
        path.append(v.previous.get_id())
        shortest(v.previous, path)
    return

import heapq

def dijkstra(aGraph, start, target):
    print '''Dijkstra's shortest path'''
    # Set the distance for the start node to zero 
    start.set_distance(0)

    # Put tuple pair into the priority queue
    unvisited_queue = [(v.get_distance(),v) for v in aGraph]
    heapq.heapify(unvisited_queue)

    while len(unvisited_queue):
        # Pops a vertex with the smallest distan


        uv = heapq.heappop(unvisited_queue)
        current = uv[1]
        current.set_visited()

        #for next in v.adjacent:
        for next in current.adjacent:
            # if visited, skip
            if next.visited:
                continue
            new_dist = current.get_distance() + current.get_weight(next)
            
            if new_dist < next.get_distance():
                next.set_distance(new_dist)
                next.set_previous(current)
                print 'updated : current = %s next = %s new_dist = %s' \
                        %(current.get_id(), next.get_id(), next.get_distance())
            else:
                print 'not updated : current = %s next = %s new_dist = %s' \
                        %(current.get_id(), next.get_id(), next.get_distance())


        # Rebuild heap
        # 1. Pop every item
        while len(unvisited_queue):
            heapq.heappop(unvisited_queue)
        # 2. Put all vertices not visited into the queue
        unvisited_queue = [(v.get_distance(),v) for v in aGraph if not v.visited]
        heapq.heapify(unvisited_queue)
    
def depthCallback(data):
    global depthData, isDepthReady
    depthData = data
    isDepthReady = True

path = []
g = Graph()
def initgraph():
    global path, g
    g.add_vertex('start')
    g.add_vertex('5806')
    g.add_vertex('5808')
    g.add_vertex('inter1')
    g.add_vertex('5801')
    g.add_vertex('brcorn')
    g.add_vertex('5414')
    g.add_vertex('5412')
    g.add_vertex('5411')
    g.add_vertex('5409')
    g.add_vertex('5406')
    g.add_vertex('5404')
    g.add_vertex('5403')
    g.add_vertex('trcorner')
    g.add_vertex('5401')
    g.add_vertex('5329')
    g.add_vertex('5327')
    g.add_vertex('5325')
    g.add_vertex('tmcorner')
    g.add_vertex('5321')
    g.add_vertex('5519')
    g.add_vertex('5517')
    g.add_vertex('tlcorner')
    g.add_vertex('5502')
    g.add_vertex('5501')
    g.add_vertex('5503')
    g.add_vertex('5505')
    g.add_vertex('5506')
    g.add_vertex('blcorner')
#    print 'ha\n'
    g.add_edge('start', '5806', 0.705 )
    g.add_edge('5806', '5808', 1.6898)  
    g.add_edge('5808', 'inter1', 5.2109)
    g.add_edge('inter1', '5801', 3.685)
    g.add_edge('inter1', 'blcorner', 7.4086)
    g.add_edge('5801', 'brcorn', 8.4841)
    g.add_edge('brcorn', '5414', 4.5090)
    g.add_edge('5414', '5412', 1.7625)
    g.add_edge('5412', '5411', 4.6307)
    g.add_edge('5411', '5409', 1.7677)
    g.add_edge('5409', '5406', 4.7419)
    g.add_edge('5406', '5405', 1.8302)
    g.add_edge('5405', '5403', 3.8791)
    g.add_edge('5403', 'trcorner', .537)
    g.add_edge('trcorner', '5401', 1.0386)
    g.add_edge('trcorner', '5329', 2.8)#guess
    g.add_edge('5329', '5327', 1.7772)
    g.add_edge('5327','5091', 1.829)
    g.add_edge('5091', '5325', 2.4348)
    g.add_edge('5325', 'tmcorner', 4.0) #guess
    g.add_edge('tmcorner', '5321', 1.4)#guess
    g.add_edge('5321', '5324', 0.88)
    g.add_edge('5324', '5319', 4.7677)
    g.add_edge('5319', '5317', 1.89)
    g.add_edge('5317', 'tlcorner', 1.48)
    g.add_edge('tlcorner', '5502', 1.5)#guess
    g.add_edge('5502', '5501', 2.2)
    g.add_edge('5501', '5503', 1.7)
    g.add_edge('5503', '5505', 4.0)   
    g.add_edge('5505', '5506', 2.5)
    g.add_edge('5506', 'blcorner', 7.0)
    print 'Graph data:'
    for v in g:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            print '( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w))
    verta = raw_input('Enter Starting Room')
    vertb = raw_input('Enter Finishing Room')
    dijkstra(g, g.get_vertex(verta), g.get_vertex(vertb)) 

    target = g.get_vertex(vertb)

    path = [target.get_id()]
    shortest(target, path)
    print 'The shortest path : %s' %(path[::-1])


def main():
    global stop, depthData, isDepthReady, path, g, x, y, degree, command, pub, weight_dict
    rospy.init_node('depth_example', anonymous=True)
    rospy.Subscriber("/camera/depth/image", Image, depthCallback, queue_size=10)
    rospy.Subscriber('/odom', Odometry, odomCallback)
    rospy.Subscriber("robotstop", Twist, robostop)
    val = False
    center = degree
    path = path[::-1]
    while not rospy.is_shutdown():
        for i in range(0, len(path)-1):
            resetter()
            rospy.sleep(.1)
            weigh = weight_dict[path[i] + path[i+1]]
	    command.linear.x = 0.3
            pub.publish(command)
#	    center = degree
	    while (x < weigh):
                if y > 0:
                    command.angular.z = -0.01
                    pub.publish(command)
                elif y < 0:
                    command.angular.z = 0.01
                    pub.publish(command)   
                while (stop == 1):
                    command.linear.x = 0
                    command.angular.z = 0
                    pub.publish(command)
                command.linear.x = 0.3
                pub.publish(command)
            command.angular.z = 0
            command.linear.x = 0
            pub.publish(command)
            while (center > degree):
                command.angular.z = 0.1
                pub.publish(command)
            while (center < degree):
                command.angular.z = -0.1
                pub.publish(command)
            command.angular.z = 0
            pub.publish(command)
          #  resetter()
          #  rospy.sleep(.1)
            if ((0 <= i+1) and (i+1 < len(path))):
                val = True
            if ((i < len(path) - 1) and ((path[i] == "5405" and path[i+1] == "trcorner") or (path[i] == "5801" and path[i+1] == "brcorn") or (path[i] == "5801" and path[i+1] == "inter1") or (path[i] == "5506" and path[i+1] == "blcorner") or (path[i] == "5317" and path[i+1] == "tlcorner") or (path[i] == "5403" and path[i + 1] == "trcorner") or (path[i] == "5091" and path[i+1] == "5325") or (path[i] == "5321" and path[i+1] == "tmcorner"))):
                command.angular.z = 0.3
                pub.publish(command)
                while degree < 88.5:
                    pass
                command.angular.z = 0
                pub.publish(command)
            elif ((i < len(path) - 1) and ((path[i] == "5329" and path[i+1] == "trcorner") or (path[i] =="5414" and path[i+1] == "brcorn") or (path[i] == "inter1" and path[i+1] == "blcorner") or (path[i] == "5502" and path[i+1] == "tlcorner") or (path[i] == "5325" and path[i+1] == "tmcorner") or (path[i] == "tmcorner" and path[i+1] == "5325")) or (path[i] == "blcorner" and path[i+1] == "inter1")):
                command.angular.z = -.3
                pub.publish(command)
                while degree > -88.5:
                    pass
                command.angular.z = 0
                pub.publish(command)
            elif(path[i] == "5808" and i < len(path) - 2):
                if(path[i+2] == "blcorner"):
                    command.angular.z = 0.3
                    pub.publish(command)
                    while degree < 88.5:
                        pass
                    command.angular.z = 0
                    pub.publish(command)
 	    	elif(path[i + 2] == "5801"):
		    command.angular.z = -.3
                    pub.publish(command)
                    while degree > -88.5:
                        pass
                    command.angular.z = 0
                    pub.publish(command)
	    resetter()
            while (center > degree + 1):
                command.angular.z = 0.05
                pub.publish(command)
            while (center < degree -1):
                command.angular.z = -0.05
                pub.publish(command)
            command.angular.z = 0
            command.linear.x = 0
            pub.publish(command)
        break    
if __name__ == "__main__":
    while not rospy.is_shutdown():
        initgraph()
        main()
  
           
