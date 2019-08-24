import obscure_blind
import os
from collections import defaultdict
import time as TIMER
from sys import stdout
import pickle
import csv
import random
from math import ceil
import argparse

DEVNULL = " > /dev/null"
# DEVNULL = " "

ERROR_LOG_FILE="errors.log"
def log_error(message):
    with open(ERROR_LOG_FILE, "a") as err_log:
        err_log.write(message)

PLAN_TIME_BOUND_FACTOR = 10
PLAN_TIME_LIMIT_MIN = 20

class Results:
    def __init__(self, problem, true_hyp, mode, version, observed_perc, unordered_perc, garble_perc, obs_idx,
                 obs_count, indicated, costs_of_hyps_with_obs, time, hyp_times,
                 num_orderings_done, num_orderings_total):
        self.problem = problem
        self.true_hyp = true_hyp
        self.mode = mode
        self.version = version
        self.observed_perc = observed_perc
        self.unordered_perc = unordered_perc
        self.garble_perc = garble_perc
        self.obs_idx = obs_idx
        self.obs_count = obs_count

        self.indicated = indicated
        self.costs_of_hyps_with_obs = costs_of_hyps_with_obs
        self.time = time
        self.hyp_times = hyp_times
        self.is_correct = (true_hyp in indicated)
        self.num_orderings_done = num_orderings_done
        self.num_orderings_total = num_orderings_total

        if self.version != "ordered" and not self.is_correct:
            log_error("Warning: {self.version} problem {self.problem} hyp{self.true_hyp} {self.mode} O{self.observed_perc:.0%} U{self.unordered_perc:.0%} B{self.garble_perc:.0%} idx{self.obs_idx} did not indicate the correct hypothesis, but should've. This indicates a non-optimal planner.\n".format(**locals()))
            # with open(ERROR_LOG_FILE, "a") as err_log:
            #     err_log.write("Warning: {self.version} problem {self.problem} hyp{self.true_hyp} {self.mode} O{self.observed_perc:.0%} U{self.unordered_perc:.0%} B{self.garble_perc:.0%} idx{self.obs_idx} did not indicate the correct hypothesis, but should've. This indicates a non-optimal planner.\n".format(**locals()))
        if self.version != "ordered" and self.num_orderings_total != 1:
            log_error("Warning: {self.version} problem {self.problem} hyp{self.true_hyp} {self.mode} O{self.observed_perc:.0%} U{self.unordered_perc:.0%} B{self.garble_perc:.0%} idx{self.obs_idx} appears to have multiple orderings, though it shouldn't. This will cause bad numbers in result extraction.\n".format(**locals()))
            # with open(ERROR_LOG_FILE, "a") as err_log:
            #     err_log.write("Warning: {self.version} problem {self.problem} hyp{self.true_hyp} {self.mode} O{self.observed_perc:.0%} U{self.unordered_perc:.0%} B{self.garble_perc:.0%} idx{self.obs_idx} appears to have multiple orderings, though it shouldn't. This will cause bad numbers in result extraction.\n".format(**locals()))

    def __str__(self):
        identifiers = "Problem: {self.problem} hyp {self.true_hyp}\tVersion: {self.version}\tMode: {self.mode}\n" \
                      "Setting: O:{self.observed_perc:.0%} U:{self.unordered_perc:.0%} B:{self.garble_perc:.0%} Observation {self.obs_idx}" \
                      "\t({self.obs_count} observations nested)".format(**locals())
        if self.is_correct is not None:
            identifiers += "\n\t{ind_size} indicated hypotheses: {self.indicated}\n" \
                           "\tTime: {self.time:.5f}\n" \
                           "\t{was_or_not} correct.".format(ind_size=len(self.indicated), **locals(),
                                                            was_or_not="Was" if self.is_correct else "Wasn't")
            identifiers += "\n\tThis problem tries {} of {} total-orderings\n".format(self.num_orderings_done,
                                                                                      self.num_orderings_total)
        return identifiers + "\n"


class Extracted_Results:
    def __init__(self, result_library):
        if isinstance(result_library, dict):
            result_library = result_library.values()

        self.num_results = defaultdict(float)  # defaults to 0.0
        self.overall_avg_time = 0

        self.avg_obs_sizes = defaultdict(float)
        self.avg_times = defaultdict(float)
        self.avg_correctness = defaultdict(float)
        self.avg_size_of_indicated = defaultdict(float)
        self.num_orderings_done_per_problem = defaultdict(float)
        self.num_total_orderings_per_problem = defaultdict(float)

        for result in result_library:
            # obsv_perc_big, un_perc_big, garb_perc_big = 100 * result.observed_perc, 100 * result.unordered_perc, 100 * result.garble_perc
            # index = "{result.version}_{result.mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
            index = (result.version, result.mode, result.observed_perc, result.unordered_perc, result.garble_perc)
            self.avg_obs_sizes[index] += result.obs_count
            self.num_results[index] += 1.0
            self.avg_times[index] += result.time
            self.overall_avg_time += result.time
            self.avg_size_of_indicated[index] += len(result.indicated)
            if result.is_correct:
                self.avg_correctness[index] += 1.0
            orderings_index = (
            result.version, result.mode, result.observed_perc, result.unordered_perc, result.garble_perc,
            result.problem, result.true_hyp, result.obs_idx)
            self.num_total_orderings_per_problem[orderings_index] = result.num_orderings_total
            self.num_orderings_done_per_problem[orderings_index] = result.num_orderings_done

        self.avg_total_orderings = defaultdict(float)
        self.avg_orderings_done = defaultdict(float)
        self.avg_fraction_of_orderings_done = defaultdict(float)
        self.num_problems = defaultdict(float)
        for key, result in self.num_orderings_done_per_problem.items():
            self.avg_total_orderings[key[:5]] += self.num_total_orderings_per_problem[key]
            self.avg_orderings_done[key[:5]] += self.num_orderings_done_per_problem[key]
            self.avg_fraction_of_orderings_done[key[:5]] += self.num_orderings_done_per_problem[key] / \
                                                            self.num_total_orderings_per_problem[key]
            self.num_problems[key[:5]] += 1

        for index in self.num_problems.keys():
            self.avg_total_orderings[index] /= self.num_problems[index]
            self.avg_orderings_done[index] /= self.num_problems[index]
            self.avg_fraction_of_orderings_done[index] /= self.num_problems[index]

        self.overall_avg_time /= sum(self.num_results.values())
        for index in self.num_results.keys():
            self.avg_obs_sizes[index] /= self.num_results[index]
            self.avg_size_of_indicated[index] /= self.num_results[index]
            self.avg_correctness[index] /= self.num_results[index]
            self.avg_times[index] /= self.num_results[index]

    def format_results(self, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25),
                       versions=("ignore", "simple", "complex"), outstream=stdout):
        # outstream.write("||       |       |       ||                    ignore                     ||                    complex                    ||\n"
        #                 "||   O   |   U   |   B   ||           A           |           AF          ||           A           |           AF          ||\n"
        #                 "||       |       |       ||   O   :   C   :   G   |   O   :   C   :   G   ||   O   :   C   :   G   |   O   :   C   :   G   ||\n")
        outstream.write("||       |       |       ||")
        for version in versions:
            outstream.write("{:^95}||".format(version))
        outstream.write("\n||   O   |   U   |   B   ||")
        for version in versions:
            outstream.write(
                "                       A                       |                       AF                      ||")
        outstream.write("\n||       |       |       ||")
        for version in versions:
            outstream.write(
                "   T   :   D   :   F   :   O   :   C   :   G   |   T   :   D   :   F   :   O   :   C   :   G   ||")
        outstream.write("\n")
        for observed_perc in obsv_percs:
            for unordered_perc in unord_percs:
                for garble_perc in garble_percs:
                    obsv_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                    outstream.write(
                        "||{obsv_perc_big:^7.0f}|{un_perc_big:^7.0f}|{garb_perc_big:^7.0f}||".format(**locals()))
                    for version in versions:
                        for mode in ["A", "AF"]:
                            # index = "{version}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
                            index = (version, mode, observed_perc, unordered_perc, garble_perc)
                            total_orderings = self.avg_total_orderings[index]
                            orderings_done = self.avg_orderings_done[index]
                            fract_ords_done = self.avg_fraction_of_orderings_done[index]
                            obs_size = self.avg_obs_sizes[index]
                            correctness = self.avg_correctness[index]
                            ind_size = self.avg_size_of_indicated[index]
                            outstream.write(
                                "{total_orderings:^7.2f}:{orderings_done:^7.2f}:{fract_ords_done:^7.2f}:{obs_size:^7.2f}:{correctness:^7.2f}:{ind_size:^7.2f}|".format(
                                    **locals()))
                        outstream.write("|")
                    outstream.write("\n")

        outstream.write("\n Avg time per problem, over all settings: {:.5f} seconds".format(self.overall_avg_time))
        outstream.write(
            "\n Total time for evaluation: {:.5f} seconds".format(
                self.overall_avg_time * sum(self.num_results.values())))

    def format_results_latex(self, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25),
                             versions=("ignore", "simple", "complex"), outstream=stdout):

        outstream.write(r"\begin{tabular}{|c|c|c")
        linelength = 3
        for version in versions:
            if version == "ordered":
                outstream.write("|c|c|c|c|c|c|c|c")
                linelength += 8
            else:
                outstream.write("|c|c|c|c")
                linelength += 4
        outstream.write(
            r"|}" + "\n" + r"\hline" + "\n" + r"\multirow{3}{*}{\textbf{O\%}} & \multirow{3}{*}{\textbf{U\%}} & \multirow{3}{*}{\textbf{B\%}} ")
        for version in versions:
            if version == "ignore":
                outstream.write(r"& \multicolumn{4}{c|}{\textbf{Previous (Ignore All Uncertainty)}}")
            if version == "simple":
                outstream.write(r"& \multicolumn{4}{c|}{\textbf{Previous (Ignore Most Uncertainty)}}")
            if version == "complex":
                outstream.write(r"& \multicolumn{4}{c|}{\textbf{This}}")
            if version == "ordered":
                outstream.write(r"& \multicolumn{8}{c|}{\textbf{Previous (Guess Ordering)}}")
        outstream.write(r"\\ \cline{{4-{}}}".format(linelength))
        outstream.write("\n&  &  ")
        for version in versions:
            if version == "ordered":
                outstream.write(r"& \multicolumn{4}{c|}{\textbf{A}} & \multicolumn{4}{c|}{\textbf{A+F}}")
            else:
                outstream.write(r"& \multicolumn{2}{c|}{\textbf{A}} & \multicolumn{2}{c|}{\textbf{A+F}}")
        outstream.write(r"\\ \cline{{4-{}}}".format(linelength))
        outstream.write("\n&  &  ")
        for version in versions:
            if version == "ordered":
                outstream.write(r"& ord & C & $|O'|$ & $|\G_T^*|$ & ord & C & $|O'|$ & $|\G_T^*|$ ")
            else:
                outstream.write(r"& $|O'|$ & $|\G_T^*|$ & $|O'|$ & $|\G_T^*|$ ")
        outstream.write(r"\\ \hline" + "\n")

        # """\multirow{6}{*}{100} & \multirow{2}{*}{0} & 0 & 1* & 00 & .00 & 00 & 1* & 00 & .00 & 00 & 00 & .00 & 00 & 00 & .00 & 00 & 00 & 00 & 00 & 00 \\ \cline{3-21} """
        always_correct = True
        always_one_order = True

        for observed_perc in obsv_percs:
            # outstream.write(r"\multirow{{6}}{{*}}{{{observed_perc:.0%}}}".format(**locals))
            for unordered_perc in unord_percs:
                for garble_perc in garble_percs:
                    obsv_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                    outstream.write("{obsv_perc_big:^7.0f}&{un_perc_big:^7.0f}&{garb_perc_big:^7.0f}".format(**locals()))
                    for version in versions:
                        for mode in ["A", "AF"]:
                            # index = "{version}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
                            index = (version, mode, observed_perc, unordered_perc, garble_perc)
                            obs_size = self.avg_obs_sizes[index]
                            if self.avg_correctness[index] < 1.0 and version != "ordered":
                                always_correct = False
                            if self.avg_orderings_done[index] > 1 and version != "ordered":
                                always_one_order = False
                            ind_size = self.avg_size_of_indicated[index]
                            if version != "ordered":
                                outstream.write("&{obs_size:^7.1f}&{ind_size:^7.1f}".format(**locals()))
                            else:
                                correctness = self.avg_correctness[index]
                                orderings_done = self.avg_orderings_done[index]
                                frac_done = self.avg_fraction_of_orderings_done[index]
                                outstream.write(
                                    "&{orderings_done:.1f}/{frac_done:.1f}&{correctness:.1f}&{obs_size:^7.1f}&{ind_size:^7.1f}".format(
                                        **locals()))
                    outstream.write(r"\\ \hline")
                    outstream.write("\n")
        outstream.write(r"\end{tabular}")
        if not always_correct:
            outstream.write(
                "\n Warning: Something did not always indicate the correct hypothesis that should've. This is a bug.")
        if not always_one_order:
            outstream.write(
                "\n Warning: A version that's not 'ordered' reports using more than one ordering. This is a bug.")
        outstream.write("\n Avg time per problem, over all settings: {:.5f} seconds".format(self.overall_avg_time))
        outstream.write(
            "\n Total time for evaluation: {:.5f} seconds".format(
                self.overall_avg_time * sum(self.num_results.values())))

    def format_results_blind(self):
        ss = "{:^8}|{:^7}|{:^7}|{:^7}|{:^7}|{:^7}:{:^7}:{:^7}:{:^7}:{:^7}:{:^7}\n".format("version","mode","O%","U%","B%","T","D","F","O","C","G")
        for index in sorted(self.num_results.keys()):
            version, mode, obsv_perc, unord_perc, garble_perc = index
            ss += "{version:^8}|{mode:^7}|{obsv_perc:^7.0%}|{unord_perc:^7.0%}|{garble_perc:^7.0%}|".format(**locals())
            total_orderings = self.avg_total_orderings[index]
            orderings_done = self.avg_orderings_done[index]
            fract_ords_done = self.avg_fraction_of_orderings_done[index]
            obs_size = self.avg_obs_sizes[index]
            correctness = self.avg_correctness[index]
            ind_size = self.avg_size_of_indicated[index]
            ss += "{total_orderings:^7.2f}:{orderings_done:^7.2f}:{fract_ords_done:^7.2f}:{obs_size:^7.2f}:{correctness:^7.2f}:{ind_size:^7.2f}".format(**locals())
            ss += "\n"
        return ss


class Setting:
    def __init__(self, version, mode, obs_idx, obsv_perc, unord_perc, garble_perc):
        self.version, self.mode, self.obs_idx, self.obsv_perc, self.unord_perc, self.garble_perc = version, mode, obs_idx, obsv_perc, unord_perc, garble_perc


def write_object_to_file(obj, filename):
    with open(filename, 'wb') as file:
        pickle.dump(obj, file)

def get_object_from_file(filename):
    try:
        with open(filename, 'rb') as file:
            try:
                return pickle.load(file)
            except Exception as ex:
                return None
    except Exception:
        return None

def write_results_CSV(filename, results):
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['problem', 'true_hyp', 'obs_idx', 'mode', 'version', 'observed_perc', 'unordered_perc', 'garble_perc',
                 'obs_count', 'indicated', 'costs_of_hyps_with_obs', 'time', 'hyp_times', 'is_correct',
                 'num_orderings_done', 'num_orderings_total'])
        for r in results.values():
            csv_writer.writerow([r.problem, r.true_hyp, r.obs_idx, r.mode, r.version, r.observed_perc, r.unordered_perc, r.garble_perc,
                 r.obs_count, r.indicated, r.costs_of_hyps_with_obs, r.time, r.hyp_times, r.is_correct,
                 r.num_orderings_done, r.num_orderings_total])



def run_planner(domain, problem, output_file='execution.details', trace_file=os.devnull, timeout_seconds=PLAN_TIME_LIMIT_MIN,
                bound=None):
    if not os.path.exists(domain):
        print("Domain file <" + domain + "> does not exist.")
    if not os.path.exists(problem):
        print("Problem file <" + problem + "> does not exist.")

    cmd = "./planner --domain {} --problem {} --output {} --trace_output {} ".format(domain, problem, output_file,
                                                                                     trace_file)
    if timeout_seconds is not None:
        timeout_seconds = max(PLAN_TIME_LIMIT_MIN, timeout_seconds)
        cmd += " --time {} ".format(int(ceil(timeout_seconds)))
    else:
        cmd += " --time 100"
    if bound is not None:
        cmd += " --bound {} ".format(bound)
    print(cmd + DEVNULL)
    start_time = TIMER.time()
    os.system(cmd + DEVNULL)
    time = TIMER.time() - start_time

    plan, cost, _ = obscure_blind.read_plan_details(output_file)
    return plan, cost, time


def fill_template_pddl(template_f, output_f, fill):
    instream = open(template_f, 'r')
    outstream = open(output_f, 'w')

    for line in instream:
        if '<HYPOTHESIS>' not in line:
            outstream.write(line.lower())
        else:
            outstream.write(fill.lower())

    outstream.close()
    instream.close()

def read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f):
    hyps = []
    with open(hyps_f, 'r') as hyps_file:
        for line in hyps_file:
            hyps.append(line.replace(',', '\n'))
            # if set(fl.strip() for fl in true_hyp_str.split("\n")) == set(fl.strip() for fl in hyps[-1].split("\n")):
            #     true_hyp = len(hyps)-1
    hyp_costs = []
    hyp_problems = []
    hyp_solutions = []
    hyp_traces = []
    hyp_times = []

    try:
        os.makedirs(basename + "_hypotheses")
    except FileExistsError:
        pass

    # Compute optimal unconstrained solutions for each hypothesis:
    for hyp in range(len(hyps)):
        hyp_problem = basename + "_hypotheses/hyp_{}_problem.pddl".format(hyp)
        hyp_problems.append(hyp_problem)
        fill_template_pddl(template_f, hyp_problem, hyps[hyp])
        hyp_sol = basename + "_hypotheses/hyp_{}.solution".format(hyp)
        hyp_solutions.append(hyp_sol)
        hyp_trace = basename + "_hypotheses/hyp_{}.trace".format(hyp)
        hyp_traces.append(hyp_trace)
        if not os.path.exists(hyp_sol):
            _, cost, time = run_planner(domain_f, hyp_problem, hyp_sol, hyp_trace, 1000)
        else:
            _, cost, time = obscure_blind.read_plan_details(hyp_sol)
        if cost is None:
            raise Exception("Could not find a plan for hypothesis {}".format(hyp))
        hyp_costs.append(cost)
        hyp_times.append(time)
    return hyp_costs, hyp_problems, hyp_solutions, hyp_traces, hyp_times, hyps


def write_ordering_info(filename, total_orders,max_num_tot_orders=25):
    with open(filename, "w") as file:
        file.write(str(len(total_orders)))
        file.write("\n")
        file.write(str(min(max_num_tot_orders, len(total_orders))))

def read_ordering_info(filename):
    with open(filename, "r") as file:
        num_total_orders = int(file.readline())
        num_orders_kept = int(file.readline())
    return num_total_orders, num_orders_kept

def write_observation_domain_settings(settings, folder, problemnames=None, overwrite=False, max_num_tot_orders=25):
    if problemnames is None:
        problemnames = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

    for problemname in problemnames:
        write_observations_settings(settings, folder,problemname,overwrite, max_num_tot_orders)

def write_observations_settings(settings, folder, problemname, overwrite=False, max_num_tot_orders=25):
    basename = folder + "/" + problemname + "/"
    domain_f = basename + "domain.pddl"
    hyps_f = basename + "hyps.dat"
    template_f = basename + "template.pddl"

    hyp_costs, hyp_problems, hyp_solutions, hyp_traces, hyp_times, hyps = read_hypotheses_and_get_costs(basename,domain_f,hyps_f,template_f)
    for setting in settings:
        write_observations_setting(folder,problemname,setting,hyp_solutions, hyp_traces, overwrite, max_num_tot_orders)

def write_observations_setting(folder, problemname, sett, hyp_solutions, hyp_traces, overwrite=False, max_num_tot_orders=25):
    basename = folder + "/" + problemname + "/"
    domain_f = basename + "domain.pddl"
    template_f = basename + "template.pddl"

    complex_folder = basename + "complex_observations/"
    ignore_folder = basename + "ignore_observations/"
    simple_folder =  basename + "simple_observations/"
    ordered_folder = basename + "order_observations/"


    # Make directories if needed:
    try:
        os.makedirs(complex_folder)
    except FileExistsError:
        pass
    try:
        os.makedirs(ignore_folder)
    except FileExistsError:
        pass
    try:
        os.makedirs(simple_folder)
    except FileExistsError:
        pass
    try:
        os.makedirs(ordered_folder)
    except FileExistsError:
        pass

    for true_hyp in range(len(hyp_solutions)):
        obsv_perc_big, un_perc_big, garb_perc_big = 100 * sett.obsv_perc, 100 * sett.unord_perc, 100 * sett.garble_perc
        obs_f = "{problemname}_hyp{true_hyp}_{sett.mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{sett.obs_idx}.obs".format(**locals())
        print("Writing ", obs_f)

        optimal_steps,_,_ = obscure_blind.read_plan_details(hyp_solutions[true_hyp])
        optimal_trace = obscure_blind.read_trace(hyp_traces[true_hyp])

        if not overwrite :
            the_folder = basename + sett.version + "_observations/"
            if sett.version == "ordered": the_folder = ordered_folder
            if os.path.exists(the_folder+obs_f):
                print("Obs file {} exists, not overwriting.".format(the_folder+obs_f))
                continue

        # Get the complex obs, or make if necessary
        if not os.path.exists(complex_folder + obs_f):
            if sett.mode == "A":
                obscure_blind.obscure_A_to_file(complex_folder + obs_f, optimal_steps,sett.obsv_perc,sett.unord_perc,sett.garble_perc)
            else:
                obscure_blind.obscure_AF_to_file(complex_folder + obs_f, optimal_steps, optimal_trace, sett.obsv_perc,sett.unord_perc,sett.garble_perc, .1)
        observations = obscure_blind.read_complex_obs(complex_folder + obs_f)

        if sett.version == "complex":
            pass # Already done did it
        elif sett.version == "ignore":
            ignore_obs = obscure_blind.write_ignore_all_uncertainty_to_file(observations, ignore_folder + obs_f)
        elif sett.version == "simple":
            simple_obs = obscure_blind.write_ignore_most_uncertainty_to_file(observations, simple_folder + obs_f)
        elif sett.version == "ordered":
            # Remove too-complex things:
            without_fl_or_opt = observations.without_fl_obs()
            if without_fl_or_opt is not None:
                without_fl_or_opt = without_fl_or_opt.without_option_groups()
            total_orders = without_fl_or_opt.get_all_total_orderings() if without_fl_or_opt is not None else []
            num_total_orders = len(total_orders)
            print("{} total orders".format(num_total_orders))
            # Start with a clean folder to overwrite any previous obs orderings
            os.system("rm -rf {}".format(ordered_folder + obs_f.replace(".obs", "/")))
            os.makedirs(ordered_folder + obs_f.replace(".obs", "/"))

            write_ordering_info(ordered_folder + obs_f.replace(".obs", "/") + obs_f.replace(".obs", ".info"),total_orders,max_num_tot_orders)

            if len(total_orders) > max_num_tot_orders:
                total_orders = random.sample(total_orders, max_num_tot_orders)
            for i in range(len(total_orders)):
                obscure_blind.write_simple_obs_to_file(total_orders[i], ordered_folder + obs_f.replace(".obs", "/")+ obs_f.replace(".obs", "_ord{}.obs".format(i)))

def make_giant_settings():
    settings = []
    for version in ["complex","simple"]:
        for obs_idx in [0,1,2]:
            for obsv_perc in [.25,.5,1]:
                for unord_perc in [0,.5,1]:
                    for garble_perc in [0,.25]:
                        for mode in ["A","AF"]:
                            settings.append(Setting(version,mode,obs_idx,obsv_perc,unord_perc,garble_perc))
    return settings

def make_settings():
    settings = []
    obsv_perc = .5
    for mode in ["A","AF"]:
        for obs_idx in (0,1,2):
            for version in ["simple", "complex"]:
                settings.append(Setting(version,mode,obs_idx,obsv_perc,.5,.25)) # Mixed
                settings.append(Setting(version,mode,obs_idx,obsv_perc,.5,0)) # Vary unorderedness
                settings.append(Setting(version,mode,obs_idx,obsv_perc,.25,0)) # Vary unorderedness
                settings.append(Setting(version, mode, obs_idx, obsv_perc, 0, .25))  # Vary garble
            settings.append(Setting("simple", mode, obs_idx, obsv_perc, 0, 0))  # Vary nothing
    return settings

def make_small_settings():
    settings = []
    obsv_perc = .5
    for mode in ["A", "AF"]:
        for obs_idx in [0]:
            for version in ["simple", "complex"]:
                settings.append(Setting(version, mode, obs_idx, obsv_perc, .5, .25))  # Mixed
                settings.append(Setting(version, mode, obs_idx, obsv_perc, .5, 0))  # Vary unorderedness
                settings.append(Setting(version, mode, obs_idx, obsv_perc, 0, .25))  # Vary garble
            settings.append(Setting("simple", mode, obs_idx, obsv_perc, 0, 0))  # Vary nothing
    return settings

def make_tiny_settings():
    settings = []
    obsv_perc = .5
    for mode in ["A", "AF"]:
        for obs_idx in [0]:
            for version in ["simple", "complex"]:
                settings.append(Setting(version, mode, obs_idx, obsv_perc, .5, .25))  # Mixed
            settings.append(Setting("simple", mode, obs_idx, obsv_perc, 0, 0))  # Vary nothing
    return settings

def count_runs(folder, settings, problemname, max_ordered=25, true_hyps=None):
    if true_hyps is None:
        hyps = []
        with open(folder + "/" + problemname + "/hyps.dat", 'r') as hyps_file:
            for line in hyps_file:
                hyps.append(line.replace(',', '\n'))
            true_hyps = range(len(hyps))

    num_runs = 0
    ordered_folder = folder + "/" + problemname + "/" + "order_observations/"
    for true_hyp in true_hyps:
        for s in settings:
            if s.version == "ordered":
                obsv_perc_big, un_perc_big, garb_perc_big = 100 * s.obsv_perc, 100 * s.unord_perc, 100 * s.garble_perc
                obs_folder = ordered_folder + "{problemname}_hyp{true_hyp}_{s.mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{s.obs_idx}/".format(**locals())
                obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if f.endswith(".obs") and os.path.isfile(os.path.join(obs_folder, f))]
                num_runs += min(len(obs_fs), max_ordered)
            else:
                num_runs += 1

    return num_runs

def count_runs_domain(folder, settings, problemnames=None, max_ordered=25):
    count = 0
    if problemnames is None:
        problemnames = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
    for name in problemnames:
        count += count_runs(folder, settings, name, max_ordered)
    return count
def count_runs_domains(folder, settings, domains=None, max_ordered=25):
    count = 0
    if domains is None:
        domains = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
    for domain in domains:
        count += count_runs_domain(folder+"/"+domain, settings, None, max_ordered)
    return count

def evaluate_domain(folder, settings, problemnames=None, true_hyps=None, result_library=None, num_runs_total=None,
                    num_runs_so_far=None, absolute_start_time=TIMER.time(), result_file=None, time_limit=PLAN_TIME_LIMIT_MIN):
    if result_library is None and result_file is not None:
        result_tmp = get_object_from_file(result_file)
        if isinstance(result_tmp, dict):
            result_library = result_tmp

    if problemnames is None:
        problemnames = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

    if num_runs_total is None:
        num_runs_total = count_runs_domain(folder, settings, problemnames)
    if num_runs_so_far is None:
        num_runs_so_far = 0

    for problemname in problemnames:
        _, num_runs_so_far = evaluate_problem(folder, settings, problemname, true_hyps, result_library, num_runs_total, num_runs_so_far, absolute_start_time, result_file, time_limit)

    return result_library, num_runs_so_far

def evaluate_problem(folder, settings, problemname, true_hyps=None, result_library=None, num_runs_total=None,
                     num_runs_so_far=None, absolute_start_time=TIMER.time(), result_file=None, time_limit=PLAN_TIME_LIMIT_MIN):
    if result_library is None and result_file is not None:
        result_tmp = get_object_from_file(result_file)
        if isinstance(result_tmp, dict):
            result_library = result_tmp

    if result_library is None:
        result_library = {}
    basename = folder + "/" + problemname + "/"
    domain_f = basename + "domain.pddl"
    hyps_f = basename + "hyps.dat"
    template_f = basename + "template.pddl"

    hyp_costs, hyp_problems, hyp_solutions, hyp_traces, optimal_hyp_times, hyps = read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f)

    if true_hyps is None:
        true_hyps = range(len(hyps))

    # Count num runs and such
    if num_runs_total is None:
        num_runs_total = count_runs(folder,settings,problemname,true_hyps=true_hyps)
    if num_runs_so_far is None:
        num_runs_so_far = 0

    for true_hyp in true_hyps:
        for setting in settings:
            _, num_runs_so_far = evaluate_setting(folder, problemname, true_hyp, setting, hyp_costs, hyp_problems, hyps, optimal_hyp_times,result_library, num_runs_total, num_runs_so_far, absolute_start_time, result_file, time_limit)
    return result_library, num_runs_so_far

def evaluate_setting(folder, problemname, true_hyp, sett, hyp_costs, hyp_problems, hyps, optimal_hyp_times,
                     result_library=None, num_runs_total=None, num_runs_so_far=None, absolute_start_time=TIMER.time(),
                     result_file=None, time_limit=PLAN_TIME_LIMIT_MIN):
    if result_library is None and result_file is not None:
        result_tmp = get_object_from_file(result_file)
        if isinstance(result_tmp, dict):
            result_library = result_tmp
    if result_library is None:
        result_library = {}
    if num_runs_total is None:
        num_runs_total = count_runs(folder,[sett],problemname)
    if num_runs_so_far is None:
        num_runs_so_far = 0

    basename = folder + "/" + problemname + "/"
    domain_f = basename + "domain.pddl"

    if sett.version == "complex":
        the_folder = basename + "complex_observations/"
    elif sett.version == "ignore":
        the_folder = basename + "ignore_observations/"
    elif sett.version == "simple":
        the_folder = basename + "simple_observations/"
    elif sett.version == "ordered":
        the_folder = basename + "order_observations/"
    else:
        the_folder = None
        print("Evaluation version {} not recognized".format(sett.version))
        exit(1)
    obsv_perc_big, un_perc_big, garb_perc_big = 100 * sett.obsv_perc, 100 * sett.unord_perc, 100 * sett.garble_perc

    obs_name = "{problemname}_hyp{true_hyp}_{sett.mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{sett.obs_idx}".format(**locals())
    obs_fs = [the_folder + obs_name + ".obs"]
    num_orderings_total = 1

    # If version is 'ordered', we test a (given) sample of orderings, making sure to read how many there were before sampling.
    if sett.version == "ordered":
        obs_folder = the_folder + obs_name + "/"
        obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if
                  f.endswith(".obs") and os.path.isfile(os.path.join(obs_folder, f))]
        num_orderings_total, _ = read_ordering_info(obs_folder + obs_name + ".info")

    for i in range(len(obs_fs)):
        obs_f = obs_fs[i]

        num_runs_so_far += 1
        time_so_far = (TIMER.time() - absolute_start_time) / 60
        print("{} of {} runs. {:.2f} minutes spent, {:.2f} etr".format(num_runs_so_far,num_runs_total, time_so_far, time_so_far/num_runs_so_far * (num_runs_total-num_runs_so_far)))
        print("Observation from ", obs_f)
        if obs_f in result_library:
            print("Result already computed in result_library. Not recomputing.")
            print("indicated:",result_library[obs_f].indicated)
            continue

        obs_hyp_costs = {}
        hyp_times = {}
        indicated = []
        correct = False
        run_start_time = TIMER.time()
        if os.path.exists(obs_f):
            obs_count = obscure_blind.count_obs_from_file(obs_f, sett.version)

            if obs_count == 0:  # No observations means everything is indicated
                indicated = range(len(hyps))
                obs_hyp_costs = hyp_costs.copy()
                hyp_times = defaultdict(float)  # defaults to 0 because it is 0
                print("Empty observation set.")
            else:
                for hyp in range(len(hyps)):
                    # Compile to planning problem
                    if sett.version == "complex":
                        command = "cd {}; ./../../pr2plan_complex -d ../../{} -i ../../{} -o ../../{} {}".format(folder,domain_f,hyp_problems[hyp],obs_f,DEVNULL)
                        # print(command)
                        os.system(command)

                    elif sett.version == "ignore" or sett.version == "simple" or sett.version == "ordered":
                        command = "cd {}; ./../../pr2plan -d ../../{} -i ../../{} -o ../../{} {}".format(folder, domain_f,hyp_problems[hyp], obs_f, DEVNULL)
                        # print(command)
                        os.system(command)

                    obs_hyp_sol = obs_f.replace(".obs", "_hyp{}.sol".format(hyp))
                    print(optimal_hyp_times[hyp])
                    print(time_limit)
                    _, cost, time = run_planner(folder+"/pr-domain.pddl", folder+"/pr-problem.pddl",obs_hyp_sol,bound=hyp_costs[hyp],timeout_seconds= max( PLAN_TIME_BOUND_FACTOR*optimal_hyp_times[hyp], time_limit) )
                    # Commented out for debugging, but should be uncommented eventually
                    os.system("rm -f {}".format(obs_hyp_sol))

                    print("Hyp {}: cost {} (optimal {}), time {:.10f}".format(hyp, cost,hyp_costs[hyp], time))

                    obs_hyp_costs[hyp] = cost
                    hyp_times[hyp] = time
                    if cost == hyp_costs[hyp]:
                        print("Hypothesis {} indicated!".format(hyp))
                        indicated.append(hyp)
        else:
            print(obs_f, "does not exist. We assume this is an empty observation set.")
            log_error("{} does not exist. We continue, assuming this is an empty observation set. If a bunch of this shows up in error log, you ran a bad test.".format(obs_f))
            print("{} does not exist. We continue, assuming this is an empty observation set. If a bunch of this shows up in error log, you ran a bad test.".format(obs_f))
            indicated = range(len(hyps))
            obs_hyp_costs = hyp_costs.copy()
            hyp_times = defaultdict(float)  # defaults to 0 because it is 0

        time = TIMER.time() - run_start_time
        result_library[obs_f] = (Results(problemname,true_hyp,sett.mode,sett.version,sett.obsv_perc,sett.unord_perc,sett.garble_perc,sett.obs_idx,obs_count,indicated,obs_hyp_costs,time,hyp_times,len(obs_fs),num_orderings_total))
        if result_file is not None:
            write_object_to_file(result_library, result_file)
        print("Time for {} problem {}: {:.10f}".format(sett.version, obs_f, time))

    return result_library, num_runs_so_far

"""Old way of doing settings """
# def write_observations(folder, problemname, obs_per_setting=3, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0),
#                        garble_percs=(0.0, .25), max_num_tot_orders=25):
#     basename = folder + "/" + problemname + "/"
#
#     complex_folder = basename + "complex_observations/"
#     ignore_complex_folder = basename + "ignore_observations/"
#     ignore_most_complex_folder = basename + "simple_observations/"
#     ordered_folder = basename + "order_observations/"
#
#     # Make directories if needed:
#     try:
#         os.makedirs(complex_folder)
#     except FileExistsError:
#         pass
#     try:
#         os.makedirs(ignore_most_complex_folder)
#     except FileExistsError:
#         pass
#     try:
#         os.makedirs(ignore_complex_folder)
#     except FileExistsError:
#         pass
#     try:
#         os.makedirs(ordered_folder)
#     except FileExistsError:
#         pass
#
#     # if mode.upper() == "A": mode = "A"
#     # elif mode.upper().replace(' ','').replace('+','') == "AF": mode = "AF"
#     # else:
#     #     print("Mode not recognized. Bailing out")
#     #     exit(0)
#
#     template_f = basename + "template.pddl"
#     tempfile = basename + "temp_goal.pddl"
#     domain_f = basename + "domain.pddl"
#     optimal_plan_details = basename + "optimal_true.details"
#     optimal_plan_trace = basename + "optimal_true.trace"
#
#     hyps_f = basename + "hyps.dat"
#     hyps = []
#     with open(hyps_f, 'r') as hyps_file:
#         for line in hyps_file:
#             hyps.append(line.replace(',', '\n'))
#     print(hyps)
#     print(len(hyps))
#
#     total_orders = []
#
#     for mode in ("A", "AF"):
#         for true_hyp in range(len(hyps)):
#             fill_template_pddl(template_f, tempfile, hyps[true_hyp])
#             print("Finding optimal plan for unconstrained problem {problemname} (true hyp is {true_hyp})".format(
#                 **locals()))
#             run_planner(domain_f, tempfile, optimal_plan_details, optimal_plan_trace)
#
#             for observed_perc in obsv_percs:
#                 for unordered_perc in unord_percs:
#                     for garble_perc in garble_percs:
#                         for idx in range(obs_per_setting):
#                             obsv_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
#                             obs_f = "{problemname}_hyp{true_hyp}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}.obs".format(
#                                 **locals())
#                             print("Writing ", obs_f)
#                             optimal_steps, optimal_cost, _ = obscure_blind.read_plan_details(optimal_plan_details)
#                             if mode == "A":
#                                 observations = obscure_blind.obscure_A_to_file(complex_folder + obs_f, optimal_steps,
#                                                                                observed_perc, unordered_perc,
#                                                                                garble_perc)
#                             else:  # mode == "AF":
#                                 optimal_trace = obscure_blind.read_trace(optimal_plan_trace)
#                                 observations = obscure_blind.obscure_AF_to_file(complex_folder + obs_f, optimal_steps,
#                                                                                 optimal_trace, observed_perc,
#                                                                                 unordered_perc, garble_perc, .1)
#
#                             ignore_obs = obscure_blind.write_ignore_all_uncertainty_to_file(observations,
#                                                                                             ignore_complex_folder + obs_f)
#                             simple_obs = obscure_blind.write_ignore_most_uncertainty_to_file(observations,
#                                                                                              ignore_most_complex_folder + obs_f)
#
#                             without_fl_or_opt = observations.without_fl_obs()
#                             if without_fl_or_opt is not None:
#                                 without_fl_or_opt = without_fl_or_opt.without_option_groups()
#                             total_orders = without_fl_or_opt.get_all_total_orderings() if without_fl_or_opt is not None else []
#                             num_total_orders = len(total_orders)
#                             print("{} total orders".format(num_total_orders))
#                             os.system("rm -rf {}".format(ordered_folder + obs_f.replace(".obs", "/")))
#                             os.makedirs(ordered_folder + obs_f.replace(".obs", "/"))
#                             write_ordering_info(ordered_folder+obs_f.replace(".obs","/")+obs_f.replace(".obs", ".info"), total_orders, max_num_tot_orders)
#                             if len(total_orders) > max_num_tot_orders:
#                                 total_orders = random.sample(total_orders, max_num_tot_orders)
#                             for i in range(len(total_orders)):
#                                 obscure_blind.write_simple_obs_to_file(total_orders[i],ordered_folder + obs_f.replace(".obs","/")
#                                                                        + obs_f.replace(".obs", "_ord{}.obs".format(i)))
#
#     os.system("rm -f " + tempfile + " " + optimal_plan_details + " " + optimal_plan_trace)
# def evaluate_problem(folder, problemname, versions=("ignore", "simple", "complex"), modes=("A", "AF"),
#                      result_library=None, obs_per_setting=3, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0),
#                      garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
#     if result_library is None:
#         result_library = []
#
#     basename = folder + "/" + problemname + "/"
#
#     complex_folder = basename + "complex_observations/"
#     ignore_complex_folder = basename + "ignore_observations/"
#     ignore_most_complex_folder = basename + "simple_observations/"
#     ordered_folder = basename + "order_observations/"
#
#     domain_f = basename + "domain.pddl"
#     hyps_f = basename + "hyps.dat"
#     template_f = basename + "template.pddl"
#
#     hyp_costs, hyp_problems, hyp_solutions, hyp_traces, optimal_hyp_times, hyps = read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f)
#
#     num_runs_total = (len(hyps) if num_hyps is None else num_hyps) * (
#                 len(versions) - (1 if "ordered" in versions else 0)) * len(modes) * len(obsv_percs) * len(
#         unord_percs) * len(garble_percs) * obs_per_setting
#
#     # Count the files we'll run.
#     if "ordered" in versions:
#         for true_hyp in range(len(hyps) if num_hyps is None else num_hyps):
#             for mode in modes:
#                 for observed_perc in obsv_percs:
#                     for unordered_perc in unord_percs:
#                         for garble_perc in garble_percs:
#                             obsv_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
#                             for idx in range(obs_per_setting):
#                                 obs_folder = ordered_folder + "{problemname}_hyp{true_hyp}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}/".format(
#                                     **locals())
#                                 obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if
#                                           f.endswith(".obs") and os.path.isfile(os.path.join(obs_folder, f))]
#                                 num_runs_total += min(len(obs_fs), max_ordered_obs)
#
#     num_runs_so_far = 0
#     evaluation_start_time = TIMER.time()
#
#     for true_hyp in range(len(hyps) if num_hyps is None else num_hyps):
#         for version in versions:
#             if version == "complex":
#                 the_folder = complex_folder
#             elif version == "ignore":
#                 the_folder = ignore_complex_folder
#             elif version == "simple":
#                 the_folder = ignore_most_complex_folder
#             elif version == "ordered":
#                 the_folder = ordered_folder
#             else:
#                 the_folder = None
#                 print("Evaluation version {} not recognized".format(version))
#                 exit(1)
#
#             for mode in modes:
#                 if mode != "A" and mode != "AF":
#                     print("Mode not recognized. Bailing out")
#                     exit(0)
#                 for observed_perc in obsv_percs:
#                     for unordered_perc in unord_percs:
#                         for garble_perc in garble_percs:
#                             obsv_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
#                             for idx in range(obs_per_setting):
#
#                                 obs_ID = "{problemname}_hyp{true_hyp}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}".format(
#                                     **locals())
#                                 obs_fs = [the_folder + obs_ID + ".obs"]
#                                 num_orderings_total = 1
#                                 if version == "ordered":
#                                     obs_folder = ordered_folder + "{problemname}_hyp{true_hyp}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}/".format(
#                                         **locals())
#                                     obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if
#                                               f.endswith(".obs") and os.path.isfile(os.path.join(obs_folder, f))]
#                                     num_orderings_total, _ = read_ordering_info(obs_folder + "{problemname}_hyp{true_hyp}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}.info".format(**locals()))
#                                     if max_ordered_obs < len(obs_fs):
#                                         obs_fs = random.sample(obs_fs, max_ordered_obs)
#
#                                 for i in range(len(obs_fs)):
#                                     obs_f = obs_fs[i]
#                                     num_runs_so_far += 1
#                                     print("{} of {} runs. {:.3f} minutes so far, {:.3f} etr".format(num_runs_so_far,
#                                                                                                     num_runs_total,
#                                                                                                     (TIMER.time() - evaluation_start_time) / 60,
#                                                                                                     ((TIMER.time() - evaluation_start_time) / num_runs_so_far * (num_runs_total - num_runs_so_far)) / 60))
#                                     print("Observation from ", obs_f)
#
#                                     obs_hyp_costs = {}
#                                     hyp_times = {}
#                                     indicated = []
#                                     correct = False
#                                     start_time = TIMER.time()
#                                     if os.path.exists(obs_f):
#                                         obs_count = obscure_blind.count_obs_from_file(obs_f, version)
#
#                                         if obs_count == 0:  # No observations means everything is indicated
#                                             indicated = range(len(hyps))
#                                             obs_hyp_costs = hyp_costs.copy()
#                                             hyp_times = defaultdict(float)  # defaults to 0 because it is 0
#                                             print("Empty observation set.")
#                                         else:
#                                             for hyp in range(len(hyps)):
#                                                 if version == "complex":
#                                                     os.system("./pr2plan_complex -d {} -i {} -o {} {}".format(domain_f,
#                                                                                                               hyp_problems[
#                                                                                                                   hyp],
#                                                                                                               obs_f,
#                                                                                                               DEVNULL))
#                                                 elif version == "ignore" or version == "simple" or version == "ordered":
#                                                     os.system("./pr2plan -d {} -i {} -o {} {}".format(domain_f,
#                                                                                                       hyp_problems[hyp],
#                                                                                                       obs_f, DEVNULL))
#                                                 obs_hyp_sol = obs_f.replace(".obs", "_hyp{}.solution".format(hyp))
#                                                 _, cost, time = run_planner("pr-domain.pddl", "pr-problem.pddl",
#                                                                             obs_hyp_sol, bound=hyp_costs[hyp])#, timeout_seconds=optimal_hyp_times[hyp]*PLAN_TIME_BOUND_FACTOR)
#                                                 # os.system("rm -f {}".format(obs_hyp_sol))
#
#                                                 print("Hyp {}: cost {}, time {:.10f}".format(hyp, cost, time))
#
#                                                 obs_hyp_costs[hyp] = cost
#                                                 hyp_times[hyp] = time
#                                                 if cost == hyp_costs[hyp]:
#                                                     print("Hypothesis {} indicated!".format(hyp))
#                                                     indicated.append(hyp)
#
#                                         time = TIMER.time() - start_time
#                                         result_library.append(
#                                             Results(problemname, true_hyp, mode, version, observed_perc, unordered_perc,
#                                                     garble_perc, idx, obs_count, indicated, obs_hyp_costs, time,
#                                                     hyp_times, len(obs_fs), num_orderings_total))
#
#                                         print("Time for {} problem {}: {:.10f}".format(version, obs_f, time))
#                                     else:
#                                         print(obs_f, "does not exist.")
#
#     return result_library
#
#
# def evaluate_problems(folder, problemnames, result_library=None, versions=("ignore", "simple", "complex"),
#                       modes=("A", "AF"), obs_per_setting=3, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0),
#                       garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
#     if result_library is None:
#         result_library = []
#
#     for problemname in problemnames:
#         evaluate_problem(folder=folder, problemname=problemname, versions=versions, modes=modes,
#                          result_library=result_library, obs_per_setting=obs_per_setting, obsv_percs=obsv_percs,
#                          unord_percs=unord_percs, garble_percs=garble_percs, num_hyps=num_hyps,
#                          max_ordered_obs=max_ordered_obs)
#
#     return result_library
#
# def evaluate_domains(folder, domain_names=None, versions=("ignore", "simple", "complex"), modes=("A", "AF"),
#                      obs_per_setting=3, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25),
#                      num_hyps=None, max_ordered_obs=25):
#     if domain_names is None:
#         domain_names = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
#
#     domain_results = {}
#     for domain in domain_names:
#         domain_path = folder + domain
#         problems = [p for p in os.listdir(domain_path) if os.path.isdir(os.path.join(domain_path, p))]
#         domain_results[domain] = evaluate_problems(domain_path, problems, result_library=None, versions=versions,
#                                                    modes=modes, obs_per_setting=obs_per_setting, obsv_percs=obsv_percs,
#                                                    unord_percs=unord_percs, garble_percs=garble_percs,
#                                                    num_hyps=num_hyps, max_ordered_obs=max_ordered_obs)
#         print("domain {} and domain_path {} and problems {}".format(domain, domain_path, problems))
#     return domain_results
#
#
# def count_runs_to_evaluate_domains(folder, domain_names=None, versions=("ignore", "simple", "complex"),
#                                    modes=("A", "AF"), obs_per_setting=3, obsv_percs=(1.0, .5, .25),
#                                    unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), num_hyps=None,
#                                    max_ordered_obs=25):
#     total = 0
#     if domain_names is None:
#         domain_names = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
#     for domain in domain_names:
#         domain_path = folder + "/" + domain
#         problems = [p for p in os.listdir(domain_path) if os.path.isdir(os.path.join(domain_path, p))]
#         total += count_runs_to_evaluate_problems(domain_path, problems, versions=versions, modes=modes,
#                                                  obs_per_setting=obs_per_setting, obsv_percs=obsv_percs,
#                                                  unord_percs=unord_percs, garble_percs=garble_percs, num_hyps=num_hyps,
#                                                  max_ordered_obs=max_ordered_obs)
#     return total
#
#
# def count_runs_to_evaluate_problems(folder, problemnames=None, versions=("ignore", "simple", "complex"), modes=("A", "AF"),
#                                     obs_per_setting=3, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0),
#                                     garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
#     if problemnames is None:
#         problemnames = [p for p in os.listdir(folder) if os.path.isdir(os.path.join(folder, p))]
#
#     total = 0
#     for problemname in problemnames:
#         total += count_runs_to_evaluate_problem(folder, problemname, versions=versions, modes=modes,
#                                                 obs_per_setting=obs_per_setting, obsv_percs=obsv_percs,
#                                                 unord_percs=unord_percs, garble_percs=garble_percs, num_hyps=num_hyps,
#                                                 max_ordered_obs=max_ordered_obs)
#     return total
#
#
# def count_runs_to_evaluate_problem(folder, problemname, versions=("ignore", "simple", "complex"), modes=("A", "AF"),
#                                    obs_per_setting=3, obsv_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0),
#                                    garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
#     basename = folder + "/" + problemname + "/"
#     hyps_f = basename + "hyps.dat"
#
#     with open(hyps_f, 'r') as file:
#         hyps = file.read().split("\n")
#
#     num_runs_total = (len(hyps) if num_hyps is None else num_hyps) * (
#                 len(versions) - (1 if "ordered" in versions else 0)) * len(modes) * len(obsv_percs) * len(
#         unord_percs) * len(garble_percs) * obs_per_setting
#
#     # Count the files we'll run.
#     if "ordered" in versions:
#         for true_hyp in range(len(hyps) if num_hyps is None else num_hyps):
#             for mode in modes:
#                 for observed_perc in obsv_percs:
#                     for unordered_perc in unord_percs:
#                         for garble_perc in garble_percs:
#                             obsv_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
#                             for idx in range(obs_per_setting):
#                                 obs_folder = basename + "order_observations/" + "{problemname}_hyp{true_hyp}_{mode}_O{obsv_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}/".format(
#                                     **locals())
#                                 obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if
#                                           os.path.isfile(os.path.join(obs_folder, f)) and f.endswith(".obs")]
#                                 num_runs_total += min(len(obs_fs), max_ordered_obs)
#     return num_runs_total
# def write_observations_for_problems(folder, problemnames,obs_per_setting=3, obsv_percs=(1.0, .5, .25),
#                                     unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), max_num_tot_orders=25):
#     if problemnames is None:
#         problemnames = [p for p in os.listdir(folder) if os.path.isdir(os.path.join(folder, p))]
#     for problemname in problemnames:
#         print("\nProblem: {}\n".format(problemname))
#         write_observations(folder=folder,problemname=problemname,obs_per_setting=obs_per_setting,obsv_percs=obsv_percs,
#                            unord_percs=unord_percs,garble_percs=garble_percs,max_num_tot_orders=max_num_tot_orders)
#
# def write_observations_domains(folder, domain_names=None, obs_per_setting=3, obsv_percs=(1.0, .5, .25),
#                                    unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), num_hyps=None,
#                                    max_num_tot_orders=25):
#     if domain_names is None:
#         domain_names = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
#     for domain in domain_names:
#         domain_path = folder + "/" + domain
#         problems = [p for p in os.listdir(domain_path) if os.path.isdir(os.path.join(domain_path, p))]
#         write_observations_for_problems(domain_path, problems, obs_per_setting=obs_per_setting, obsv_percs=obsv_percs,
#                                         unord_percs=unord_percs, garble_percs=garble_percs,max_num_tot_orders=max_num_tot_orders)


def run_domain(domain, settings, problemnames=None, time=PLAN_TIME_LIMIT_MIN):
    """Assumes you've already got the observation files in place."""
    folder = "Benchmark_Problems/" + domain

    evaluate_domain(folder, settings,problemnames, result_file=folder + "/results.object", time_limit=time)



if __name__ == '__main__':

    # results = get_object_from_file("block-words-results.object")
    # write_results_CSV("block-words-results.csv", results)

    # results = get_object_from_file("Benchmark_Problems/block-words/big_results.object")
    # extracted_results = Extracted_Results(results)
    # print(extracted_results.overall_avg_time)
    #
    # giant_sett = make_giant_settings()
    # norm_sett = make_settings()
    # domains = ["Benchmark_Problems/easy-ipc-grid"]
    # est_minutes = [1,1,1,1]
    # print(min(minutes * count_runs_domain(domain, giant_sett)  for domain, minutes in zip(domains, est_minutes)))
    # print(min(minutes * count_runs_domain(domain, norm_sett)  for domain, minutes in zip(domains, est_minutes)))

    # settings = make_settings()
    # write_observation_domain_settings(settings,"Benchmark_Problems/block-words")
    # write_observation_domain_settings(settings,"Benchmark_Problems/easy-grid-navigation")
    # write_observation_domain_settings(settings,"Benchmark_Problems/easy-ipc-grid")
    # write_observation_domain_settings(settings,"Benchmark_Problems/logistics")

    # basenames = ["Benchmark_Problems/block-words/block-words_p01/",
    #              "Benchmark_Problems/block-words/block-words_p02/",
    #              "Benchmark_Problems/block-words/block-words_p03/"]
    # basenames += ["Benchmark_Problems/easy-grid-navigation/easy-grid-navigation_p01/",
    #              "Benchmark_Problems/easy-grid-navigation/easy-grid-navigation_p02/",
    #              "Benchmark_Problems/easy-grid-navigation/easy-grid-navigation_p03/",
    #              "Benchmark_Problems/easy-grid-navigation/easy-grid-navigation_p04/",
    #              "Benchmark_Problems/easy-grid-navigation/easy-grid-navigation_p05/"]
    # basenames += ["Benchmark_Problems/easy-ipc-grid/easy-ipc-grid_p5-5-5/",
    #              "Benchmark_Problems/easy-ipc-grid/easy-ipc-grid_p5-10-10/",
    #              "Benchmark_Problems/easy-ipc-grid/easy-ipc-grid_p10-5-5/",
    #              "Benchmark_Problems/easy-ipc-grid/easy-ipc-grid_p10-10-10/"]
    # basenames += ["Benchmark_Problems/logistics/logistics_p01/",
    #              "Benchmark_Problems/logistics/logistics_p02/",
    #              "Benchmark_Problems/logistics/logistics_p03/"]
    # for basename in basenames:
    #     domain_f = basename+ "domain.pddl"
    #     hyps_f = basename+ "hyps.dat"
    #     template_f = basename+ "template.pddl"
    #     og_hyp_costs, hyp_problems, hyp_solutions, hyp_traces, optimal_hyp_times, hyps = read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f)
    #     print(og_hyp_costs)
    #     os.system("rm -r {}_hypotheses".format(basename))
    #     new_hyp_costs, hyp_problems, hyp_solutions, hyp_traces, optimal_hyp_times, hyps = read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f)
    #     print(new_hyp_costs)
    #     print([x-y for x,y in zip(og_hyp_costs,new_hyp_costs) ])


    parser = argparse.ArgumentParser(description="Evaluate a domain, or process the results from a run")
    parser.add_argument('domain', default='block-words', nargs='?', help="Choices: ['block-words', 'easy-grid-navigation', 'easy-ipc-grid', 'logistics'] ")
    parser.add_argument('--problems', default=None, help='Optionally choose problem(s) within the domain to evaluate.', nargs='*')
    parser.add_argument('--time', type=float, default=PLAN_TIME_LIMIT_MIN, help='Minimum time limit given to planning processes. Default {}'.format(PLAN_TIME_LIMIT_MIN) )
    parser.add_argument('--settings', default="full", choices=["full", "simple", "tiny", "giant"], help='What settings to evaluate on (defaults to a full evaluation)')
    parser.add_argument('--max_ordered', default=25, help="The maximum number of total-orders to sample, when evaluating the 'ordered' tactic. Defaults to 25. Will use less if not enough total-order observations available.")
    parser.add_argument('--process', const='USE_DOMAIN', nargs='?', help='Process and report the results for this domain, or a specified file (Evaluates if flag not present)')
    args = parser.parse_args()
    print(args)
    if args.settings == "simple":
        settings = make_small_settings()
    elif args.settings == "full":
        settings = make_settings()
    elif args.settings == "giant":
        settings = make_giant_settings()
    else:
        settings = make_tiny_settings()
    if args.process is not None:
        result_file = "Benchmark_Problems/" + args.domain + "/results.object" if args.process == "USE_DOMAIN" else args.process
        print("Processing results from '{}'.".format(result_file))
        results = get_object_from_file(result_file)
        for r in results.values():
            if r.version != "ordered" and not r.is_correct:
                print("NON-OPTIMAL PLANNER WARNING: \n\t" + str(r).replace("\n","\n\t"))
        extracted = Extracted_Results(results)
        print(extracted.format_results_blind())
    else:
        if args.problems is None:
            print("Running domain '{}', which will take {} runs. Results will be regularly updated to a 'results.object' in the domain's directory.".format(args.domain, count_runs_domain("Benchmark_Problems/"+args.domain, settings, args.problems, max_ordered=args.max_ordered)))
        else:
            print("Running problems {} in domain '{}', which will take {} runs. Results will be regularly updated to a 'results.object' in the domain's directory.".format(args.problems, args.domain,count_runs_domain("Benchmark_Problems/" + args.domain, settings, args.problems, max_ordered=args.max_ordered)))
        run_domain(args.domain, settings, args.problems, args.time)