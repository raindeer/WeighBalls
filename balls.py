# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 18:25:28 2015

@author: Erik Rehn
"""

import json
import itertools
from collections import OrderedDict
import numpy as np

NUM_BALLS = 20
NUM_MEASUREMENTS = 4

SCALE_LEFT = -1
SCALE_RIGHT = 1
SCALE_BALANCED = 0
SCALE_RESULT_LABELS = {SCALE_LEFT:'>', SCALE_BALANCED:'=', SCALE_RIGHT:'<'}
LH = 0
L = 1
H = 2
N = 3

def updateKnowledge(left, right, result, knowledge):
  
  newKnowledge = np.copy(knowledge)
  
  if result != SCALE_BALANCED:

    # If the scale is unbalanced we know that all that 
    # were not on the scale are normal
    notOnScale = knowledge - (left + right)
    newKnowledge -= notOnScale
    newKnowledge[N] += notOnScale.sum()
    
    if result == SCALE_LEFT:
      # All light on the left side must be normal
      newKnowledge[L] -= left[L]
      newKnowledge[N] += left[L]
      # All light or heavy on the left can only be heavy
      newKnowledge[LH] -= left[LH]
      newKnowledge[H] += left[LH]
      # All heavy on the right must be normal
      newKnowledge[H] -= right[H]
      newKnowledge[N] += right[H]
      # All heavy or light on the right must be light
      newKnowledge[LH] -= right[LH]
      newKnowledge[L] += right[LH]
      
    elif result == SCALE_RIGHT:
      newKnowledge[H] -= left[H]
      newKnowledge[N] += left[H]
      newKnowledge[LH] -= left[LH]
      newKnowledge[L] += left[LH]
      
      newKnowledge[L] -= right[L]
      newKnowledge[N] += right[L]
      newKnowledge[LH] -= right[LH]
      newKnowledge[H] += right[LH]
        
  else:
    # If the scale is balanaced everything on the scale must be normal
    newKnowledge -= left
    newKnowledge -= right
    newKnowledge[N] += left.sum()
    newKnowledge[N] += right.sum()
    
  return newKnowledge


def generateScaleSettings(knowledge):
  
  if (knowledge.sum() != NUM_BALLS):
    print "Invalid knowledge state"
  
  def pickBalls(notOnScale, ballCount):
    #print "pickBalls", notOnScale, ballCount
    if notOnScale.sum() == ballCount:
      balls = notOnScale.copy()
      notOnScale[:] = 0
      yield balls
      notOnScale += balls
      return
      
    balls = np.zeros(4, np.int8)

    for ballsToPick, startDim in itertools.product(range(1, ballCount+1), range(4)):
      pickedBalls = 0
      
      dim = startDim
      #print ballsToPick, dim, notOnScale
      while balls.sum() < ballCount: 
        
        if pickedBalls == ballsToPick:
          dim += 1
          if dim > 3: 
            dim = 0
            
        while notOnScale[dim] == 0:
          dim += 1
          if dim > 3: 
            dim = 0
            
        balls[dim] += 1
        notOnScale[dim] -= 1
        pickedBalls += 1
    
      yield balls
      notOnScale += balls
      balls[:] = 0
      pickedBalls = 0
  
  notOnScale = np.copy(knowledge)
  
  prevLeft = np.zeros(4)
  prevRight = np.zeros(4)
 
  for ballCount in range(1, NUM_BALLS/2+1):
    for left in pickBalls(notOnScale, ballCount):
      for right in pickBalls(notOnScale, ballCount):
        if not (prevLeft==left).all() or not (prevRight==right).all():
          #print left, "vs", right, ", Not on scale: ", notOnScale, ballCount
          yield left, right, notOnScale, ballCount
          prevLeft = left
          prevRight = right


def measure(knowledge, m = 1):
  
  solutionFound = np.zeros(3, np.int8)
  
  # Iterate over all possible ball configurations given the knowledge we have
  
  for left, right, notOnScale, ballCount in generateScaleSettings(knowledge):
    
    solutionFound[:] = 0
    
    # Generate the possible results of the mesurement (left/right/balanced) 
    # given what we know of what we have in the left and right cup.
    # Note: if the left and right side are equal we only need to evaluate
    # one of the unbalanced cases since the solution then is symmetric.
    
    scaleResults = []
    
    if left[LH] > 0 or left[H] > 0 or right[LH] > 0 or right[L] > 0:
      scaleResults.append(SCALE_LEFT)
    
    if ((right[LH] > 0 or right[H] > 0 or left[LH] > 0 or left[L] > 0) and 
         not (left == right).all()):
      scaleResults.append(SCALE_RIGHT) # Only add if left != right
    
    if notOnScale[0:3].sum() > 0:
      scaleResults.append(SCALE_BALANCED)
    
    solutions = {}
    
    for i, scaleResult in enumerate(scaleResults):
      
      # Update the knowledge we have given the balls on the scale, the
      # scale position/result, and the current knowledge.     
      newKnowledge = updateKnowledge(left, right, scaleResult, knowledge)
      
      # Have we found a solution for this scale result?
      if newKnowledge[N] == NUM_BALLS-1:
          solutionFound[i] = 1
          solutions[SCALE_RESULT_LABELS[scaleResult]] = "Result:" + str(list(newKnowledge))
      elif m != NUM_MEASUREMENTS:
        # Recusivly call measure() to do the next measurement
        solutionFound[i], solution = measure(newKnowledge, m + 1)
        solutions[SCALE_RESULT_LABELS[scaleResult]] = solution
        
    # If we found a solution for all scale results, return it
    if solutionFound.sum() == len(scaleResults):
      return 1, OrderedDict([('knowledge', str(list(knowledge))), 
                             ('left', str(list(left))), 
                             ('right',  str(list(right))), 
                             (str(m),  solutions)])
    
  return 0, None
    
    
print "Start ---"
print "Number of balls:", NUM_BALLS
print "Number of measurments:", NUM_MEASUREMENTS

initialKnowledge = np.array([NUM_BALLS, 0, 0, 0], np.int8)
solutionFound, solution = measure(initialKnowledge)

if solutionFound == 1:
  print "\nSolution:"
  print json.dumps(solution, indent=2)
else:
  print "\nNo solution was found..."
  

