"""
This is an example file for prepraing Bodytrack for RAPID(C)
"""

from Classes import *  # import the parent class and other classes from the file Classes.py


class appMethods(AppMethods):
    database_path = "/home/liuliu/Research/mara_bench/parsec-3.0/pkgs/apps/ferret/run/corel/"
    table="lsh"
    query_path="/home/liuliu/Research/mara_bench/parsec-3.0/pkgs/apps/ferret/run/queries"

    def cleanUpAfterEachRun(self, configs=None):
        # backup the generated output to another location
        itr = 25
        hash = 8
        probe = 20
        self.training_units = 20
        if configs is not None:
            for config in configs:
                name = config.knob.set_name
                if name == "hash":
                    hash = config.val  # retrieve the setting for each knob
                elif name == "probe":
                    probe = config.val  # retrieve the setting for each knob
                elif name == "itr":
                    itr = config.val  # retrieve the setting for each knob

        self.moveFile("output.txt",
                      "./training_outputs/output_" + str(hash) + "_" + str(probe) + "_"+str(itr)+".txt")

    def afterGTRun(self):
        self.gt_path = "./training_outputs/grountTruth.txt"
        output_path = "output.txt"
        self.moveFile(output_path, self.gt_path)

    # helper function to assembly the command
    def getCommand(self, configs=None):
        itr = 25
        hash = 8
        probe = 20
        if configs is not None:
            for config in configs:
                name = config.knob.set_name
                if name == "hash":
                    hash = config.val  # retrieve the setting for each knob
                elif name == "probe":
                    probe = config.val  # retrieve the setting for each knob
                elif name == "itr":
                    itr = config.val  # retrieve the setting for each knob
        return [self.obj_path,
                self.database_path,
                self.table, self.query_path,
                "50",
                "20",
                "1",
                "output.txt",
                '-l',
                str(hash),
                '-t',
                str(probe),
                '-itr',
                str(itr)]

    def rank(self, img, imglist):
        if img in imglist:
            return imglist.index(img) + 1
        return 0

    def compute1(self, list1, imgset):
        res = 0
        for img in imgset:
            res += self.rank(img, list1)
        return res

    def compute2(self, list1, list2, imgset):
        res = 0
        for img in imgset:
            res += abs(self.rank(img, list1) - self.rank(img, list2))
        return res

    # helper function to evaluate the QoS
    def getQoS(self):
        truth = open(self.gt_path, "r")
        mission = open("./output.txt", "r")
        truthmap = {}
        missionmap = {}
        truth_res = []
        mission_res = []
        for line in mission:
            col = line.split('\t')
            name = col[0].split("/")[1]
            missionmap[name] = []
            for i in range(1, len(col)):  # 50 results
                missionmap[name].append(col[i].split(':')[0])
        for line in truth:
            col = line.split('\t')
            name = col[0].split("/")[1]
            if name not in missionmap:
                continue
            truthmap[name] = []
            for i in range(1, len(col)):  # 50 results
                truthmap[name].append(col[i].split(':')[0])

        # now that 2 maps are set, compare each item
        # setup the Z / S/ and T
        Z = set()
        S = set()
        T = set()
        toterr = 0.0
        totimg = 0
        for query_image in truthmap:
            totimg += 1
            truth_res = truthmap[query_image]
            mission_res = missionmap[query_image]
            # compute the worst case senario, where Z = empty
            maxError = ((1 + len(truth_res)) * len(truth_res) / 2) * 2
            # setup S and T
            S.update(truth_res)
            T.update(mission_res)
            Z = S & T  # Z includes images both in S and T
            # clear S and T
            for s in Z:
                T.remove(s)
                S.remove(s)
            # now that Z, S, and T are set, compute the ranking function
            ranking_res = self.compute2(truth_res, mission_res, Z) - self.compute1(truth_res, S) - self.compute1(mission_res, T)
            ranking_res = abs(float(ranking_res) / float(maxError))
            toterr += 1.0 - ranking_res
            S.clear()
            T.clear()
            Z.clear()
        return (1.0 - (toterr / totimg)) * 100.0