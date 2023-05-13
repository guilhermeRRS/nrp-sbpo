def main_runSingle(self):
    
    numberOfIters = 2*self.nurseModel.I*self.nurseModel.D*self.nurseModel.T
    while self.chronos.stillValidRestrict():
        numberSuccess = 0
        for i in range(numberOfIters):
            s, move = self.run_single(worse = False, better = True, equal = False)
            
            if s:
                self.commit_single(move)
                numberSuccess += 1
                
            if not self.chronos.stillValidRestrict():
                break

        print(numberSuccess)
        if numberSuccess < 0.001*numberOfIters:
            break

def main_runSingleMany(self, numberOfNurses:int):

    numberOfIters = 2*numberOfNurses*self.nurseModel.I*self.nurseModel.D*self.nurseModel.T
    while self.chronos.stillValidRestrict():
        numberSuccess = 0
        for i in range(numberOfIters):
            s, move = self.run_singleMany(numberOfNurses = numberOfNurses, worse = False, better = True, equal = False)
            
            if s:
                self.commit_singleMany(move)
                numberSuccess += 1
                
            if not self.chronos.stillValidRestrict():
                break

        print(numberSuccess)
        if numberSuccess < 0.001*numberOfIters:
            break


def main_teste(self):
    
    while self.chronos.stillValidRestrict():
        rangeOfSequences = 2
        s, move = self.run_seqNurseFromModel(numberOfNurses = 5, rangeOfSequences = rangeOfSequences, worse = False, better = True, equal = False)
        
        if s:
            self.commit_sequenceMany(move)
            print(self.penalties.total)
            #numberSuccess += 1
        else:
            print(".")
        
    #if not self.chronos.stillValidRestrict():
    #    break