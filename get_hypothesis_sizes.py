import numpy as np
# import pandas as pd
import statsmodels
import statsmodels.stats.api as sms
from statsmodels.stats.power import TTestIndPower
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
import harness, obscure_blind
from harness import Results # Needed for pickle loading to work!
from collections import defaultdict

from matplotlib.ticker import AutoMinorLocator

from math import ceil

def get_results_from_file(file):
    return harness.get_object_from_file(file)


def pair_and_accumulate(results):
    pairs = defaultdict(list)
    for key, r in results.items():
        problem, true_hyp, mode, version, observed_perc, unordered_perc, garble_perc, obs_idx = r.problem, r.true_hyp, r.mode, r.version, r.observed_perc, r.unordered_perc, r.garble_perc, r.obs_idx
        # if "logistics_p02" in key:
        #     continue
        # if "logistics_p03" in key:
        #     continue
        if version == "simple":
            # if (unordered_perc, garble_perc) == (0,0):
            #     pairs[(mode, observed_perc, unordered_perc, garble_perc)].append((r, r))
            #     continue
            # key = key.replace("/logistics/", "/logistics1/")
            complex_alt_key = key.replace("/simple_", "/complex_")
            # complex_alt_key = complex_alt_key.replace("/logistics/", "/logistics1/")
            complex_alt = results[complex_alt_key]
            complex_alt.set_obsf(complex_alt_key)
            r.set_obsf(key)
            # print("set obsf: " + key)
            pairs[(mode, observed_perc, unordered_perc, garble_perc)].append((r,complex_alt))
    pairs = dict(pairs)
    return pairs


def get_all_paired_results(filename):
    res = get_results_from_file(filename)
    accum_pairs = pair_and_accumulate(res)
    pairs = []
    for prs in accum_pairs.values():
        pairs.extend(prs)

    # So in cases where no observations were given, we made the indicated goals a range. We later filtered them out.
    # Sorry for the jank...
    pairs = [(them, us) for them, us in pairs if not isinstance(them.indicated, range)]

    # Now filtering out instance of them getting it too perfect for us to improve on
    pairs = [(them, us) for (them, us) in pairs if len(them.indicated) != 1]

    return pairs

if __name__ == '__main__':




    block = get_all_paired_results("block-words-results-with-cpx-base.object")
    grid = get_all_paired_results("easy-ipc-grid-results-with-cpx-base.object")
    nav = get_all_paired_results("easy-grid-navigation-results-with-cpx-base.object")
    log = get_all_paired_results("logistics1-and-2-combined.object")

    block_avg = np.mean([len(them.costs_of_hyps_with_obs) for them, us in block])
    grid_avg = np.mean([len(them.costs_of_hyps_with_obs) for them, us in grid])
    nav_avg = np.mean([len(them.costs_of_hyps_with_obs) for them, us in nav])
    log_avg = np.mean([len(them.costs_of_hyps_with_obs) for them, us in log])

    # print(block_avg, grid_avg, nav_avg, log_avg)

    print("block", block_avg)
    print("grid", grid_avg)
    print("nav", nav_avg)
    print("log ", log_avg)






