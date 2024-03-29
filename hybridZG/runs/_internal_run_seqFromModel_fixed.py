from model import GurobiOptimizedOutput


def internal_run_seqFromModel_fixed(self, nurse:int, day:int, rangeOfSequences:int): #this is random

    x = self.parallelModels[nurse]["x"]
    m = self.parallelModels[nurse]["m"]

    restrictions = []
    workingDays = self.helperVariables.workingDays[nurse]
    freeDays = [i for i, x in enumerate(self.helperVariables.projectedX[nurse]) if x < 0]
    
    restrictions.append(m.addConstr(sum((1 - x[d][t]) for t in range(self.nurseModel.T) for d in workingDays) + sum(x[d][t] for t in range(self.nurseModel.T) for d in freeDays) >= 1))

    dayStart, dayEnd = self.getRangeRewrite(nurse, day, rangeOfSequences)
    for d in range(dayStart, dayEnd+1):
        for t in range(self.nurseModel.T):
            x[d][t].lb = 0
            x[d][t].ub = 1

    if self.chronos.stillValidMIP():

        m.setParam("TimeLimit", self.chronos.timeLeftForVND())
        
        m.update()
        self.chronos.startCounter(f"Internal optinization")
        m.optimize()
        self.chronos.stopCounter()

        gurobiReturn = GurobiOptimizedOutput(m)

        self.chronos.printObj("SEQ_FROM_MODEL", "SOLVER_GUROBI_OUTPUT", gurobiReturn)

        if gurobiReturn.valid():
            newX = []
            for d in range(dayStart, dayEnd+1):
                newX.append(-1)
                for t in range(self.nurseModel.T):
                    if x[d][t].x >= 0.5:
                        newX[-1] = t
                        break
            for d in range(dayStart, dayEnd+1):
                for t in range(self.nurseModel.T):
                    x[d][t].lb = self.currentSol.solution[nurse][d][t]
                    x[d][t].ub = self.currentSol.solution[nurse][d][t]
            for restriction in restrictions:
                m.remove(restriction)
            return True, {"n": nurse, "d": dayStart, "s": newX}
            
        else:
            for restriction in restrictions:
                m.remove(restriction) 
            for d in range(dayStart, dayEnd+1):
                for t in range(self.nurseModel.T):
                    x[d][t].lb = self.currentSol.solution[nurse][d][t]
                    x[d][t].ub = self.currentSol.solution[nurse][d][t]
            return False, None
        
    for restriction in restrictions:
        m.remove(restriction)  
    for d in range(dayStart, dayEnd+1):
        for t in range(self.nurseModel.T):
            x[d][t].lb = self.currentSol.solution[nurse][d][t]
            x[d][t].ub = self.currentSol.solution[nurse][d][t]
    return False, None