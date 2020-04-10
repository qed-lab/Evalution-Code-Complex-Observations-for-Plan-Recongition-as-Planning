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


def accumulate_results(results):

    accumulation = defaultdict(list) # setting to list
    for r in results.values():
        version, mode, observed_perc, unordered_perc, garble_perc = r.version, r.mode, r.observed_perc, r.unordered_perc, r.garble_perc
        accumulation[(version, mode, observed_perc, unordered_perc, garble_perc)].append(r)
    return accumulation

def pair_versions(accumulation):
    pairs = {}
    for key in accumulation.keys():
        if key[0] == "complex":
            other_tuple = ("simple",) + key[1:]
            if other_tuple in accumulation:
                pair = (accumulation[key], accumulation[other_tuple])
                pairs[key[1:]] = pair
            elif key[3:] == (0,0): #if the settings are such that the're equivalent, double up
                pair = (accumulation[key], accumulation[key])
                pairs[key[1:]] = pair
            else:
                print(other_tuple)
    return pairs

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


def get_table(res_filename, mode, obs_folder):

    results = get_results_from_file(res_filename)

    pairs = pair_and_accumulate(results)

    result_string = ""

    settings = [(mode, .5,0,0),
                (mode, .5, 0, .25),
                (mode, .5, .25, 0),
                (mode, .5, .5, 0),
                (mode, .5, .5, .25)
               ]
    for sett in settings:
        unfixed_category = pairs[sett]
        category = [(them,us) for them,us in pairs[sett] if not(0.0 in them.hyp_times.values())]
        category = [(them,us) for them,us in pairs[sett] if not isinstance(them.indicated, range)]
        # if len(unfixed_category) != len(filtered):
        #     raise Exception("PLEASE LOOK AT THIS")
        # print(len(unfixed_category) - len(category), res_filename, sett)

        unimprovable_category = [(them,us) for them, us in category if len(them.indicated)==1]
        improvable_category = [(them,us) for them,us in category if len(them.indicated)>1 and len(them.indicated) == len(us.indicated)]
        improved_category = [(them,us) for them,us in category if len(them.indicated)>1 and len(them.indicated) != len(us.indicated)]

        unimprovable_them_obsv_counts, unimprovable_us_obsv_counts = count_observations(unimprovable_category, obs_folder)
        improvable_them_obsv_counts, improvable_us_obsv_counts = count_observations(improvable_category, obs_folder)
        improved_them_obsv_counts, improved_us_obsv_counts = count_observations(improved_category, obs_folder)

        all_them_obsv_counts = unimprovable_them_obsv_counts+improvable_them_obsv_counts+improved_them_obsv_counts
        all_us_obsv_counts = unimprovable_us_obsv_counts+improvable_us_obsv_counts+improved_us_obsv_counts


        them_obsv_count_mean, them_obsv_count_err = confidence_interval(all_them_obsv_counts)
        us_obsv_count_mean, us_obsv_count_err = confidence_interval(all_us_obsv_counts)


        unimprovable_them_obsv_count_mean, unimprovable_them_obsv_count_err = confidence_interval(unimprovable_them_obsv_counts)
        unimprovable_us_obsv_count_mean, unimprovable_us_obsv_count_err = confidence_interval(unimprovable_us_obsv_counts)
        improvable_ed_them_obsv_count_mean, improvable_ed_them_obsv_count_err = confidence_interval(improvable_them_obsv_counts+improved_them_obsv_counts)
        improvable_ed_us_obsv_count_mean, improvable_ed_us_obsv_count_err = confidence_interval(improvable_us_obsv_counts+improved_us_obsv_counts)

        them_G_sizes = [len(them.indicated) for them,us in improvable_category+improved_category]
        us_G_sizes = [len(us.indicated) for them,us in improvable_category+improved_category]

        them_G_mean, them_G_err = confidence_interval(them_G_sizes)
        us_G_mean, us_G_err = confidence_interval(us_G_sizes)

        them_times = [them.time for them,us in category]
        us_times = [us.time for them, us in category]
        them_time_mean, them_time_err = confidence_interval(them_times)
        us_time_mean, us_time_err = confidence_interval(us_times)

        G_t_val, G_p_val = stats.ttest_ind(them_G_sizes, us_G_sizes, equal_var=False)
        G_significant = G_p_val < 0.05
        time_t_val, time_p_val = stats.ttest_ind(them_times, us_times, equal_var=False)
        time_significant = time_p_val < 0.05

        # format_str = "& {:.0f}\% & {:.0f}\% & {} & {} & {} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} "
        # format_str = format_str.format(sett[2]*100,sett[3]*100, len(unimprovable_category),len(improvable_category), len(improved_category),
        #                   them_obsv_count_mean,them_obsv_count_err,us_obsv_count_mean,us_obsv_count_err,
        #                   them_G_mean,them_G_err, us_G_mean,us_G_err,
        #                   them_time_mean,them_time_err, us_time_mean, us_time_err
        #                   )
        # result_string += format_str + r" \\ " + "\n"
        # format_str = "& {:.0f}\% & {:.0f}\% & {} & {} & {} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} " \
        #              "& {:.2f} $\pm$ {:.2f} & {:.2f} $\pm$ {:.2f} "
        # format_str = format_str.format(sett[2] * 100, sett[3] * 100, len(unimprovable_category),
        #                                len(improvable_category), len(improved_category),
        #                                unimprovable_them_obsv_count_mean, unimprovable_them_obsv_count_err, unimprovable_us_obsv_count_mean, unimprovable_us_obsv_count_err,
        #                                improvable_ed_them_obsv_count_mean, improvable_ed_them_obsv_count_err, improvable_ed_us_obsv_count_mean, improvable_ed_us_obsv_count_err,
        #                                them_G_mean, them_G_err, us_G_mean, us_G_err,
        #                                them_time_mean, them_time_err, us_time_mean, us_time_err
        #                                )

        format_str = "&& {:.0f}\% & {:.0f}\% & {} & {} " \
                     "& {:.2f} \scriptsize{{ $\pm$ {:.2f} }} & {:.2f} \scriptsize{{ $\pm$ {:.2f} }} " \
                     "& {:.2f} \scriptsize{{ $\pm$ {:.2f} }} & {:.2f} \scriptsize{{ $\pm$ {:.2f} }} " \
                     "& {} {}{:.2f} \scriptsize{{ $\pm$ {:.2f} }}{}{} & {}{}{:.2f} \scriptsize{{ $\pm$ {:.2f} }}{}  {}" \
                     "& {} {}{:.2f} \scriptsize{{ $\pm$ {:.2f} }}{}{} & {}{}{:.2f} \scriptsize{{ $\pm$ {:.2f} }}{}  {}"
        format_str = format_str.format(sett[2] * 100, sett[3] * 100, len(unimprovable_category),
                                       len(improvable_category)+ len(improved_category),
                                       unimprovable_them_obsv_count_mean, unimprovable_them_obsv_count_err,
                                       improvable_ed_them_obsv_count_mean, improvable_ed_them_obsv_count_err,
                                       unimprovable_us_obsv_count_mean, unimprovable_us_obsv_count_err,
                                       improvable_ed_us_obsv_count_mean, improvable_ed_us_obsv_count_err,
                                       r"\textbf{" if G_significant else "",
                                       r"\underline{" if them_G_mean<us_G_mean else "", them_G_mean, them_G_err, "}" if them_G_mean<us_G_mean else "",
                                       "}" if G_significant else "",
                                       r"\textbf{" if G_significant else "",
                                       r"\underline{" if us_G_mean<them_G_mean else "", us_G_mean, us_G_err, "}" if us_G_mean<them_G_mean else "",
                                       "}" if G_significant else "",
                                       r"\textbf{" if time_significant else "",
                                       r"\underline{" if them_time_mean<us_time_mean else "", them_time_mean, them_time_err,  "}" if them_time_mean<us_time_mean else "",
                                       "}" if time_significant else "",
                                       r"\textbf{" if time_significant else "",
                                       r"\underline{" if us_time_mean<them_time_mean else "", us_time_mean, us_time_err, "}" if us_time_mean<them_time_mean else "",
                                       "}" if time_significant else ""
                                       )
        result_string += format_str + r" \\ " + "\n"





    return " " + result_string[1:]

def statistical_analysis_per_domain(res_filename, mode, title):
    results = get_results_from_file(res_filename)

    pairs = pair_and_accumulate(results)

    # result_string = "Mode  O    U    D    : eff(pow=.8) pow(e=s) pow(e=m) pow(e=l) t     p    \n"

    settings = [(mode, .5, 0, 0),
                (mode, .5, 0, .25),
                (mode, .5, .25, 0),
                (mode, .5, .5, 0),
                (mode, .5, .5, .25)
                ]

    all_improvable_ed = []

    for sett in settings:
        unfixed_category = pairs[sett]
        category = [(them,us) for them,us in pairs[sett] if not(0.0 in them.hyp_times.values())]
        category = [(them,us) for them,us in pairs[sett] if not isinstance(them.indicated, range)]
        # if len(unfixed_category) != len(filtered):
        #     raise Exception("PLEASE LOOK AT THIS")
        # print(len(unfixed_category) - len(category), res_filename, sett)

        unimprovable_category = [(them,us) for them, us in category if len(them.indicated)==1]
        improvable_category = [(them,us) for them,us in category if len(them.indicated)>1 and len(them.indicated) == len(us.indicated)]
        improved_category = [(them,us) for them,us in category if len(them.indicated)>1 and len(them.indicated) != len(us.indicated)]

        improvable_ed_category = improved_category + improvable_category
        all_improvable_ed += improvable_ed_category

        them_G_sizes = [len(them.indicated) for them, us in improvable_ed_category]
        us_G_sizes = [len(us.indicated) for them, us in improvable_ed_category]

        ttest = TTestIndPower()
        effect_size_from_eight_power = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, power=.8 )
        power_from_sm_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, effect_size=.2 )
        power_from_med_effect = ttest.solve_power( nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, effect_size=.5 )
        power_from_large_effect = ttest.solve_power( nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, effect_size=.8 )

        t_val, p_val = stats.ttest_ind(them_G_sizes, us_G_sizes, equal_var=False)

        # result_string += f"{mode:5} {sett[1]:4} {sett[2]:4} {sett[3]:4} : {effect_size_from_eight_power:11.3f} {power_from_sm_effect:8.3f} {power_from_med_effect:8.3f} {power_from_large_effect:8.3f} {t_val:5.3f} {p_val:5.3f}\n"

    them_G_sizes = [len(them.indicated) for them, us in all_improvable_ed]
    us_G_sizes = [len(us.indicated) for them, us in all_improvable_ed]

    ttest = TTestIndPower()
    effect_size_from_eight_power = ttest.solve_power(nobs1=len(them_G_sizes),
                                                     ratio=(len(us_G_sizes) / len(them_G_sizes)), alpha=.05, power=.8)
    power_from_sm_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes) / len(them_G_sizes)),
                                             alpha=.05, effect_size=.2)
    power_from_med_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes) / len(them_G_sizes)),
                                              alpha=.05, effect_size=.5)
    power_from_large_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes) / len(them_G_sizes)),
                                                alpha=.05, effect_size=.8)

    t_val, p_val = stats.ttest_ind(them_G_sizes, us_G_sizes, equal_var=False)

    result_string = f"{title:20} : {effect_size_from_eight_power:11.3f} {power_from_sm_effect:8.3f} {power_from_med_effect:8.3f} {power_from_large_effect:8.3f} {t_val:6.3f} {p_val:6.5f}"

    return result_string

def statistical_analysis_multi(res_filenames, modes, title):
    all_improvable_ed = []

    # result_string = "Mode  O    U    D    : eff(pow=.8) pow(e=s) pow(e=m) pow(e=l) t     p    \n"
    for mode in modes:
        for res_filename in res_filenames:
            results = get_results_from_file(res_filename)
            pairs = pair_and_accumulate(results)


            settings = [(mode, .5, 0, 0),
                        (mode, .5, 0, .25),
                        (mode, .5, .25, 0),
                        (mode, .5, .5, 0),
                        (mode, .5, .5, .25)
                        ]


            for sett in settings:
                # unfixed_category = pairs[sett]
                # category = [(them,us) for them,us in pairs[sett] if not(0.0 in them.hyp_times.values())]
                category = [(them,us) for them,us in pairs[sett] if not isinstance(them.indicated, range)]
                # if len(unfixed_category) != len(filtered):
                #     raise Exception("PLEASE LOOK AT THIS")
                # print(len(unfixed_category) - len(category), res_filename, sett)

                # unimprovable_category = [(them,us) for them, us in category if len(them.indicated)==1]
                improvable_category = [(them,us) for them,us in category if len(them.indicated)>1 and len(them.indicated) == len(us.indicated)]
                improved_category = [(them,us) for them,us in category if len(them.indicated)>1 and len(them.indicated) != len(us.indicated)]

                all_improvable_ed += improved_category + improvable_category

                # them_G_sizes = [len(them.indicated) for them, us in improvable_ed_category]
                # us_G_sizes = [len(us.indicated) for them, us in improvable_ed_category]

                # ttest = TTestIndPower()
                # effect_size_from_eight_power = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, power=.8 )
                # power_from_sm_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, effect_size=.2 )
                # power_from_med_effect = ttest.solve_power( nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, effect_size=.5 )
                # power_from_large_effect = ttest.solve_power( nobs1=len(them_G_sizes), ratio=(len(us_G_sizes)/len(them_G_sizes)), alpha=.05, effect_size=.8 )
                #
                # t_val, p_val = stats.ttest_ind(them_G_sizes, us_G_sizes, equal_var=False)

                # result_string += f"{mode:5} {sett[1]:4} {sett[2]:4} {sett[3]:4} : {effect_size_from_eight_power:11.3f} {power_from_sm_effect:8.3f} {power_from_med_effect:8.3f} {power_from_large_effect:8.3f} {t_val:5.3f} {p_val:5.3f}\n"

    them_G_sizes = [len(them.indicated) for them, us in all_improvable_ed]
    us_G_sizes = [len(us.indicated) for them, us in all_improvable_ed]

    ttest = TTestIndPower()
    effect_size_from_eight_power = ttest.solve_power(nobs1=len(them_G_sizes),
                                                     ratio=(len(us_G_sizes) / len(them_G_sizes)), alpha=.05, power=.8)
    power_from_sm_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes) / len(them_G_sizes)),
                                             alpha=.05, effect_size=.2)
    power_from_med_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes) / len(them_G_sizes)),
                                              alpha=.05, effect_size=.5)
    power_from_large_effect = ttest.solve_power(nobs1=len(them_G_sizes), ratio=(len(us_G_sizes) / len(them_G_sizes)),
                                                alpha=.05, effect_size=.8)

    t_val, p_val = stats.ttest_ind(them_G_sizes, us_G_sizes, equal_var=False)

    # Setup for the df calculation in stats.ttest_ind
    v1 = np.var(them_G_sizes, 0, ddof=1)
    v2 = np.var(us_G_sizes, 0, ddof=1)
    n1 = len(them_G_sizes)
    n2 = len(us_G_sizes)

    # copied from stats._unequal_var_ttest_denom(v1, n1, v2, n2)
    vn1 = v1 / n1
    vn2 = v2 / n2
    df = (vn1 + vn2) ** 2 / (vn1 ** 2 / (n1 - 1) + vn2 ** 2 / (n2 - 1))

    mean_them = np.mean(them_G_sizes)
    mean_us = np.mean(us_G_sizes)
    mean_diff = mean_them - mean_us

    std_them = np.std(them_G_sizes)
    std_us = np.std(us_G_sizes)

    result_string = f"{title:20} : {effect_size_from_eight_power:11.3f} {power_from_sm_effect:8.3f} {power_from_med_effect:8.3f} {power_from_large_effect:8.3f} {t_val:6.3f} {p_val:6.4f} {df:8.2f} {n1:5} {mean_them:4.3f} {std_them:6.3f} {n2:5} {mean_us:6.3f} {std_us:6.3f} {mean_diff:6.3f}  "

    return result_string


def count_observations(category, folder):
    them_obsv_counts = []
    us_obsv_counts = []

    for them, us in category:
        them_obsv_perc_big, them_un_perc_big, them_garb_perc_big = them.observed_perc * 100, them.unordered_perc * 100, them.garble_perc * 100
        them_file = folder +"{them.problem}/simple_observations/{them.problem}_hyp{them.true_hyp}_{them.mode}_O{them_obsv_perc_big:.0f}_U{them_un_perc_big:.0f}_B{them_garb_perc_big:.0f}_{them.obs_idx}.obs".format(**locals())
        us_obsv_perc_big, us_un_perc_big, us_garb_perc_big = us.observed_perc*100, us.unordered_perc*100, us.garble_perc*100
        us_file = folder +"{us.problem}/complex_observations/{us.problem}_hyp{us.true_hyp}_{us.mode}_O{us_obsv_perc_big:.0f}_U{us_un_perc_big:.0f}_B{us_garb_perc_big:.0f}_{us.obs_idx}.obs".format(**locals())

        try:
            them_obsv = obscure_blind.read_simple_obs(them_file)
            them_obsv_counts.append(len(them_obsv))
        except FileNotFoundError:
            them_obsv_counts.append(0)

        us_obsv = obscure_blind.read_complex_obs(us_file)
        us_obsv_counts.append(len(us_obsv))


    return them_obsv_counts, us_obsv_counts

def confidence_interval(data, confidence=.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), stats.sem(a)
    h = se * stats.t.ppf((1 + confidence) / 2., n - 1)
    return m, h

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






