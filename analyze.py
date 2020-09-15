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

def histogram_of_opt_noimprov_improv(counts, label):
    barchart = plt.bar(np.arange(3), counts)
    plt.xticks(np.arange(3), ['Optimal', 'No Improvement', 'Improvement'])
    plt.title(label)
    plt.ylabel('Count of Problems')
    rects = barchart.patches
    for rect, label in zip(rects, counts):
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width() / 2, height, str(label), ha='center', va='bottom')
    plt.show()

def boxplot(list_o_lists, labels, title, ylabel="$|\mathcal{G}_T^*|$", rotation=0):
    plt.boxplot(list_o_lists, notch=True)
    plt.xticks(range(1,len(labels)+1), labels, rotation=rotation)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()


if __name__ == '__main__':
    # plt.interactive(False)

    # obsv_perc = .5
    # filename = "block-words-results.object"
    # filename = "easy-grid-navigation-results.object2"
    # filename = "easy-ipc-grid-results.object2"
    # filename = "logistics1-results.object2"
    # filenames = ["block-words-results.object","easy-grid-navigation-results.object2","easy-ipc-grid-results.object2", "logistics1-results.object2"]
    # for filename in filenames:
    #
    #     print(get_table(filename, "A", "Benchmark_Problems/block-words/"))
    #
    #     res = get_results_from_file(filename)
    #     print(res)
    #     acc = accumulate_results(res)
    #     pairs = pair_versions(acc)
    #     print([len(p) for p in pairs[('AF', 0.5, 0.5, 0.25)]])
    #
    #     pairs = pair_and_accumulate(res)

        # for sett in pairs.keys():
        #     pair = pairs[sett]
        #     if len(pair[0]) != len(pair[1]):
        #         continue
        #     ttest = TTestIndPower()
        #     effect = .2
        #     alpha = 0.05
        #     power = ttest.solve_power(effect_size=effect,nobs1=len(pair[0]), alpha=alpha, power=None, alternative='larger')
        #     print('\n',sett)
        #     print(pair[0])
        #     print(pair[1])
        #     print(power)
        #
        #     print(stats.ttest_rel(pair[0],pair[1]))
        #     diff_list = [them - us for (them,us) in zip(pair[0],pair[1])]
        #     diff_list_not_1 = [them - us for (them,us) in zip(pair[0],pair[1]) if them != 1]
        #     mean_diff = np.average(diff_list)
        #     print(mean_diff)
        #     interval = sms.DescrStatsW(diff_list).tconfint_mean(alpha=.05)
        #     print(interval)
        #
        #     print("Other:",diff_list_not_1)
        #     not_perf_interval = sms.DescrStatsW(diff_list_not_1).tconfint_mean(alpha=.05)
        #     print("Other:",not_perf_interval)
        #
        #     fig, ax = plt.subplots(1,2,tight_layout=False)
        #     grid = gridspec.GridSpec(2,2)
        #     ax0 = plt.subplot(grid[0,0])
        #     ax1 = plt.subplot(grid[0,1])
        #     ax2 = plt.subplot(grid[1,:])
        #
        #     ax0.boxplot(pair,labels=["Them", "Us"],)
        #     ax1.boxplot(diff_list, labels=["|G_them| - |G_us|"])
        #     ax0.yaxis.grid(True, color='lightgrey')
        #     ax0.set_axisbelow(True)
        #     ax1.yaxis.grid(True, color='lightgrey')
        #     ax1.set_axisbelow(True)
        #     # ax2.barh([0],[mean_diff],[mean_diff-interval[0]])
        #     # ax2.yticks([0], ["Difference"])
        #     plt.subplots_adjust(top=1.8)
        #     fig.suptitle(filename + " "+ str(sett))
        #     plt.show(block=True)

        # for mode in ['A', "AF"]:
        #     obsv_perc = .5
        #
        #     no_obsc = pairs[(mode, obsv_perc, 0, 0)]
        #
        #     vary_garble = pairs[(mode,obsv_perc,0,.25)]
        #
        #     combo = pairs[(mode,obsv_perc,.5,.25)]
        #
        #     vary_unord_little = pairs[(mode, obsv_perc, 0.25, 0)]
        #     vary_unord_lot = pairs[(mode, obsv_perc, 0.5, 0)]
        #
        #     # Separate already-optimal cases
        #     opt_no_obsc = [(them,us) for (them, us) in zip(no_obsc[0], no_obsc[1]) if them == 1]
        #     opt_vary_garble = [(them, us) for (them, us) in zip(vary_garble[0], vary_garble[1]) if them == 1]
        #     opt_combo = [(them, us) for (them, us) in zip(combo[0], combo[1]) if them == 1]
        #     opt_vary_unord_little = [(them, us) for (them, us) in zip(vary_unord_little[0], vary_unord_little[1]) if them == 1]
        #     opt_vary_unord_lot = [(them, us) for (them, us) in zip(vary_unord_lot[0], vary_unord_lot[1]) if them == 1]
        #
        #     no_improve_no_obsc = [(them, us) for (them, us) in zip(no_obsc[0], no_obsc[1]) if them !=1 and them == us]
        #     no_improve_vary_garble = [(them, us) for (them, us) in zip(vary_garble[0], vary_garble[1]) if them !=1 and them == us]
        #     no_improve_combo = [(them, us) for (them, us) in zip(combo[0], combo[1]) if them !=1 and them == us]
        #     no_improve_vary_unord_little = [(them, us) for (them, us) in zip(vary_unord_little[0], vary_unord_little[1]) if them !=1 and them == us]
        #     no_improve_vary_unord_lot = [(them, us) for (them, us) in zip(vary_unord_lot[0], vary_unord_lot[1]) if them !=1 and them == us]
        #
        #     improve_no_obsc = [(them, us) for (them, us) in zip(no_obsc[0], no_obsc[1]) if them != 1 and them != us]
        #     print("VAR_GARBLE_LENS:",len(vary_garble[0]), len(vary_garble[1]))
        #     improve_vary_garble = [(them, us) for (them, us) in zip(vary_garble[0], vary_garble[1]) if them != 1 and them != us]
        #     improve_combo = [(them, us) for (them, us) in zip(combo[0], combo[1]) if them != 1 and them != us]
        #     improve_vary_unord_little = [(them, us) for (them, us) in zip(vary_unord_little[0], vary_unord_little[1]) if them != 1 and them != us]
        #     improve_vary_unord_lot = [(them, us) for (them, us) in zip(vary_unord_lot[0], vary_unord_lot[1]) if them != 1 and them != us]
        #
        #     # Histogram of how many there is for each
        #     counts= [len(opt_vary_garble), len(no_improve_vary_garble), len(improve_vary_garble)]
        #     # histogram_of_opt_noimprov_improv(counts, (filename + " " + mode + ": Vary Garble"))
        #     # TODO: The Rest
        #
        #     ###### Boxplots ######
        #
        #     # Vary garble:
        #     only_improved = [[len(them.indicated) for (them,us) in improve_vary_garble], [len(us.indicated) for (them,us) in improve_vary_garble]]
        #     boxplot(only_improved, ["Obscure 25% (Them)", "Obscure 25% (Us)"], filename + " " + mode + ": When we did improve, by how much?")
        #
        #     difference = [[len(them.indicated) - len(us.indicated) for (them,us) in improve_vary_garble]]
        #     for (them,us) in improve_vary_garble:
        #         if len(them.indicated) - len(us.indicated) < 0:
        #             print(them)
        #             print(us)
        #     boxplot(difference, ["Obscure 25%"], filename+" "+mode+": When we did improve, by how much?", "$|\mathcal{G}_them^*| - |\mathcal{G}_us^*|$")
        #
        #     when_could_improve = [[len(them.indicated) for (them,us) in improve_no_obsc + no_improve_no_obsc], [len(them.indicated) for (them,us) in improve_vary_garble+no_improve_vary_garble], [len(us.indicated) for (them,us) in improve_vary_garble+no_improve_vary_garble]]
        #     boxplot(when_could_improve, ["Base (both)","Obscure 25% (Them)", "Obscure 25% (Us)"], filename + " " + mode + ": When we could improve, how much did we?")



        # pairs = pair_and_accumulate(res) # Lists of 2-tuples
        # # for (them, us) in pairs[('AF', 0.5, 0.5, 0.25)]:
        # #     print(them)
        # #     print(us)
        # # print(len( pairs[('AF', 0.5, 0.5, 0.25)]))
        #
        # for mode in ['A', 'AF']:
        #     no_obsc = pairs[(mode, obsv_perc, 0, 0)]
        #
        #     vary_garble = pairs[(mode, obsv_perc, 0, .25)]
        #
        #     combo = pairs[(mode, obsv_perc, .5, .25)]
        #
        #     vary_unord_little = pairs[(mode, obsv_perc, 0.25, 0)]
        #     vary_unord_lot = pairs[(mode, obsv_perc, 0.5, 0)]
        #
        #     opt_no_obsc = [(them,us) for (them,us) in no_obsc if len(them.indicated) == 1]
        #     opt_vary_garble = [(them, us) for (them, us) in vary_garble if len(them.indicated)== 1]
        #     opt_combo = [(them, us) for (them, us) in combo if len(them.indicated)== 1]
        #     opt_vary_unord_little = [(them, us) for (them, us) in vary_unord_little if len(them.indicated)== 1]
        #     opt_vary_unord_lot = [(them, us) for (them, us) in vary_unord_lot if len(them.indicated)== 1]
        #
        #     no_improve_no_obsc = [(them, us) for (them, us) in no_obsc if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated) ]
        #     no_improve_vary_garble = [(them, us) for (them, us) in vary_garble if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated) ]
        #     no_improve_combo = [(them, us) for (them, us) in combo if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated) ]
        #     no_improve_vary_unord_little = [(them, us) for (them, us) in vary_unord_little if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated) ]
        #     no_improve_vary_unord_lot = [(them, us) for (them, us) in vary_unord_lot if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated) ]
        #
        #     improve_no_obsc = [(them, us) for (them, us) in no_obsc if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated) ]
        #     improve_vary_garble = [(them, us) for (them, us) in vary_garble if len(them.indicated) != 1 and len(them .indicated) != len(us.indicated) ]
        #     improve_combo = [(them, us) for (them, us) in combo if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated) ]
        #     improve_vary_unord_little = [(them, us) for (them, us) in vary_unord_little if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated) ]
        #     improve_vary_unord_lot = [(them, us) for (them, us) in vary_unord_lot if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated) ]
        #
        #     no_obsc_counts = [len(opt_no_obsc), len(no_improve_no_obsc), len(improve_no_obsc)]
        #     print(filename + " " + mode + " No complexity histo: " + str(no_obsc_counts) + " Total: " + str(sum(no_obsc_counts)))
        #     vary_garble_counts = [len(opt_vary_garble), len(no_improve_vary_garble), len(improve_vary_garble)]
        #     print(filename + " " + mode + " U: 0%, B: 25% histo: " + str(vary_garble_counts) + " Total: " + str(sum(vary_garble_counts)))
        #     combo_counts = [len(opt_combo), len(no_improve_combo), len(improve_combo)]
        #     print(filename + " " + mode + " U: 50%, B: 25% histo: " + str(combo_counts) + " Total: " + str(sum(combo_counts)))
        #     vary_unord_little_counts = [len(opt_vary_unord_little), len(no_improve_vary_unord_little), len(improve_vary_unord_little)]
        #     print(filename + " " + mode + " U: 25%, B: 0% histo: " + str(vary_unord_little_counts) + " Total: " + str(sum(vary_unord_little_counts)))
        #     vary_unord_lot_counts = [len(opt_vary_unord_lot), len(no_improve_vary_unord_lot), len(improve_vary_unord_lot)]
        #     print(filename + " " + mode + " U: 50%, B: 0% histo: " + str(vary_unord_lot_counts) + " Total: " + str(sum(vary_unord_lot_counts)))
        #
        #     all_counts = [sum(x) for x in zip(no_obsc_counts,vary_garble_counts,combo_counts,vary_unord_little_counts,vary_unord_lot_counts)]
        #     print(filename + " " + mode + " SUM: " + str(all_counts) + " Total: " + str(sum(all_counts)))
        #
        #     # Vary garble:
        #     # only_improved = [[len(them.indicated) for (them, us) in improve_vary_garble], [len(us.indicated) for (them, us) in improve_vary_garble]]
        #     # boxplot(only_improved, ["Obscure 25% (Them)", "Obscure 25% (Us)"], filename + " " + mode + ": When we did improve, by how much?")
        #     #
        #     # when_could_improve = [[len(them.indicated) for (them,us) in improve_no_obsc + no_improve_no_obsc], [len(them.indicated) for (them,us) in improve_vary_garble+no_improve_vary_garble], [len(us.indicated) for (them,us) in improve_vary_garble+no_improve_vary_garble]]
        #     # boxplot(when_could_improve, ["Base (both)","Obscure 25% (Them)", "Obscure 25% (Us)"], filename + " " + mode + ": When we could improve, how much did we?")
        #     #
        #     # difference_did_improve = [len(them.indicated) - len(us.indicated) for (them, us) in improve_vary_garble]
        #     # boxplot(difference_did_improve, ["Obscure 25%"], filename + " " + mode + ": When we did improve, by how much?", "$|\mathcal{G}_them^*| - |\mathcal{G}_us^*|$")
        #     #
        #     # difference_could_improve = [len(them.indicated) - len(us.indicated) for (them, us) in improve_vary_garble+no_improve_vary_garble]
        #     # boxplot(difference_could_improve, ["Obscure 25%"], filename + " " + mode + ": When we could improve, by how much did we?", "$|\mathcal{G}_them^*| - |\mathcal{G}_us^*|$")
        #
        #
        #
        #
        #     # Lets just look at all the settings!
        #
        #     # diff_could_vary_garble = [len(them.indicated) - len(us.indicated) for (them, us) in
        #     #                           improve_vary_garble + no_improve_vary_garble]
        #     # diff_could_combo = [len(them.indicated) - len(us.indicated) for (them, us) in
        #     #                           improve_combo + no_improve_combo]
        #     # diff_could_vary_unord_little = [len(them.indicated) - len(us.indicated) for (them, us) in
        #     #                           improve_vary_unord_little + no_improve_vary_unord_little]
        #     # diff_could_vary_unord_lot = [len(them.indicated) - len(us.indicated) for (them, us) in
        #     #                           improve_vary_unord_lot + no_improve_vary_unord_lot]
        #     #
        #     # all_could_diffs = [diff_could_vary_garble , diff_could_combo , diff_could_vary_unord_little , diff_could_vary_unord_lot]
        #     # labels = ["U: 0%, B: 25%",
        #     #           "U: 50%, B: 25%",
        #     #           "U: 25%, B: 0%",
        #     #           "U: 50%, B: 0%"]
        #     #
        #     # boxplot(all_could_diffs, labels, filename+" "+mode + " When we could improve, by how much?", "$|\mathcal{G}_them^*| - |\mathcal{G}_us^*|$")
        #     #
        #     #
        #     # time_diff_opt_no_obsc = [them.time-us.time for (them,us) in opt_no_obsc]
        #     # time_diff_opt_vary_garble = [them.time-us.time for (them,us) in opt_vary_garble]
        #     # time_diff_opt_combo = [them.time-us.time for (them,us) in opt_combo]
        #     # time_diff_opt_vary_unord_little = [them.time-us.time for (them,us) in opt_vary_unord_little]
        #     # time_diff_opt_vary_unord_lot = [them.time-us.time for (them,us) in opt_vary_unord_lot]
        #     #
        #     # all_time_diffs_opt = [time_diff_opt_vary_garble, time_diff_opt_combo, time_diff_opt_vary_unord_little, time_diff_opt_vary_unord_lot]
        #     # labels = ["U: 0%, B: 25%",
        #     #           "U: 50%, B: 25%",
        #     #           "U: 25%, B: 0%",
        #     #           "U: 50%, B: 0%"]
        #     # boxplot(all_time_diffs_opt, labels, filename + " " + mode + " Time Comparison When Couldn't Improve", "time to compute (them) - time to compute (us)")
        #     #
        #     #
        #     # time_diff_opt_noimprov_no_obsc = [them.time-us.time for (them,us) in opt_no_obsc+no_improve_no_obsc]
        #     # time_diff_opt_noimprov_vary_garble = [them.time-us.time for (them,us) in opt_vary_garble+no_improve_vary_garble]
        #     # time_diff_opt_noimprov_combo = [them.time-us.time for (them,us) in opt_combo+no_improve_combo]
        #     # time_diff_opt_noimprov_vary_unord_little = [them.time-us.time for (them,us) in opt_vary_unord_little+no_improve_vary_unord_little]
        #     # time_diff_opt_noimprov_vary_unord_lot = [them.time-us.time for (them,us) in opt_vary_unord_lot+no_improve_vary_unord_lot]
        #     #
        #     # all_time_diffs_opt_noimprov = [time_diff_opt_noimprov_vary_garble, time_diff_opt_noimprov_combo, time_diff_opt_noimprov_vary_unord_little, time_diff_opt_noimprov_vary_unord_lot]
        #     # labels = ["U: 0%, B: 25%",
        #     #           "U: 50%, B: 25%",
        #     #           "U: 25%, B: 0%",
        #     #           "U: 50%, B: 0%"]
        #     # boxplot(all_time_diffs_opt_noimprov, labels, filename + " " + mode + " Time Comparison When Didn't Improve", "time to compute (them) - time to compute (us)")
        #     #
        #     #
        #     # time_diff_improve_no_obsc = [them.time-us.time for (them,us) in improve_no_obsc]
        #     # time_diff_improve_vary_garble = [them.time-us.time for (them,us) in improve_vary_garble]
        #     # time_diff_improve_combo = [them.time-us.time for (them,us) in improve_combo]
        #     # time_diff_improve_vary_unord_little = [them.time-us.time for (them,us) in improve_vary_unord_little]
        #     # time_diff_improve_vary_unord_lot = [them.time-us.time for (them,us) in improve_vary_unord_lot]
        #     #
        #     # all_time_diffs_improve = [time_diff_improve_vary_garble, time_diff_improve_combo, time_diff_opt_noimprov_vary_unord_little, time_diff_opt_noimprov_vary_unord_lot]
        #     # labels = ["U: 0%, B: 25%",
        #     #           "U: 50%, B: 25%",
        #     #           "U: 25%, B: 0%",
        #     #           "U: 50%, B: 0%"]
        #     # boxplot(all_time_diffs_improve, labels, filename + " " + mode + " Time Comparison When Improved", "time to compute (them) - time to compute (us)")
        #     #
        #     #
        #     # time_diff_all_no_obsc = [them.time-us.time for (them,us) in opt_no_obsc+no_improve_no_obsc]
        #     # time_diff_all_vary_garble = [them.time-us.time for (them,us) in opt_vary_garble+no_improve_vary_garble]
        #     # time_diff_all_combo = [them.time-us.time for (them,us) in opt_combo+no_improve_combo]
        #     # time_diff_all_vary_unord_little = [them.time-us.time for (them,us) in opt_vary_unord_little+no_improve_vary_unord_little]
        #     # time_diff_all_vary_unord_lot = [them.time-us.time for (them,us) in opt_vary_unord_lot+no_improve_vary_unord_lot]
        #     #
        #     # all_time_diffs_all = [time_diff_all_vary_garble, time_diff_all_combo, time_diff_all_vary_unord_little, time_diff_all_vary_unord_lot]
        #     # labels = ["U: 0%, B: 25%",
        #     #           "U: 50%, B: 25%",
        #     #           "U: 25%, B: 0%",
        #     #           "U: 50%, B: 0%"]
        #     # boxplot(all_time_diffs_all, labels, filename + " " + mode + " Time Comparison Overall", "time to compute (them) - time to compute (us)")
        #
        #     #
        #     # combine_all_time_diffs = []
        #     # positions = []
        #
        #
        #
        #     #######################################
        #
        #     def set_box_color(bp, color):
        #         plt.setp(bp['boxes'], color=color)
        #         plt.setp(bp['whiskers'], color=color)
        #         plt.setp(bp['caps'], color=color)
        #         plt.setp(bp['medians'], color=color)
        #
        #     def set_double_color(bp, color1, color2):
        #         plt.setp(bp['boxes'][0], color=color1)
        #         plt.setp(bp['caps'][0], color=color1)
        #         plt.setp(bp['caps'][1], color=color1)
        #         plt.setp(bp['whiskers'][0], color=color1)
        #         plt.setp(bp['whiskers'][1], color=color1)
        #         plt.setp(bp['fliers'][0], color=color1)
        #         plt.setp(bp['fliers'][1], color=color1)
        #         plt.setp(bp['medians'][0], color=color1)
        #
        #         plt.setp(bp['boxes'][1], color=color2)
        #         plt.setp(bp['caps'][2], color=color2)
        #         plt.setp(bp['caps'][3], color=color2)
        #         plt.setp(bp['whiskers'][2], color=color2)
        #         plt.setp(bp['whiskers'][3], color=color2)
        #         # plt.setp(bp['fliers'][2], color=color2)
        #         # plt.setp(bp['fliers'][3], color=color2)
        #         plt.setp(bp['medians'][1], color=color2)
        #
        #     ### |G| for us and them, over all five settings, when could improve
        #
        #     bp_base_case = [[len(them.indicated) for them,us in improve_no_obsc+no_improve_no_obsc]]
        #     # obsv_sizes = [len(obscure_blind.read_complex_obs(them.obsf)) if them.version=='complex' else len(obscure_blind.read_simple_obs(them.obsf)) for them,us in improve_no_obsc+no_improve_no_obsc]
        #     # base_case_obsv_size, base_case_obvs_size_err = confidence_interval( obsv_sizes)
        #     # print(base_case_obsv_size, base_case_obvs_size_err)
        #
        #     bp_garble_case = [ [len(them.indicated) for them,us in improve_vary_garble+no_improve_vary_garble],
        #                     [len(us.indicated) for them,us in improve_vary_garble+no_improve_vary_garble] ]
        #
        #     bp_unord_little = [ [len(them.indicated) for them,us in improve_vary_unord_little+no_improve_vary_unord_little],
        #                     [len(us.indicated) for them,us in improve_vary_unord_little+no_improve_vary_unord_little] ]
        #
        #     bp_unord_lot = [ [len(them.indicated) for them,us in improve_vary_unord_lot+no_improve_vary_unord_lot],
        #                     [len(us.indicated) for them,us in improve_vary_unord_lot+no_improve_vary_unord_lot] ]
        #
        #     bp_combo = [ [len(them.indicated) for them,us in improve_combo+no_improve_combo],
        #                     [len(us.indicated) for them,us in improve_combo+no_improve_combo] ]
        #
        #     # positions = [1, 3,4, 6,7, 9,10, 12,13]
        #     # labels = ["Base", "1", "2", "3", "4"]
        #     # bp_altogether = bp_base_case  + bp_garble_case + bp_unord_little + bp_unord_lot + bp_combo
        #     # plt.boxplot(bp_altogether, notch=True,positions=positions)
        #     # plt.xticks([1, 3.5,6.5,9.5,12.5 ], labels=labels)
        #     # plt.ylabel("|G|")
        #     # plt.title(filename + " " + mode +  " When Could Improve, |G|")
        #     # plt.show()
        #
        #     plt.figure(figsize=(6,6))
        #     ax = plt.subplot()
        #
        #     bp = ax.boxplot(bp_base_case, notch=True, positions=[1], widths=.6)
        #     set_box_color(bp, "black")
        #     bp = ax.boxplot(bp_garble_case, notch=True, positions=[3,4], widths=.6)
        #     set_double_color(bp, "black", "black")
        #     bp = ax.boxplot(bp_unord_little, notch=True, positions=[6,7], widths=.6)
        #     set_double_color(bp, "black", "black")
        #     bp = ax.boxplot(bp_unord_lot, notch=True, positions=[9,10], widths=.6)
        #     set_double_color(bp, "black", "black")
        #     bp = ax.boxplot(bp_combo, notch=True, positions=[12,13], widths=.6)
        #     set_double_color(bp, "black", "black")
        #
        #     labels = ["Base", "1", "2", "3", "4"]
        #     # ax.set_xticks([1,3.5,6.5,9.5,12.5])
        #     # ax.set_xticklabels(labels)
        #     ax.set_ylabel("|G|")
        #     ax.set_title(filename + " " + mode +  " When Could Improve, |G|")
        #
        #     # all_y = bp_base_case[0]+bp_garble_case[0]+bp_garble_case[1]+bp_unord_little[0]+bp_unord_little[1]+bp_unord_lot[0]+bp_unord_lot[1]+bp_combo[0]+bp_combo[1]
        #     # yint = range(0, ceil(max(all_y)) + 2)
        #     yint = range(1,23)
        #     ax.set_yticks(yint)
        #
        #     # hB, = ax.plot([1, 1], 'o-')
        #     # hR, = ax.plot([1, 1], 'b-')
        #     # ax.legend((hB, hR), ('Them', 'Us'))
        #     # hB.set_visible(False)
        #     # hR.set_visible(False)
        #
        #     labelticks = [1, 3.5, 3, 4, 6.5, 6, 7, 9.5, 9, 10, 12.5, 12, 13]
        #     major_labelticks = [1, 3, 4, 6, 7, 9, 10, 12, 13]
        #     minor_labelticks = [3.5, 6.5, 9.5, 12.5]
        #     # labelticks = [1, 3,4,5, 7,8,9, 11,12,13, 15,16,17]
        #     # major_labelticks = [1,3,5,7,9,11,13,15,17]
        #     # minor_labelticks = [4,8,12,16]
        #     labels = ["Base", "Us", "\n1", "Them", "Us", "\n2", "Them", "Us", "\n3", "Them", "Us", "\n4", "Them"]
        #     major_labels = ["Base\n\nU:0% D:0%"+"\nn={}".format(no_obsc_counts[1]+no_obsc_counts[2]), "Us", "Them", "Us", "Them", "Us", "Them", "Us", "Them"]
        #     minor_labels = ["\n\nU:0% D:25%"+"\nn={}".format(vary_garble_counts[1]+vary_garble_counts[2]),
        #                     "\n\nU:25% D:0%"+"\nn={}".format(vary_unord_little_counts[1]+vary_unord_little_counts[2]),
        #                     "\n\nU:50% D:0%"+"\nn={}".format(vary_unord_lot_counts[1]+vary_unord_lot_counts[2]),
        #                     "\n\nU:50% D:25%"+"\nn={}".format(combo_counts[1]+combo_counts[2])]
        #
        #     # vertical_alignment = [0, -.05, 0,0, -.05,0,0,-.05,0,0,-.05,0,0]
        #     # ax.set_xticks(major_labelticks)
        #     # ax.set_xticks(minor_labelticks, minor=True)
        #     # ax.set_xticklabels(labels)
        #     #
        #     # for tick, align in zip(ax.get_xticklabels(), vertical_alignment):
        #     #     tick.set_y(align)
        #     #
        #     # ax.tick_params(axis='x', which='minor', direction='out', length=0)
        #     ax.set_xticks(major_labelticks)
        #
        #     ax.set_xticks(minor_labelticks, minor=True)
        #     ax.set_xticklabels(major_labels)
        #     ax.set_xticklabels(minor_labels, minor=True)
        #     ax.tick_params(top=False, bottom=False, which='minor')
        #
        #     plt.show()
        #
        #
        #     ############# TIME GRAPHS ################
        #
        #     def set_triple_color(bp, color1, color2, color3):
        #         plt.setp(bp['boxes'][0], color=color1)
        #         plt.setp(bp['caps'][0], color=color1)
        #         plt.setp(bp['caps'][1], color=color1)
        #         plt.setp(bp['whiskers'][0], color=color1)
        #         plt.setp(bp['whiskers'][1], color=color1)
        #         plt.setp(bp['fliers'][0], color=color1)
        #         plt.setp(bp['fliers'][1], color=color1)
        #         plt.setp(bp['medians'][0], color=color1)
        #
        #         plt.setp(bp['boxes'][1], color=color2)
        #         plt.setp(bp['caps'][2], color=color2)
        #         plt.setp(bp['caps'][3], color=color2)
        #         plt.setp(bp['whiskers'][2], color=color2)
        #         plt.setp(bp['whiskers'][3], color=color2)
        #         # plt.setp(bp['fliers'][2], color=color2)
        #         # plt.setp(bp['fliers'][3], color=color2)
        #         plt.setp(bp['medians'][1], color=color2)
        #
        #         plt.setp(bp['boxes'][2], color=color3)
        #         plt.setp(bp['caps'][4], color=color3)
        #         plt.setp(bp['caps'][5], color=color3)
        #         plt.setp(bp['whiskers'][4], color=color3)
        #         plt.setp(bp['whiskers'][5], color=color3)
        #         # plt.setp(bp['fliers'][2], color=color3)
        #         # plt.setp(bp['fliers'][3], color=color3)
        #         plt.setp(bp['medians'][2], color=color3)
        #
        #     plt.figure(figsize=(6,6))
        #     ax = plt.subplot()
        #
        #     time_bp_garble = [ [them.time-us.time for them,us in opt_vary_garble],
        #                        [them.time-us.time for them,us in no_improve_vary_garble],
        #                        [them.time-us.time for them,us in improve_vary_garble]
        #                      ]
        #     time_bp_unord_little = [ [them.time - us.time for them, us in opt_vary_unord_little],
        #                        [them.time - us.time for them, us in no_improve_vary_unord_little],
        #                        [them.time - us.time for them, us in improve_vary_unord_little]
        #                      ]
        #     time_bp_unord_lot = [ [them.time - us.time for them, us in opt_vary_unord_lot],
        #                        [them.time - us.time for them, us in no_improve_vary_unord_lot],
        #                        [them.time - us.time for them, us in improve_vary_unord_lot]
        #                      ]
        #     time_bp_combo = [ [them.time - us.time for them, us in opt_combo],
        #                        [them.time - us.time for them, us in no_improve_combo],
        #                        [them.time - us.time for them, us in improve_combo]
        #                      ]
        #
        #
        #     bp = ax.boxplot(time_bp_garble, notch=True, positions=[1, 2, 3], widths=.6)
        #     set_triple_color(bp, 'red', 'blue', 'purple')
        #     bp = ax.boxplot(time_bp_unord_little, notch=True, positions=[5,6,7], widths=.6)
        #     set_triple_color(bp, 'red', 'blue', 'purple')
        #     bp = ax.boxplot(time_bp_unord_lot, notch=True, positions=[9,10,11], widths=.6)
        #     set_triple_color(bp, 'red', 'blue', 'purple')
        #     bp = ax.boxplot(time_bp_combo, notch=True, positions=[13,14,15], widths=.6)
        #     set_triple_color(bp, 'red', 'blue', 'purple')
        #
        #     ax.set_ylabel("Time (them) - Time (us)")
        #     ax.set_title(filename + " " + mode + " Time Differences")
        #
        #     major_ticks = [1,2,3, 5,6,7, 9,10,11, 13,14,15]
        #     minor_ticks = [2.01,6.01,10.01,14.01]
        #     major_labels = ["Optimal Already (n={})".format(vary_garble_counts[0]), "No Improvement (n={})".format(vary_garble_counts[1]), "Did Improve (n={})".format(vary_garble_counts[2]),
        #                     "Optimal Already (n={})".format(vary_unord_little_counts[0]), "No Improvement (n={})".format(vary_unord_little_counts[1]), "Did Improve (n={})".format(vary_unord_little_counts[2]),
        #                     "Optimal Already (n={})".format(vary_unord_lot_counts[0]), "No Improvement (n={})".format(vary_unord_lot_counts[1]), "Did Improve (n={})".format(vary_unord_lot_counts[2]),
        #                     "Optimal Already (n={})".format(combo_counts[0]), "No Improvement (n={})".format(combo_counts[1]), "Did Improve (n={})".format(combo_counts[2])]
        #     minor_labels = ["U:0% D:25%",
        #                     "U:25% D:0%",
        #                     "U:50% D:0%",
        #                     "U:50% D:25%"]
        #
        #     ax.set_xticks(major_ticks)
        #     ax.set_xticks(minor_ticks, minor=True)
        #     ax.set_xticklabels(major_labels, rotation=45, ha='right')
        #     ax.set_xticklabels(minor_labels, minor=True)
        #
        #
        #     for tick, align in zip(ax.get_xticklabels(which='minor'), [.05,.05,.05,.05]):
        #         tick.set_y(align)
        #
        #     plt.show()


    # TRY SOME STATS EY?

    print("                     :  eff(pow=.8)  pow(e=s) pow(e=m) pow(e=l)   t      p     df       n1    m1   std1    n2    m2   std2   m1-m2")
    # print()
    print(statistical_analysis_multi(["block-words-results-with-cpx-base.object"], ["A"], "Block-Words: A"))
    # print("")
    print(statistical_analysis_multi(["block-words-results-with-cpx-base.object"], ["AF"], "Block-Words: A+F"))

    # print("IPC-Grid: A")
    print(statistical_analysis_multi(["easy-ipc-grid-results-with-cpx-base.object"], ["A"], "IPC-Grid: A"))
    # print("IPC-Grid: A+F")
    print(statistical_analysis_multi(["easy-ipc-grid-results-with-cpx-base.object"], ["AF"], "IPC-Grid: A+F"))

    # print("Grid-Navigation: A")
    print(statistical_analysis_multi(["easy-grid-navigation-results-with-cpx-base.object"], ["A"], "Grid-Navigation: A"))
    # print("Grid-Navigation: A+F")
    print(statistical_analysis_multi(["easy-grid-navigation-results-with-cpx-base.object"], ["AF"], "Grid-Navigation: A+F"))

    # print("Logistics 1/2: A")
    print(statistical_analysis_multi(["logistics1-and-2-combined.object"], ["A"], "Logistics: A"))
    # print("Logistics 1/2: A+F")
    print(statistical_analysis_multi(["logistics1-and-2-combined.object"], ["AF"], "Logistics: A+F"))

    print()

    print(statistical_analysis_multi(["block-words-results-with-cpx-base.object"], ["A", "AF"], "Block-Words: A/A+F"))
    # print("")

    # print("IPC-Grid: A")
    print(statistical_analysis_multi(["easy-ipc-grid-results-with-cpx-base.object"], ["A", "AF"], "IPC-Grid: A/A+F"))
    # print("IPC-Grid: A+F")

    # print("Grid-Navigation: A")
    print(statistical_analysis_multi(["easy-grid-navigation-results-with-cpx-base.object"], ["A", "AF"], "Grid-Navigation:A/AF"))
    # print("Grid-Navigation: A+F")

    # print("Logistics 1/2: A")
    print(statistical_analysis_multi(["logistics1-and-2-combined.object"], ["A", "AF"], "Logistics: A/A+F"))
    # print("Logistics 1/2: A+F")
    print()

    # print("FROM ALL DOMAINS: A")
    print(statistical_analysis_multi(["block-words-results-with-cpx-base.object", "easy-ipc-grid-results-with-cpx-base.object", "easy-grid-navigation-results-with-cpx-base.object", "logistics1-and-2-combined.object"], ["A"], "ALL DOMAINS: A"))
    # print("FROM ALL DOMAINS: A+F")
    print(statistical_analysis_multi(["block-words-results-with-cpx-base.object", "easy-ipc-grid-results-with-cpx-base.object", "easy-grid-navigation-results-with-cpx-base.object", "logistics1-and-2-combined.object"], ["AF"], "ALL DOMAINS: A+F"))
    # print("FROM ALL DOMAINS: bboth modes")
    print(statistical_analysis_multi(["block-words-results-with-cpx-base.object", "easy-ipc-grid-results-with-cpx-base.object", "easy-grid-navigation-results-with-cpx-base.object", "logistics1-and-2-combined.object"], ["A", "AF"], "ALL DOMAINS: A / A+F"))


    print('\n')

    # exit(0)

    ##########################################
    ##########################################
    #######      The Real Graphs     #########
    ##########################################
    ##########################################
    print(r"\parbox[t]{2mm}{\multirow{20}{*}{\rotatebox[origin=c]{90}{\textbf{A} : Action Observations Only}}}")

    # print("Block-Words: A")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Block-Words}}}")
    print(get_table("block-words-results-with-cpx-base.object", "A", "Benchmark_Problems/block-words/"))
    print("\cline{3-14}")

    # print("IPC-Grid: A")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Ipc-Grid}}} ")
    print(get_table("easy-ipc-grid-results-with-cpx-base.object", "A", "Benchmark_Problems/easy-ipc-grid/"))
    print("\cline{3-14}")

    # print("Grid-Navigation: A")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Navigation}}} ")
    print(get_table("easy-grid-navigation-results-with-cpx-base.object", "A", "Benchmark_Problems/easy-grid-navigation/"))
    print("\cline{3-14}")

    # print("Logistics 1/2: A")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Logistics}}} ")
    print(get_table("logistics1-and-2-combined.object", "A", "Benchmark_Problems/logistics/"))

    print(r"\toprule")
    print(r"\parbox[t]{2mm}{\multirow{20}{*}{\rotatebox[origin=c]{90}{\textbf{A+F} : Action and Fluent Observations}}}")
    # print("Block-Words: A+F")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Block-Words}}}")
    print(get_table("block-words-results-with-cpx-base.object", "AF", "Benchmark_Problems/block-words/"))
    print("\cline{3-14}")
    # print("IPC-Grid: A+F")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Ipc-Grid}}} ")
    print(get_table("easy-ipc-grid-results-with-cpx-base.object", "AF", "Benchmark_Problems/easy-ipc-grid/"))
    print("\cline{3-14}")
    # print("Grid-Navigation: A+F")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Navigation}}} ")
    print(get_table("easy-grid-navigation-results-with-cpx-base.object", "AF", "Benchmark_Problems/easy-grid-navigation/"))
    print("\cline{3-14}")
    # print("Logistics 1/2: A+F")
    print(r"&\parbox[t]{2mm}{\multirow{5}{*}{\rotatebox[origin=c]{90}{Logistics}}} ")
    print(get_table("logistics1-and-2-combined.object", "AF","Benchmark_Problems/logistics/"))

    # log1_res = harness.get_object_from_file("logistics1-results-with-cpx-base.object")
    # log2_res = harness.get_object_from_file("logistics2-results-with-cpx-base.object")
    #
    # prior_logistics_results = {}
    # combo_results = {}
    #
    # for key, res in log1_res.items():
    #     if "/logistics/" in key:
    #         prior_logistics_results[key] = res
    #     else:
    #         new_key = key.replace("/logistics1/", "/logistics/")
    #         print(key, "->", new_key)
    #         combo_results[new_key] = res
    # for key, res in log2_res.items():
    #     if "/logistics/" in key:
    #         prior_logistics_results[key] = res
    #     else:
    #         new_key = key.replace("/logistics2/", "/logistics/")
    #         print(key, "->", new_key)
    #         if new_key in combo_results.keys():
    #             print(new_key, "exists in combo results. How?")
    #         else:
    #             combo_results[new_key] = res
    #
    # harness.write_object_to_file(combo_results, "logistics1-and-2-combined.object")
    # exit(0)


    filename = "block-words-results-with-cpx-base.object"
    res = get_results_from_file(filename)
    # icky_result = res["Benchmark_Problems/block-words/block-words_p01/simple_observations/block-words_p01_hyp2_AF_O50_U50_B25_2.obs"]
    # print(icky_result)
    pairs = pair_and_accumulate(res)
    obsv_perc = .5

    A_base = [(them,us) for them,us in  pairs[("A", obsv_perc, 0, 0)] if not isinstance(them.indicated, range)]
    A_vary_garble = [(them,us) for them,us in pairs[("A", obsv_perc, 0, .25)] if not isinstance(them.indicated, range)]
    A_combo = [(them,us) for them,us in pairs[("A", obsv_perc, .5, .25)] if not isinstance(them.indicated, range)]
    A_vary_unord_little = [(them,us) for them,us in pairs[("A", obsv_perc, 0.25, 0)] if not isinstance(them.indicated, range)]
    A_vary_unord_lot = [(them,us) for them,us in pairs[("A", obsv_perc, 0.5, 0)] if not isinstance(them.indicated, range)]


    AF_base = [(them,us) for them,us in  pairs[("AF", obsv_perc, 0, 0)] if not isinstance(them.indicated, range)]
    AF_vary_garble = [(them,us) for them,us in pairs[("AF", obsv_perc, 0, .25)] if not isinstance(them.indicated, range)]
    AF_combo = [(them,us) for them,us in pairs[("AF", obsv_perc, .5, .25)] if not isinstance(them.indicated, range)]
    AF_vary_unord_little = [(them,us) for them,us in pairs[("AF", obsv_perc, 0.25, 0)] if not isinstance(them.indicated, range)]
    AF_vary_unord_lot = [(them,us) for them,us in pairs[("AF", obsv_perc, 0.5, 0)] if not isinstance(them.indicated, range)]

    A_opt_base = [(them, us) for (them, us) in A_base if len(them.indicated) == 1]
    A_opt_vary_garble = [(them, us) for (them, us) in A_vary_garble if len(them.indicated) == 1]
    A_opt_combo = [(them, us) for (them, us) in zip(A_combo[0], A_combo[1]) if them == 1]
    A_opt_vary_unord_little = [(them, us) for (them, us) in A_vary_unord_little if len(them.indicated) == 1]
    A_opt_vary_unord_lot = [(them, us) for (them, us) in A_vary_unord_lot if len(them.indicated) == 1]

    A_no_improve_base = [(them, us) for (them, us) in A_base if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    A_no_improve_vary_garble = [(them, us) for (them, us) in A_vary_garble if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    A_no_improve_combo = [(them, us) for (them, us) in A_combo if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    A_no_improve_vary_unord_little = [(them, us) for (them, us) in A_vary_unord_little if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    A_no_improve_vary_unord_lot = [(them, us) for (them, us) in A_vary_unord_lot if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]

    A_improve_base = [(them, us) for (them, us) in A_base if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    A_improve_vary_garble = [(them, us) for (them, us) in A_vary_garble if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    A_improve_combo = [(them, us) for (them, us) in A_combo if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    A_improve_vary_unord_little = [(them, us) for (them, us) in A_vary_unord_little if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    A_improve_vary_unord_lot = [(them, us) for (them, us) in A_vary_unord_lot if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]

    AF_opt_base = [(them, us) for (them, us) in AF_base if len(them.indicated) == 1]
    AF_opt_vary_garble = [(them, us) for (them, us) in AF_vary_garble if len(them.indicated) == 1]
    AF_opt_combo = [(them, us) for (them, us) in zip(AF_combo[0], AF_combo[1]) if them == 1]
    AF_opt_vary_unord_little = [(them, us) for (them, us) in AF_vary_unord_little if len(them.indicated) == 1]
    AF_opt_vary_unord_lot = [(them, us) for (them, us) in AF_vary_unord_lot if len(them.indicated) == 1]

    AF_no_improve_base = [(them, us) for (them, us) in AF_base if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    AF_no_improve_vary_garble = [(them, us) for (them, us) in AF_vary_garble if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    AF_no_improve_combo = [(them, us) for (them, us) in AF_combo if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    AF_no_improve_vary_unord_little = [(them, us) for (them, us) in AF_vary_unord_little if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]
    AF_no_improve_vary_unord_lot = [(them, us) for (them, us) in AF_vary_unord_lot if len(them.indicated) != 1 and len(them.indicated) == len(us.indicated)]

    AF_improve_base = [(them, us) for (them, us) in AF_base if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    AF_improve_vary_garble = [(them, us) for (them, us) in AF_vary_garble if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    AF_improve_combo = [(them, us) for (them, us) in AF_combo if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    AF_improve_vary_unord_little = [(them, us) for (them, us) in AF_vary_unord_little if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]
    AF_improve_vary_unord_lot = [(them, us) for (them, us) in AF_vary_unord_lot if len(them.indicated) != 1 and len(them.indicated) != len(us.indicated)]

    A_improvable_base = A_no_improve_base + A_improve_base
    A_improvable_vary_garble = A_no_improve_vary_garble + A_improve_vary_garble
    A_improvable_combo = A_no_improve_combo + A_improve_combo
    A_improvable_vary_unord_little = A_no_improve_vary_unord_little + A_improve_vary_unord_little
    A_improvable_vary_unord_lot = A_no_improve_vary_unord_lot + A_improve_vary_unord_lot

    AF_improvable_base = AF_no_improve_base + AF_improve_base
    AF_improvable_vary_garble = AF_no_improve_vary_garble + AF_improve_vary_garble
    AF_improvable_combo = AF_no_improve_combo + AF_improve_combo
    AF_improvable_vary_unord_little = AF_no_improve_vary_unord_little + AF_improve_vary_unord_little
    AF_improvable_vary_unord_lot = AF_no_improve_vary_unord_lot + AF_improve_vary_unord_lot

    base_case_bp = [[len(them.indicated) for (them,us) in A_no_improve_base+A_improve_base],
                    [len(us.indicated) for (them, us) in A_no_improve_base + A_improve_base],
                    [len(them.indicated) for (them, us) in AF_no_improve_base + AF_improve_base],
                    [len(us.indicated) for (them, us) in AF_no_improve_base + AF_improve_base]
                    ]
    vary_garble_bp = [[len(them.indicated) for (them,us) in A_no_improve_vary_garble+A_improve_vary_garble],
                      [len(us.indicated) for (them,us) in A_no_improve_vary_garble+A_improve_vary_garble],
                      [len(them.indicated) for (them, us) in AF_no_improve_vary_garble + AF_improve_vary_garble],
                      [len(us.indicated) for (them, us) in AF_no_improve_vary_garble + AF_improve_vary_garble]
                     ]
    vary_unord_little_bp = [[len(them.indicated) for (them, us) in A_no_improve_vary_unord_little + A_improve_vary_unord_little],
                            [len(us.indicated) for (them, us) in A_no_improve_vary_unord_little + A_improve_vary_unord_little],
                            [len(them.indicated) for (them, us) in AF_no_improve_vary_unord_little + AF_improve_vary_unord_little],
                            [len(us.indicated) for (them, us) in AF_no_improve_vary_unord_little + AF_improve_vary_unord_little]
                           ]
    vary_unord_lot_bp = [[len(them.indicated) for (them, us) in A_no_improve_vary_unord_lot + A_improve_vary_unord_lot],
                         [len(us.indicated) for (them, us) in A_no_improve_vary_unord_lot + A_improve_vary_unord_lot],
                         [len(them.indicated) for (them, us) in AF_no_improve_vary_unord_lot + AF_improve_vary_unord_lot],
                         [len(us.indicated) for (them, us) in AF_no_improve_vary_unord_lot + AF_improve_vary_unord_lot]
                        ]
    combo_bp = [[len(them.indicated) for (them, us) in A_no_improve_combo + A_improve_combo],
                [len(us.indicated) for (them, us) in A_no_improve_combo + A_improve_combo],
                [len(them.indicated) for (them, us) in AF_no_improve_combo + AF_improve_combo],
                [len(us.indicated) for (them, us) in AF_no_improve_combo + AF_improve_combo]
               ]


    positions = [1, 3, 4, 6, 7, 9, 10, 12, 13]
    positions = [1, 2, 4,5, 7,8, 10,11, 13,14]
    fig, (ax1,ax2) = plt.subplots(2,1, sharey="all", figsize=(6,6))

    all_A = base_case_bp[:2] + vary_garble_bp[:2] + vary_unord_little_bp[:2] + vary_unord_lot_bp[:2] + combo_bp[:2]
    all_AF = base_case_bp[2:] + vary_garble_bp[2:] + vary_unord_little_bp[2:] + vary_unord_lot_bp[2:] + combo_bp[2:]


    ax2.set_yticks(range(1,22,2))
    ax2.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax1.grid(which='both', axis='y', linestyle='--',zorder=0, color='lightgrey')
    ax2.grid(which='both', axis='y', linestyle='--', zorder=0, color='lightgrey')

    ax1.set_ylabel("A: Action Observations Only\n$|\mathcal{G}^*|$")
    ax2.set_ylabel("A+F: Action and Fluent Observations\n$|\mathcal{G}^*|$")

    meanprops = dict(linestyle=':', linewidth=1.5, color='black')

    A_bp = ax1.boxplot(all_A, positions=positions, sym='.', notch=True, showmeans=True, meanline=True, meanprops=meanprops, widths=.7, patch_artist=True)
    AF_bp = ax2.boxplot(all_AF, positions=positions, sym='.', notch=True, showmeans=True, meanline=True, meanprops=meanprops, widths=.7, patch_artist=True)
    for bp in [A_bp, AF_bp]:
        for box in bp['boxes']:
            box.set_facecolor('white')
        for median in bp['medians']:
            median.set_color('black')

    major_ticks = positions
    minor_ticks= [1.5, 4.5, 7.5, 10.5, 13.5]
    major_labels = ["Ign","Cpx","Ign", "Cpx","Ign","Cpx","Ign","Cpx","Ign","Cpx"]
    ax2_minor_labels = ["\nn={}".format(len(base_case_bp[0])) + "\nU:0% B:0%",
                        "\nn={}".format(len(vary_garble_bp[0])) + "\nU:0% B:25%",
                        "\nn={}".format(len(vary_unord_little_bp[0])) + "\nU:25% B:0%",
                        "\nn={}".format(len(vary_unord_lot_bp[0])) + "\nU:50% B:0%",
                        "\nn={}".format(len(combo_bp[0])) + "\nU:50% B:25%"
                       ]
    ax1_minor_labels = ["n={}".format(len(base_case_bp[1])),
                        "n={}".format(len(vary_garble_bp[2])),
                        "n={}".format(len(vary_unord_little_bp[2])),
                        "n={}".format(len(vary_unord_lot_bp[2])),
                        "n={}".format(len(combo_bp[2]))
                       ]

    ax2.set_xticks(major_ticks)
    ax2.set_xticks(minor_ticks, minor=True)
    ax1.set_xticks(minor_ticks, minor=True)
    ax2.set_xticklabels(major_labels)
    ax1.set_xticklabels([])
    ax1.set_xticklabels(ax1_minor_labels, minor=True)
    ax2.set_xticklabels(ax2_minor_labels, minor=True)
    ax1.tick_params(top=False, bottom=False, which='both')
    ax2.tick_params(top=False, bottom=False, which='both')

    plt.show()


    ##### TIME ####

    A_time_base = [[them.time - us.time for (them, us) in A_opt_base],
                          [them.time - us.time for (them, us) in A_no_improve_base],
                          [them.time - us.time for (them, us) in A_improve_base]
                          ]
    A_time_vary_garble = [[them.time - us.time for (them, us) in A_opt_vary_garble],
                          [them.time - us.time for (them, us) in A_no_improve_vary_garble],
                          [them.time - us.time for (them, us) in A_improve_vary_garble]
                          ]
    A_time_vary_unord_little = [[them.time - us.time for (them, us) in A_opt_vary_unord_little],
                                [them.time - us.time for (them, us) in A_no_improve_vary_unord_little],
                                [them.time - us.time for (them, us) in A_improve_vary_unord_little]
                               ]
    A_time_vary_unord_lot = [[them.time - us.time for (them, us) in A_opt_vary_unord_lot],
                             [them.time - us.time for (them, us) in A_no_improve_vary_unord_lot],
                             [them.time - us.time for (them, us) in A_improve_vary_unord_lot]
                            ]
    A_time_combo = [[them.time - us.time for (them, us) in A_opt_combo],
                    [them.time - us.time for (them, us) in A_no_improve_combo],
                    [them.time - us.time for (them, us) in A_improve_combo]
                   ]

    AF_time_base = [[them.time - us.time for (them, us) in AF_opt_base],
                   [them.time - us.time for (them, us) in AF_no_improve_base],
                   [them.time - us.time for (them, us) in AF_improve_base]
                   ]
    AF_time_vary_garble = [[them.time - us.time for (them, us) in AF_opt_vary_garble],
                           [them.time - us.time for (them, us) in AF_no_improve_vary_garble],
                           [them.time - us.time for (them, us) in AF_improve_vary_garble]
                           ]
    AF_time_vary_unord_little = [[them.time - us.time for (them, us) in AF_opt_vary_unord_little],
                                 [them.time - us.time for (them, us) in AF_no_improve_vary_unord_little],
                                 [them.time - us.time for (them, us) in AF_improve_vary_unord_little]
                                 ]
    AF_time_vary_unord_lot = [[them.time - us.time for (them, us) in AF_opt_vary_unord_lot],
                              [them.time - us.time for (them, us) in AF_no_improve_vary_unord_lot],
                              [them.time - us.time for (them, us) in AF_improve_vary_unord_lot]
                              ]
    AF_time_combo = [[them.time - us.time for (them, us) in AF_opt_combo],
                     [them.time - us.time for (them, us) in AF_no_improve_combo],
                     [them.time - us.time for (them, us) in AF_improve_combo]
                     ]

    fig, (axA, axAF) = plt.subplots(2, 1, sharey="all", figsize=(7,7))
    axA.set_ylabel("A: Action Observations Only\ntime for $\mathcal{G}^*_{cpx}$ - time for $\mathcal{G}^*_{ign}$ (seconds)")
    # axA.set_title("A")
    axAF.set_ylabel("A+F: Action and Fluent Observations\ntime for $\mathcal{G}^*_{cpx}$ - time for $\mathcal{G}^*_{ign}$ (seconds)")
    # axAF.set_title("A+F")

    positions = [1,2,3, 5,6,7, 9,10,11, 13,14,15, 17,18,19]

    all_A_bp = A_time_base+A_time_vary_garble+A_time_vary_unord_little+A_time_vary_unord_lot+A_time_combo
    all_AF_bp = AF_time_base+AF_time_vary_garble+AF_time_vary_unord_little+AF_time_vary_unord_lot+AF_time_combo
    meanprops = dict(linestyle=':', linewidth=1.5, color='black')
    A_bp = axA.boxplot(all_A_bp, positions=positions, sym='.', notch=True, showmeans=True, meanline=True, meanprops=meanprops, widths=.7, patch_artist=True)
    AF_bp = axAF.boxplot(all_AF_bp, positions=positions, sym='.', notch=True, showmeans=True, meanline=True, meanprops=meanprops, widths=.7, patch_artist=True)
    for bp in [A_bp, AF_bp]:
        for box in bp['boxes']:
            box.set_facecolor('white')
        for median in bp['medians']:
            median.set_color('black')

    major_ticks = [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15,17,18,19]
    minor_ticks = [2.01,6.01,10.01,14.01,18.01]
    AF_major_labels = ["Unimprovable (n={})".format(len(AF_time_base[0])), "Unimproved (n={})".format(len(AF_time_base[1])), "Improved (n={})".format(len(AF_time_base[2])),
                    "Unimprovable (n={})".format(len(AF_time_vary_garble[0])), "Unimproved (n={})".format(len(AF_time_vary_garble[1])), "Improved (n={})".format(len(AF_time_vary_garble[2])),
                    "Unimprovable (n={})".format(len(AF_time_vary_unord_little[0])), "Unimproved (n={})".format(len(AF_time_vary_unord_little[1])), "Improved (n={})".format(len(AF_time_vary_unord_little[2])),
                    "Unimprovable (n={})".format(len(AF_time_vary_unord_lot[0])), "Unimproved (n={})".format(len(AF_time_vary_unord_lot[1])), "Improved (n={})".format(len(AF_time_vary_unord_lot[2])),
                    "Unimprovable (n={})".format(len(AF_time_combo[0])), "Unimproved (n={})".format(len(AF_time_combo[1])), "Improved (n={})".format(len(AF_time_combo[2]))]
    A_major_labels = ["n={}".format(len(A_time_base[0])), "n={}".format(len(A_time_base[1])), "n={}".format(len(A_time_base[2])),
                    "n={}".format(len(A_time_vary_garble[0])), "n={}".format(len(A_time_vary_garble[1])), "n={}".format(len(A_time_vary_garble[2])),
                    "n={}".format(len(A_time_vary_unord_little[0])), "n={}".format(len(A_time_vary_unord_little[1])), "n={}".format(len(A_time_vary_unord_little[2])),
                    "n={}".format(len(A_time_vary_unord_lot[0])), "n={}".format(len(A_time_vary_unord_lot[1])), "n={}".format(len(A_time_vary_unord_lot[2])),
                    "n={}".format(len(A_time_combo[0])), "n={}".format(len(A_time_combo[1])), "n={}".format(len(A_time_combo[2]))]

    minor_labels = ["U:0% B:0%",
                    "U:0% B:25%",
                    "U:25% B:0%",
                    "U:50% B:0%",
                    "U:50% B:25%"]

    axA.grid(which='both', axis='y', linestyle='--',zorder=0, color='lightgrey')
    axAF.grid(which='both', axis='y', linestyle='--',zorder=0, color='lightgrey')
    axAF.set_xticks(major_ticks)
    axAF.set_xticks(minor_ticks, minor=True)
    axA.set_xticks(minor_ticks, minor=True)
    axAF.set_xticklabels(AF_major_labels, rotation=45, ha='right')
    axA.set_xticklabels(A_major_labels, rotation=45, ha='right')

    axA.set_xticklabels(minor_labels, minor=True)

    for tick, align in zip(axA.get_xticklabels(which='minor'), [.15, .15, .15, .15, .15]):
        tick.set_y(align)



    axA.tick_params(top=False, bottom=False, which='both')
    axAF.tick_params(top=False, bottom=False, which='both')

    plt.show()


    ########################
    ### TIME, again, but combine improved with unimproved

    A_time_base = [[them.time - us.time for (them, us) in A_opt_base],
                   [them.time - us.time for (them, us) in A_improvable_base]
                   ]
    A_time_vary_garble = [[them.time - us.time for (them, us) in A_opt_vary_garble],
                          [them.time - us.time for (them, us) in A_improvable_vary_garble]
                          ]
    A_time_vary_unord_little = [[them.time - us.time for (them, us) in A_opt_vary_unord_little],
                                [them.time - us.time for (them, us) in A_improvable_vary_unord_little]
                                ]
    A_time_vary_unord_lot = [[them.time - us.time for (them, us) in A_opt_vary_unord_lot],
                             [them.time - us.time for (them, us) in A_improvable_vary_unord_lot]
                             ]
    A_time_combo = [[them.time - us.time for (them, us) in A_opt_combo],
                    [them.time - us.time for (them, us) in A_improvable_combo]
                    ]

    AF_time_base = [[them.time - us.time for (them, us) in AF_opt_base],
                    [them.time - us.time for (them, us) in AF_improvable_base]
                    ]
    AF_time_vary_garble = [[them.time - us.time for (them, us) in AF_opt_vary_garble],
                           [them.time - us.time for (them, us) in AF_improvable_vary_garble]
                           ]
    AF_time_vary_unord_little = [[them.time - us.time for (them, us) in AF_opt_vary_unord_little],
                                 [them.time - us.time for (them, us) in AF_improvable_vary_unord_little]
                                 ]
    AF_time_vary_unord_lot = [[them.time - us.time for (them, us) in AF_opt_vary_unord_lot],
                              [them.time - us.time for (them, us) in AF_improvable_vary_unord_lot]
                              ]
    AF_time_combo = [[them.time - us.time for (them, us) in AF_opt_combo],
                     [them.time - us.time for (them, us) in AF_improvable_combo]
                     ]

    fig, (axA, axAF) = plt.subplots(2, 1, sharey="all", figsize=(7, 7))
    axA.set_ylabel("A: Action Observations Only\ntime$_{ign}-$ time$_{cpx}$ (seconds)")
    # axA.set_title("A")
    axAF.set_ylabel("A+F: Action and Fluent Observation\ntime$_{ign}-$ time$_{cpx}$ (seconds)")
    # axAF.set_title("A+F")

    positions = [1,2, 4,5, 7,8 ,10,11, 13,14]

    all_A_bp = A_time_base + A_time_vary_garble + A_time_vary_unord_little + A_time_vary_unord_lot + A_time_combo
    all_AF_bp = AF_time_base + AF_time_vary_garble + AF_time_vary_unord_little + AF_time_vary_unord_lot + AF_time_combo
    meanprops = dict(linestyle=':', linewidth=1.5, color='black')
    A_bp = axA.boxplot(all_A_bp, positions=positions, sym='.', notch=True, showmeans=True, meanline=True,
                       meanprops=meanprops, widths=.7, patch_artist=True)
    AF_bp = axAF.boxplot(all_AF_bp, positions=positions, sym='.', notch=True, showmeans=True, meanline=True,
                         meanprops=meanprops, widths=.7, patch_artist=True)
    for bp in [A_bp, AF_bp]:
        for box in bp['boxes']:
            box.set_facecolor('white')
        for median in bp['medians']:
            median.set_color('black')

    major_ticks = [1,2, 4,5, 7,8 ,10,11, 13,14]
    minor_ticks = [1.5, 4.5, 7.5, 10.5, 13.35]
    AF_major_labels = ["Unimprovable (n={})".format(len(AF_time_base[0])),
                       "Improvable (n={})".format(len(AF_time_base[1])),

                       "Unimprovable (n={})".format(len(AF_time_vary_garble[0])),
                       "Improvable (n={})".format(len(AF_time_vary_garble[1])),

                       "Unimprovable (n={})".format(len(AF_time_vary_unord_little[0])),
                       "Improvable (n={})".format(len(AF_time_vary_unord_little[1])),

                       "Unimprovable (n={})".format(len(AF_time_vary_unord_lot[0])),
                       "Improvable (n={})".format(len(AF_time_vary_unord_lot[1])),

                       "Unimprovable (n={})".format(len(AF_time_combo[0])),
                       "Improvable (n={})".format(len(AF_time_combo[1])),
                       ]
    A_major_labels = ["n={}".format(len(A_time_base[0])),
                      "n={}".format(len(A_time_base[1])),

                      "n={}".format(len(A_time_vary_garble[0])),
                      "n={}".format(len(A_time_vary_garble[1])),

                      "n={}".format(len(A_time_vary_unord_little[0])),
                      "n={}".format(len(A_time_vary_unord_little[1])),

                      "n={}".format(len(A_time_vary_unord_lot[0])),
                      "n={}".format(len(A_time_vary_unord_lot[1])),

                      "n={}".format(len(A_time_combo[0])),
                      "n={}".format(len(A_time_combo[1]))
                     ]

    minor_labels = ["U:0% B:0%",
                    "U:0% B:25%",
                    "U:25% B:0%",
                    "U:50% B:0%",
                    "U:50% B:25%"]

    axA.grid(which='both', axis='y', linestyle='--', zorder=0, color='lightgrey')
    axAF.grid(which='both', axis='y', linestyle='--', zorder=0, color='lightgrey')
    axAF.set_xticks(major_ticks)
    axAF.set_xticks(minor_ticks, minor=True)
    axA.set_xticks(minor_ticks, minor=True)
    axAF.set_xticklabels(AF_major_labels, rotation=45, ha='right')
    axA.set_xticklabels(A_major_labels, rotation=45, ha='right')

    axA.set_xticklabels(minor_labels, minor=True)

    for tick, align in zip(axA.get_xticklabels(which='minor'), [.15, .15, .15, .15, .15]):
        tick.set_y(align)

    axA.tick_params(top=False, bottom=False, which='both')
    axAF.tick_params(top=False, bottom=False, which='both')

    plt.show()







