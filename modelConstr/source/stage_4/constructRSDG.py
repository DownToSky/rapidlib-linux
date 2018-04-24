from stage_1.training import *
from Classes import *
from representset import *
from piecewiseProb import *
from quadProb import *

# contains functions to compute the representative list of a RSDG, given the fact profile
def constructRSDG(gt, knob_samples, threshold, knobs, PRINT,model):
    # gT is a dictionary where entry is the config and value is hte cost
    # profile_configs is the structured configuration
    # segmentation level
    seglvl = 0
    # initial error rate set to 100%
    error = 1.0
    while error>=threshold:
        if seglvl >= 4:
            print "Reached Highest Segmentation Granularity"
            break
        seglvl += 1
        partitions = partition(seglvl,knob_samples)
        observed_profile = retrieve(partitions, gt, knobs)
        costrsdg,mvrsdg = populate(observed_profile,partitions,model)
        error = compare(costrsdg,gt,False,model)
    if PRINT:
        compare(costrsdg,gt,True)
        print "Granulatiry = "+ str(seglvl)
    return costrsdg,mvrsdg

# given a partion level, return a list of configurations
def partition(seglvl, knob_samples):
    partitions = {}
    #seglvl indicate the number of partition lvl on each knob
    for knob in knob_samples:
        val_range = knob_samples[knob]
        length = len(val_range)
        partitions[knob] = []
        max = length-1
        min = 0
        # determine the step size
        num_of_partitions = 2**(seglvl-1)
        step = length / num_of_partitions - 1
        if step<1:
            step = 1
        for i in range(min,max+1,step):
            partitions[knob].append(val_range[i])
        #extend the last one to the end
        length = len(partitions[knob])
        partitions[knob][length-1]=val_range[max]
    return partitions

# given a partition list, retrieve the data points in ground truth
# return a profile by observation
def retrieve(partitions, gt, knobs):
    observed_profile = Profile()
    final_sets = set()
    # partitions contains a dictionary of all knob samples
    for knob in partitions:
        samples = partitions[knob]
        single_set = []
        for sample in samples:
            single_set.append(Config(knobs.getKnob(knob),sample))
        final_sets.add(frozenset(single_set))
    product = crossproduct(final_sets)
    flatted_observed = flatAll(product)
    for config in flatted_observed:
        configuration = Configuration()
        configuration.addConfig(config)
        # filter out the invalid config, invalid if not present in groundTruth
        if not gt.hasEntry(configuration):
            continue
        costval = gt.getCost(configuration)
        mvval = gt.getMV(configuration)
        observed_profile.addCostEntry(configuration, costval)
        observed_profile.addMVEntry(configuration,mvval)
    return observed_profile

# given an observed profile, generate the continuous problem and populate the rsdg
def populate(observed,partitions,model):
    if model=="piecewise":
        return populatePieceWiseRSDG(observed,partitions)

def compare(rsdg,groundTruth,PRINT,model):
   if model=="piecewise":
       return modelValid(rsdg,groundTruth,PRINT)

def generateContProblem(observed, partitions, model, COST=True):
    if model=="piecewise":
        return generatePieceWiseContProblem(observed,partitions,COST)
    if model=="quad":
        return generateQuadContProblem(observed,partitions,model,COST)