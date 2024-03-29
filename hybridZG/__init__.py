# coding=utf-8
import json
import math
from chronos import Chronos
from model import NurseModel, Solution, GurobiOptimizedOutput
from typing import List, Dict, NewType
import random
import gurobipy as gp
from gurobipy import GRB

ORIGIN_SOLVER = "ORIGIN_SOLVER"
START_OPTIMIZE = "START_OPTIMIZE"

SOLVER_GUROBI_OUTPUT = "SOLVER_GUROBI_OUTPUT"
SOLVER_ITERATION_NO_SOLUTION = "SOLVER_ITERATION_NO_SOLUTION"
SOLVER_ITERATION_NO_TIME = "SOLVER_ITERATION_NO_TIME"

OneDimInt = NewType("oneDimInt", List[int])
TwoDimInt = NewType("twoDimInt", List[List[int]])
TwoDimVar = NewType("twoDimVar", List[List[gp.Var]])
ThreeDimInt = NewType("threeDimInt", List[List[List[int]]])
ThreeDimVar = NewType("threeDimVar", List[List[List[gp.Var]]])

class penalties:

    numberNurses: TwoDimInt
    demand: int
    preference_total: int

    total: int
    best: int

class tmp:

    zero = 0

class HelperVariables:

    shiftTypeCounter: TwoDimInt
    workloadCounter: OneDimInt
    weekendCounter: TwoDimInt #yes, this is the same as K variable
    projectedX: TwoDimInt

    oneInnerJourney_rt: Dict[int, Dict[int, OneDimInt]]
    twoInnerJourney_rt: Dict[int, Dict[int, TwoDimInt]]

class Hybrid:

    nurseModel: NurseModel
    chronos: Chronos
    helperVariables: HelperVariables
    currentSol: Solution

    #####utils
    from .utils._prePro import preProcessFromSolution
    from .utils._forShifts import computeLt, computeWorkloadNewSeq, shiftFreeMark, shiftFreeUnMark
    from .utils._forShifts import getSequenceWorkMarks, getRangeRewrite

    #####prepare
    from .prepare._calculateHelper import calculateHelper
    from .prepare._setSolToX import solToX
    from .prepare._setSolToParallel import solToParallel
    from .prepare._setBestSolToX import bestSolToX
    from .prepare._setBestAsCurrent import setBestAsCurrent
    
    #####generators
    from .generators._generateSingleNurseModel import generateSingleNurseModel
    from .generators._generateShiftModel import generateShiftModel

    ####maths
    from .maths._forSingle import math_single, math_single_demandDelta
    from .maths._forSingle import math_single_preferenceDelta, math_single_preference
    from .maths._forSingle import math_single_demandDelta, math_single_demand

    from .maths._forSingleMany import math_singleMany, math_singleMany_demand

    from .maths._forSeq import math_sequence
    from .maths._forSeqMany import math_seqMany

    #####options
    from .getters._forSingle import getSingle

    #####fo
    from .foEvaluate._simple import evaluateFO

    #####run
    from .runs._run_single import run_single
    from .runs._run_singleMany import run_singleMany, investigate_singleMany

    from .runs._run_seqFromModel import run_seqFromModel
    from .runs._run_seqNursesFromModel import run_seqNursesFromModel

    from .runs._internal_run_seqFromModel_fixed import internal_run_seqFromModel_fixed

    #####commits
    from .commits._commit_single import commit_single
    from .commits._commit_singleMany import commit_singleMany
    from .commits._commit_seq import commit_sequence
    from .commits._commit_seqMany import commit_sequenceMany

    #####main runner
    from ._mainRunner import main_runSingle, main_runSingleMany, main_seqFromModel,  main_seqNursesFromModel

    from ._manager import startSeqs, startSingles, manager_singleDeep, manager_singleSearch, run_internal_innerFix, run_internal_dayInnerFix, run_internal_dayDayInnerFix, run_internal_all

    def __init__(self, nurseModel: NurseModel, instance, chronos: Chronos):
        
        self.nurseModel = nurseModel
        self.instance = instance
        self.chronos = chronos
        self.helperVariables = HelperVariables()
        self.penalties = penalties()
        self.tmp = tmp()

    
    def run(self, startObj, numberOfNurses_fixDay = 5, numberOfNurses_fixNurse = 2, numberOfDays = 12):
        
        if numberOfNurses_fixDay < 1:
            numberOfNurses_fixDay = math.ceil(numberOfNurses_fixDay*self.nurseModel.I)
        if numberOfNurses_fixNurse < 1:
            numberOfNurses_fixNurse = math.ceil(numberOfNurses_fixNurse*self.nurseModel.I)
        if numberOfDays < 1:
            numberOfDays = 12 + math.ceil(numberOfDays*self.nurseModel.W)
        numberOfDays = min(numberOfDays, self.nurseModel.D)

        m = self.nurseModel.model.m
        self.startObj = startObj
        self.currentObj = startObj
        self.chronos.startCounter("SETTING_START")
        self.preProcessFromSolution()
        #self.SA_shift_model, self.SA_sm_x, self.SA_preference_total, self.SA_demand = self.generateShiftModel()
        self.chronos.stopCounter()
        print("Start working")
        
        m.setParam('OutputFlag', 0)

        keepFix = True
        
        self.nurseModel.model.m.setParam("MIPGap", 1/100)
        self.nurseModel.model.m.setParam("MIPFocus", 2)

        numberTries = 0
        
        runRandom = False

        while self.chronos.stillValid() and keepFix:
            
            begginBest = self.penalties.best

            if True:
                if runRandom:
                    for i in range(max(1, math.ceil(0.5*self.nurseModel.I/numberOfNurses_fixNurse))):
                        if not self.chronos.stillValid():
                            break
                        print("--> ",i)
                        time = max(min(120+numberTries*24, self.chronos.timeLeft()), 1)
                        self.run_internal_innerFix(time, numberOfNurses_fixNurse)
                        
                    tmpBest = self.penalties.best

                    if begginBest - tmpBest < 200:
                        numberOfNurses_fixNurse += 1
                        numberOfNurses_fixNurse = min(numberOfNurses_fixNurse, self.nurseModel.I)
                        print("Adding fixNurse")

                    for i in range(max(1, math.ceil(0.5*self.nurseModel.I/numberOfNurses_fixDay)*math.ceil(self.nurseModel.D/numberOfDays))):
                        if not self.chronos.stillValid():
                            break
                        print("--> ",i)
                        time = max(min(120+numberTries*24, self.chronos.timeLeft()), 1)
                        self.run_internal_dayDayInnerFix(time, numberOfDays, numberOfNurses_fixDay)

                    
                    if tmpBest - self.penalties.best < 200:
                        numberOfNurses_fixDay += 1
                        numberOfNurses_fixDay = min(numberOfNurses_fixDay, self.nurseModel.I)
                        print("Adding fixDay")

                else:
                    for pos in range(0, self.nurseModel.I, numberOfNurses_fixNurse):
                        if not self.chronos.stillValid():
                            break
                        print("--> ",pos)
                        time = max(min(120+numberTries*24, self.chronos.timeLeft()), 1)
                        self.run_internal_innerFix(time, numberOfNurses_fixNurse, False, pos)

                    tmpBest = self.penalties.best

                    if begginBest - tmpBest < 200:
                        numberOfNurses_fixNurse += 1
                        numberOfNurses_fixNurse = min(numberOfNurses_fixNurse, self.nurseModel.I)
                        print("Adding fixNurse")

                    for posI in range(0, self.nurseModel.I, numberOfNurses_fixDay):
                        if not self.chronos.stillValid():
                            break
                        for posD in range(0,self.nurseModel.D, 7): #NOTICE: HARDCODED OVERLAPPING
                            if not self.chronos.stillValid():
                                break
                            markD = min(posD, self.nurseModel.D-numberOfDays)
                            print("--> ",posI, posD, f"({markD})")
                            time = max(min(120+numberTries*24, self.chronos.timeLeft()), 1)
                            self.run_internal_dayDayInnerFix(time, numberOfDays, numberOfNurses_fixDay, False, markD, posI)

                    if tmpBest - self.penalties.best < 200:
                        numberOfNurses_fixDay += 1
                        numberOfNurses_fixDay = min(numberOfNurses_fixDay, self.nurseModel.I)
                        print("Adding fixDay")

            endBest = self.penalties.best

            if begginBest - endBest < 1:
                print("Got in MIP")
                runRandom = not runRandom
                self.nurseModel.model.m.setParam("BestObjStop", 0)
                self.nurseModel.model.m.setParam("MIPFocus", 2)
                if self.chronos.timeLeft() > 60+numberTries*12:
                    time = max(min(self.chronos.timeLeft(), 60+numberTries*12), 1)
                    self.run_internal_all(time, final = False)
                    
                    print("...", endBest, self.penalties.best)
                    if endBest - self.penalties.best < 1:
                        if numberTries == 5:
                            keepFix = False
                        else:
                            numberTries += 1
                            self.nurseModel.model.m.setParam("MIPGap", 1/10000)
                    else:
                        self.nurseModel.model.m.setParam("MIPGap", 1/100)
                        numberTries = 0
                else:
                    keepFix = False
            else:
                self.nurseModel.model.m.setParam("MIPGap", 1/100)
                numberTries = 0

        self.nurseModel.model.m.setParam("NoRelHeurTime", 0)
        self.nurseModel.model.m.setParam("MIPGap", 1/10000)
        self.nurseModel.model.m.setParam("BestObjStop", 0)
        self.nurseModel.model.m.setParam("MIPFocus", 2)
                
        print("Got in universal improving",keepFix)

        self.run_internal_all(max(self.chronos.timeLeft(), 1))

        ########################################

        ########## HERE WE FINISH THE ALGORITHM IN ORDER TO LATER PRINT, DONT EDIT IT
        ########## THE TIME COST MAY BE REALY SMALL, SO IT IS FIXED A HUGE TIMELIMIT FOR THE SOLVER

        ########################################
        print("-->",self.startObj, self.penalties.best)
        
        m.setParam("TimeLimit", 43200)
        m.setParam("BestObjStop", 0)
        #m.setParam('OutputFlag', 1)
        
        m.update()
        self.chronos.startCounter("START_OPTIMIZE_LAST")
        m.optimize()
        self.chronos.stopCounter()

        gurobiReturn = GurobiOptimizedOutput(m)

        self.chronos.printObj(ORIGIN_SOLVER, SOLVER_GUROBI_OUTPUT, gurobiReturn)

        if gurobiReturn.valid():

            print("||>", m.objVal)

            self.nurseModel.solution = Solution().getFromX(self.nurseModel.model.x)
            #self.nurseModel.solution = Solution().getFromLb(self.nurseModel.model.x)
            #self.nurseModel.solution.printSolution("failed.sol", self.nurseModel.data.sets)
            self.nurseModel.s_solution = True
            return True, self.nurseModel
        
        else:
            self.nurseModel.solution = Solution().getFromLb(self.nurseModel.model.x)
            self.nurseModel.solution.printSolution("failed.sol", self.nurseModel.data.sets)
            self.chronos.printMessage(ORIGIN_SOLVER, SOLVER_ITERATION_NO_SOLUTION, False)
            
        self.chronos.printMessage(ORIGIN_SOLVER, "NOT_ABLE_TO_SAVE", True)
            
        return False, self.nurseModel