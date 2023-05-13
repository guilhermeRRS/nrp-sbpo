def commit_singleMany(self, move):

    self.penalties.demand = move["nD"]
    self.penalties.preference_total = move["nP"]

    self.penalties.total = self.penalties.demand + self.penalties.preference_total
    
    lnurses = len(move["ns"])
    day = move["d"]
    newShifts = move["s"]

    for i in range(lnurses):
        nurse = move["ns"][i]

        oldShift = self.helperVariables.projectedX[nurse][day]
        newShift = newShifts[i]

        self.nurseModel.model.x[nurse][day][oldShift].lb = 0
        self.nurseModel.model.x[nurse][day][oldShift].ub = 0
        
        self.nurseModel.model.x[nurse][day][newShift].lb = 1
        self.nurseModel.model.x[nurse][day][newShift].ub = 1

        self.helperVariables.projectedX[nurse][day] = newShift


        self.helperVariables.shiftTypeCounter[nurse][oldShift] -= 1
        self.helperVariables.workloadCounter[nurse] -= self.nurseModel.data.parameters.l_t[oldShift]
        self.penalties.numberNurses[day][oldShift] -= 1

        self.helperVariables.shiftTypeCounter[nurse][newShift] += 1
        self.helperVariables.workloadCounter[nurse] += self.nurseModel.data.parameters.l_t[newShift]
        self.penalties.numberNurses[day][newShift] += 1