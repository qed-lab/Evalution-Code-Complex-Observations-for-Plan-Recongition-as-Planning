
import obscure_blind
import os
from collections import defaultdict
import time as TIMER
from sys import stdout
import pickle
import random

DEVNULL = " > /dev/null"
# DEVNULL = " "


class Results:
    def __init__(self, problem, true_hyp, mode, version, observed_perc, unordered_perc, garble_perc, obs_idx,
                 obs_count, indicated = None, costs_of_hyps_with_obs=None, time=None, hyp_times=None):
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
        self.is_correct = (true_hyp in indicated) if indicated is not None else None

    def fill_result(self, indicated , hyp_observation_costs, time, hyp_times):
        self.indicated = indicated
        self.time = time
        self.hyp_times = hyp_times
        self.is_correct = (self.true_hyp in self.indicated) if indicated is not None else None
        self.costs_of_hyps_with_obs = hyp_observation_costs

    def __str__(self):
        identifiers =  "Problem: {self.problem} hyp {self.true_hyp}\tVersion: {self.version}\tMode: {self.mode}\n" \
               "Setting: O:{self.observed_perc:.0%} U:{self.unordered_perc:.0%} B:{self.garble_perc:.0%} Observation {self.obs_idx}" \
               "\t({self.obs_count} observations nested)".format(**locals())
        if self.is_correct is not None:
            identifiers += "\n\t{ind_size} indicated hypotheses: {self.indicated}\n" \
                           "\tTime: {self.time:.5f}\n" \
                           "\t {was_or_not} correct.".format(ind_size=len(self.indicated), **locals(), was_or_not="Was" if self.is_correct else "Wasn't")
        return identifiers + "\n"

def write_object_to_file(object, filename):
    with open(filename, 'wb') as file:
        pickle.dump(object, file)
def get_object_from_file(filename):
    with open(filename, 'rb') as file:
        return pickle.load(file)

def run_planner(domain, problem, output_file='execution.details', trace_file=os.devnull, timeout_seconds=None, bound=None):

    if not os.path.exists(domain):
        print("Domain file <" + domain + "> does not exist.")
    if not os.path.exists(problem):
        print("Problem file <" + problem + "> does not exist.")

    cmd = "./planner --domain {} --problem {} --output {} --trace_output {} ".format(domain, problem, output_file, trace_file)
    if timeout_seconds is not None:
        cmd += " --time {} ".format(timeout_seconds)
    if bound is not None:
        cmd += " --bound {} ".format(bound)
    # print(cmd + DEVNULL)
    start_time = TIMER.time()
    os.system(cmd + DEVNULL)
    time = TIMER.time() - start_time

    plan, cost = obscure_blind.read_plan_details(output_file)
    return plan, cost, time



def write_observations(folder, problemname, obs_per_setting=3, obs_percs=(1.0,.5,.25), unord_percs=(0.0,.5,1.0), garble_percs=(0.0,.25)):

    basename = folder+"/"+problemname+"/"

    complex_folder = basename +"complex_observations/"
    ignore_complex_folder = basename +"ignore_observations/"
    ignore_most_complex_folder = basename +"simple_observations/"
    ordered_folder = basename +"order_observations/"

    # Make diretories if needed:
    try:
        os.makedirs(complex_folder)
    except FileExistsError:
        pass
    try:
        os.makedirs(ignore_most_complex_folder)
    except FileExistsError:
        pass
    try:
        os.makedirs(ignore_complex_folder)
    except FileExistsError:
        pass
    try:
        os.makedirs(ordered_folder)
    except FileExistsError:
        pass

    # if mode.upper() == "A": mode = "A"
    # elif mode.upper().replace(' ','').replace('+','') == "AF": mode = "AF"
    # else:
    #     print("Mode not recognized. Bailing out")
    #     exit(0)

    template_f = basename+"template.pddl"
    tempfile = basename+"temp_goal.pddl"
    domain_f = basename+"domain.pddl"
    optimal_plan_details =  basename + "optimal_true.details"
    optimal_plan_trace =  basename + "optimal_true.trace"

    hyps_f = basename + "hyps.dat"
    hyps = []
    with open(hyps_f, 'r') as hyps_file:
        for line in hyps_file:
            hyps.append(line.replace(',', '\n'))
    print(hyps)
    print(len(hyps))

    total_orders = []

    for mode in ("A","AF"):
        for true_hyp in range(len(hyps)):
            fill_template_pddl(template_f, tempfile, hyps[true_hyp])
            print("Finding optimal plan for unconstrained problem {problemname} (true hyp is {true_hyp})".format(**locals()))
            run_planner(domain_f, tempfile, optimal_plan_details, optimal_plan_trace)

            for observed_perc in obs_percs:
                for unordered_perc in unord_percs:
                    for garble_perc in garble_percs:
                        for idx in range(obs_per_setting):
                            obs_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                            obs_f = "{problemname}_hyp{true_hyp}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}.obs".format(**locals())
                            print("Writing ", obs_f)
                            optimal_steps, optimal_cost = obscure_blind.read_plan_details(optimal_plan_details)
                            if mode == "A":
                                observations = obscure_blind.obscure_A_to_file(complex_folder + obs_f, optimal_steps, observed_perc, unordered_perc, garble_perc)
                            else:# mode == "AF":
                                optimal_trace = obscure_blind.read_trace(optimal_plan_trace)
                                observations = obscure_blind.obscure_AF_to_file(complex_folder + obs_f, optimal_steps, optimal_trace, observed_perc,unordered_perc, garble_perc, .1)


                            ignore_obs = obscure_blind.write_ignore_all_uncertainty_to_file(observations, ignore_complex_folder + obs_f)
                            simple_obs = obscure_blind.write_ignore_most_uncertainty_to_file(observations, ignore_most_complex_folder+obs_f)

                            without_fl_or_opt = observations.without_fl_obs()
                            if without_fl_or_opt is not None:
                                without_fl_or_opt = without_fl_or_opt.without_option_groups()
                            total_orders = without_fl_or_opt.get_all_total_orderings() if without_fl_or_opt is not None else []
                            num_total_orders = len(total_orders)
                            print("{} total orders".format(num_total_orders))
                            os.system("rm -rf {}".format(ordered_folder + obs_f.replace(".obs", "/")))
                            os.makedirs(ordered_folder + obs_f.replace(".obs", "/"))
                            for i in range(len(total_orders)):
                                obscure_blind.write_simple_obs_to_file(total_orders[i], ordered_folder + obs_f.replace(".obs", "/") + obs_f.replace(".obs", "_ord{}.obs".format(i)) )

    os.system("rm -f "+ tempfile + " " + optimal_plan_details + " " + optimal_plan_trace)



def evaluate_problem(folder, problemname, versions=("ignore","simple","complex"), modes=("A","AF"), result_library=None, obs_per_setting=3, obs_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
    if result_library is None:
        result_library = {}


    basename = folder + "/" + problemname + "/"

    complex_folder = basename +"complex_observations/"
    ignore_complex_folder = basename +"ignore_observations/"
    ignore_most_complex_folder = basename +"simple_observations/"
    ordered_folder = basename +"order_observations/"

    domain_f = basename + "domain.pddl"
    hyps_f = basename + "hyps.dat"
    template_f = basename + "template.pddl"


    hyp_costs, hyp_problems, hyps = read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f)

    num_runs_total = (len(hyps) if num_hyps is None else num_hyps) * (len(versions) - (1 if "ordered" in versions else 0)) * len(modes) * len(obs_percs) * len(unord_percs) * len(garble_percs) *obs_per_setting

    # Count the files we'll run.
    if "ordered" in versions:
        for true_hyp in range(len(hyps) if num_hyps is None else num_hyps):
            for mode in modes:
                for observed_perc in obs_percs:
                    for unordered_perc in unord_percs:
                        for garble_perc in garble_percs:
                            obs_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                            for idx in range(obs_per_setting):
                                obs_folder = ordered_folder + "{problemname}_hyp{true_hyp}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}/".format(**locals())
                                obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if os.path.isfile(os.path.join(obs_folder, f))]
                                num_runs_total += min(len(obs_fs), max_ordered_obs)

    num_runs_so_far = 0
    evaluation_start_time = TIMER.time()

    for true_hyp in range(len(hyps) if num_hyps is None else num_hyps):
        for version in versions:
            if version == "complex":
                the_folder = complex_folder
            elif version == "ignore":
                the_folder = ignore_complex_folder
            elif version == "simple":
                the_folder = ignore_most_complex_folder
            elif version == "ordered":
                the_folder = ordered_folder
            else:
                print("Evaluation version {} not recognized".format(version))
                exit(1)

            for mode in modes:
                if mode != "A" and mode != "AF":
                    print("Mode not recognized. Bailing out")
                    exit(0)
                for observed_perc in obs_percs:
                    for unordered_perc in unord_percs:
                        for garble_perc in garble_percs:
                            obs_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                            for idx in range(obs_per_setting):

                                obs_ID = "{problemname}_hyp{true_hyp}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}".format(**locals())
                                obs_fs = [the_folder+obs_ID+".obs"]
                                if version == "ordered":
                                    obs_folder = ordered_folder + "{problemname}_hyp{true_hyp}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}_{idx}/".format(**locals())
                                    obs_fs = [os.path.join(obs_folder, f) for f in os.listdir(obs_folder) if os.path.isfile(os.path.join(obs_folder, f))]
                                    if max_ordered_obs < len(obs_fs):
                                        obs_fs = random.sample(obs_fs, max_ordered_obs)

                                for i in range(len(obs_fs)):
                                    obs_f = obs_fs[i]
                                    num_runs_so_far+=1
                                    print("{} of {} runs. {:.3f} minutes so far, {:.3f} etr".format(num_runs_so_far, num_runs_total, (TIMER.time() - evaluation_start_time)/60, ((TIMER.time() - evaluation_start_time)/num_runs_so_far * (num_runs_total-num_runs_so_far) )/60))
                                    print("Observation from ", obs_f)

                                    obs_hyp_costs = {}
                                    hyp_times = {}
                                    indicated = []
                                    correct = False
                                    start_time = TIMER.time()
                                    if os.path.exists(obs_f) :
                                        obs_count =  obscure_blind.count_obs_from_file(obs_f, version)

                                        if obs_count == 0: # No observations means everything is indicated
                                            indicated = range(len(hyps))
                                            obs_hyp_costs = hyp_costs.copy()
                                            hyp_times = defaultdict(float) # defaults to 0 because it is 0
                                            print("Empty observation set.")
                                        else:
                                            for hyp in range(len(hyps)):
                                                if version == "complex":
                                                    os.system("./pr2plan_complex -d {} -i {} -o {} {}".format(domain_f, hyp_problems[hyp], obs_f, DEVNULL))
                                                elif version == "ignore" or version == "simple" or version == "ordered":
                                                    os.system("./pr2plan -d {} -i {} -o {} {}".format(domain_f, hyp_problems[hyp], obs_f, DEVNULL))
                                                obs_hyp_sol = obs_f.replace(".obs", "_hyp{}.solution".format(hyp))
                                                _, cost, time = run_planner("pr-domain.pddl", "pr-problem.pddl", obs_hyp_sol, bound=hyp_costs[hyp])
                                                # os.system("rm -f {}".format(obs_hyp_sol))

                                                print("Hyp {}: cost {}, time {:.10f}".format(hyp, cost, time))

                                                obs_hyp_costs[hyp] = cost
                                                hyp_times[hyp] = time
                                                if cost == hyp_costs[hyp] :
                                                    print("Hypothesis {} indicated!".format(hyp))
                                                    indicated.append(hyp)
                                                    # if hyp == correct_hyp:
                                                    #     correct = True
                                        time = TIMER.time()-start_time
                                        result_idx = "{problemname}_hyp{true_hyp}_{version}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
                                        if len(obs_fs) != 0:
                                            result_idx += "_{}".format(i)
                                        result_library[result_idx] = Results(problemname,true_hyp,mode,version,observed_perc,unordered_perc,garble_perc,idx,obs_count,indicated,obs_hyp_costs,time,hyp_times)

                                        print( "Time for {} problem {}: {:.10f}".format(version, obs_f, time))
                                    else:
                                        print(obs_f, "does not exist.")

    return result_library


def read_hypotheses_and_get_costs(basename, domain_f, hyps_f, template_f):
    hyps = []
    with open(hyps_f, 'r') as hyps_file:
        for line in hyps_file:
            hyps.append(line.replace(',', '\n'))
            # if set(fl.strip() for fl in true_hyp_str.split("\n")) == set(fl.strip() for fl in hyps[-1].split("\n")):
            #     true_hyp = len(hyps)-1
    hyp_costs = []
    hyp_problems = []

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
        if not os.path.exists(hyp_sol):
            _, cost, _ = run_planner(domain_f, hyp_problem, hyp_sol)
            os.system("rm {}".format(hyp_problem))
        else:
            _, cost = obscure_blind.read_plan_details(hyp_sol)
        hyp_costs.append(cost)
    return hyp_costs, hyp_problems, hyps


def evaluate_problems( folder, problemnames, result_library=None, versions=("ignore", "simple", "complex"), modes = ("A","AF"), obs_per_setting=3, obs_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
    if result_library is None:
        result_library = {}

    for problemname in problemnames:
        evaluate_problem(folder=folder,problemname=problemname,versions=versions,modes=modes,result_library=result_library, obs_per_setting=obs_per_setting, obs_percs=obs_percs, unord_percs=unord_percs, garble_percs=garble_percs, num_hyps=num_hyps,max_ordered_obs=max_ordered_obs)

    return result_library

def evaluate_domains(folder, domain_names=None,  versions=("ignore", "simple", "complex"), modes = ("A","AF"), obs_per_setting=3, obs_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), num_hyps=None, max_ordered_obs=25):
    if domain_names is None:
        domain_names = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder,d))]

    domain_results = {}
    for domain in domain_names:
        domain_path = folder + domain
        problems = [p for p in os.listdir(domain_path) if os.path.isdir(os.path.join(domain_path, p))]
        domain_results[domain] = evaluate_problems(domain_path, problems,result_library=None,versions=versions,modes=modes,obs_per_setting=obs_per_setting,obs_percs=obs_percs,unord_percs=unord_percs,garble_percs=garble_percs,num_hyps=num_hyps,max_ordered_obs=max_ordered_obs)
        print("domain {} and domain_path {} and problems {}".format(domain,domain_path,problems))
    return domain_results

def extract_results(result_library: dict):

    num_results = defaultdict(float)
    overall_avg_time = 0

    avg_obs_sizes = defaultdict(float)
    avg_times = defaultdict(float)
    avg_correctness = defaultdict(float)
    avg_size_of_indicated = defaultdict(float)



    for key, result in result_library.items():
        obs_perc_big, un_perc_big, garb_perc_big = 100 * result.observed_perc, 100 * result.unordered_perc, 100 * result.garble_perc
        index = "{result.version}_{result.mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
        avg_obs_sizes[index] += result.obs_count
        num_results[index] += 1.0
        avg_times[index] += result.time
        overall_avg_time += result.time
        avg_size_of_indicated[index] += len(result.indicated)
        if result.is_correct:
            avg_correctness[index]+= 1.0

    overall_avg_time /= sum(num_results.values())
    for index in num_results.keys():
        avg_obs_sizes[index] /= num_results[index]
        avg_size_of_indicated[index] /= num_results[index]
        avg_correctness[index] /= num_results[index]
        avg_times[index] /= num_results[index]

    return num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time

def print_extracted_results(num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time,  obs_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), versions=("ignore", "simple", "complex") ,outstream=stdout):

    # outstream.write("||       |       |       ||                    ignore                     ||                    complex                    ||\n"
    #                 "||   O   |   U   |   B   ||           A           |           AF          ||           A           |           AF          ||\n"
    #                 "||       |       |       ||   O   :   C   :   G   |   O   :   C   :   G   ||   O   :   C   :   G   |   O   :   C   :   G   ||\n")
    outstream.write("||       |       |       ||")
    for version in versions:
        outstream.write("{:^47}||".format(version))
    outstream.write("\n||   O   |   U   |   B   ||")
    for version in versions:
        outstream.write("           A           |           AF          ||")
    outstream.write("\n||       |       |       ||")
    for version in versions:
        outstream.write("   O   :   C   :   G   |   O   :   C   :   G   ||")
    outstream.write("\n")
    for observed_perc in obs_percs:
        for unordered_perc in unord_percs:
            for garble_perc in garble_percs:
                obs_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                outstream.write( "||{obs_perc_big:^7.0f}|{un_perc_big:^7.0f}|{garb_perc_big:^7.0f}||".format(**locals()))
                for version in versions:
                    for mode in ["A","AF"]:
                        index = "{version}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
                        obs_size = avg_obs_sizes[index]
                        correctness = avg_correctness[index]
                        ind_size = avg_size_of_indicated[index]
                        outstream.write( "{obs_size:^7.2f}:{correctness:^7.2f}:{ind_size:^7.2f}|".format(**locals()) )
                    outstream.write("|")
                outstream.write("\n")

    outstream.write("\n Avg time per problem, over all settings: {:.5f} seconds".format(overall_avg_time))
    outstream.write("\n Total time for evaluation: {:.5f} seconds".format( overall_avg_time* sum(num_results.values())))

def print_extracted_results_latex(num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time,  obs_percs=(1.0, .5, .25), unord_percs=(0.0, .5, 1.0), garble_percs=(0.0, .25), versions=("ignore", "simple", "complex"), outstream=stdout):

    header = \
    r"""
    \begin{tabular}{|c|c|c|c|c|c|c|c|c|c|c|}
    \hline" \
    \multirow{3}{*}{\textbf{O\%}} & \multirow{3}{*}{\textbf{U\%}} & \multirow{3}{*}{\textbf{B\%}} & \multicolumn{4}{c|}{\textbf{Previous (Ignore Uncertainty)}} & \multicolumn{4}{c|}{\textbf{This}} \\ \cline{4-11}
     &  &  & \multicolumn{2}{c|}{\textbf{A}} & \multicolumn{2}{c|}{\textbf{A+F}} & \multicolumn{2}{c|}{\textbf{A}} & \multicolumn{2}{c|}{\textbf{A+F}} \\ \cline{4-11}
     &  &  & $|O'|$ & $|\G_T^*|$ & $|O'|$ & $|\G_T^*|$ & $|O|$ & $|\G_T^*|$ & $|O|$ & $|\G_T^*|$ \\ \hline
     """

    # outstream.write(header)
    outstream.write(r"\begin{tabular}{|c|c|c")
    for version in versions:
        outstream.write(r"|c|c|c|c")
    outstream.write(r"|}" + "\n" + r"\hline" + "\n" + r"\multirow{3}{*}{\textbf{O\%}} & \multirow{3}{*}{\textbf{U\%}} & \multirow{3}{*}{\textbf{B\%}} ")
    for version in versions:
        if version == "ignore":
            outstream.write(r"& \multicolumn{4}{c|}{\textbf{Previous (Ignore All Uncertainty)}}")
        if version == "simple":
            outstream.write(r"& \multicolumn{4}{c|}{\textbf{Previous (Ignore Most Uncertainty)}}")
        if version == "complex":
            outstream.write(r"& \multicolumn{4}{c|}{\textbf{This}}")
    outstream.write(r"\\ \cline{{4-{}}}".format(3+(4*len(versions))))
    outstream.write("\n&  &  ")
    for version in versions:
        outstream.write(r"& \multicolumn{2}{c|}{\textbf{A}} & \multicolumn{2}{c|}{\textbf{A+F}}")
    outstream.write(r"\\ \cline{{4-{}}}".format(3 + (4 * len(versions))))
    outstream.write("\n&  &  ")
    for version in versions:
        outstream.write(r"& $|O'|$ & $|\G_T^*|$ & $|O'|$ & $|\G_T^*|$ ")
    outstream.write(r"\\ \hline" + "\n")


    # """\multirow{6}{*}{100} & \multirow{2}{*}{0} & 0 & 1* & 00 & .00 & 00 & 1* & 00 & .00 & 00 & 00 & .00 & 00 & 00 & .00 & 00 & 00 & 00 & 00 & 00 \\ \cline{3-21} """
    always_correct = True

    for observed_perc in obs_percs:
        # outstream.write(r"\multirow{{6}}{{*}}{{{observed_perc:.0%}}}".format(**locals))
        for unordered_perc in unord_percs:
            for garble_perc in garble_percs:
                obs_perc_big, un_perc_big, garb_perc_big = 100 * observed_perc, 100 * unordered_perc, 100 * garble_perc
                outstream.write( "{obs_perc_big:^7.0f}&{un_perc_big:^7.0f}&{garb_perc_big:^7.0f}".format(**locals()))
                for version in versions:
                    for mode in ["A","AF"]:
                        index = "{version}_{mode}_O{obs_perc_big:.0f}_U{un_perc_big:.0f}_B{garb_perc_big:.0f}".format(**locals())
                        obs_size = avg_obs_sizes[index]
                        if avg_correctness[index] < 1.0:
                            always_correct = False
                        ind_size = avg_size_of_indicated[index]
                        outstream.write( "&{obs_size:^7.1f}&{ind_size:^7.1f}".format(**locals()) )
                outstream.write(r"\\ \hline")
                outstream.write("\n")
    outstream.write(r"\end{tabular}")
    if not always_correct:
        outstream.write("\n Warning: Did not always indicate the correct hypothesis. It should. This is a bug.")
    outstream.write("\n Avg time per problem, over all settings: {:.5f} seconds".format(overall_avg_time))
    outstream.write("\n Total time for evaluation: {:.5f} seconds".format(overall_avg_time*sum(num_results.values())))


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


if __name__ == '__main__':
    # evaluate_domains("Benchmark_Problems/")

    # write_observations("Benchmark_Problems/block-words", "block-words_p01")
    versions = ["ignore", "simple","complex"]
    ## Quick target
    # obs_percs = (.25,)
    # unord_percs=(.5,)
    # garble_percs=(.25,)
    # obs_per_setting=1
    # num_hyps = 1

    ## Full deal
    # obs_percs = (1.0,.5,.25)
    # unord_percs=(0.0,.5,1.0)
    # garble_percs=(0.0,.25,)
    # obs_per_setting=3
    # num_hyps = None
    # versions = ["simple","complex","ordered"]

    ## 4 settings
    # obs_percs = (.5,.25,)
    # unord_percs=(.0,.5,)
    # garble_percs=(.25,)
    # obs_per_setting=1
    # num_hyps = 1

    ## 3 settings
    # obs_percs = (1.0, .5, .25)
    # unord_percs = (.5,)
    # garble_percs = (.25,)
    # obs_per_setting = 1
    # num_hyps = 1

    ## 3 settings averaging over 6
    # obs_percs = (1.0, .5, .25)
    # unord_percs = (.5,)
    # garble_percs = (.25,)
    # obs_per_setting = 2
    # num_hyps = 3
    # versions=["ordered"]

    ## 2 settings averaging over 3
    # obs_percs = (.5, .25)
    # unord_percs = (.5,)
    # garble_percs = (.25,)
    # obs_per_setting = 3
    # num_hyps = 1

    ## 2 settings with ordering issues
    # obs_percs = (1.0, .5)
    # unord_percs = (1.0,)
    # garble_percs = (0,)
    # obs_per_setting = 1
    # num_hyps = 1
    # versions=["ordered"]


    # 3 settings small orderings
    obs_percs = (1, .5, .25)
    unord_percs = (.5,)
    garble_percs = (0,)
    obs_per_setting = 1
    num_hyps = 1
    versions=["ordered"]

    result_library = evaluate_problem("Benchmark_Problems/block-words", "block-words_p01",versions=versions, obs_percs=obs_percs, unord_percs=unord_percs, garble_percs=garble_percs,obs_per_setting=obs_per_setting, num_hyps=num_hyps)

    for r in result_library.values():
        print(r)

    write_object_to_file(result_library, "TestFiles/results_temp")


    num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time = extract_results(result_library)
    print_extracted_results(num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time,versions=versions, obs_percs=obs_percs, unord_percs=unord_percs, garble_percs=garble_percs)
    print_extracted_results_latex(num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time,versions=versions, obs_percs=obs_percs, unord_percs=unord_percs, garble_percs=garble_percs)

    result_library = get_object_from_file("TestFiles/results_temp")
    print("\nRead from file:")
    num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time = extract_results(result_library)
    print_extracted_results(num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time,versions=versions, obs_percs=obs_percs, unord_percs=unord_percs, garble_percs=garble_percs)
    print_extracted_results_latex(num_results, avg_obs_sizes, avg_times, avg_correctness, avg_size_of_indicated, overall_avg_time,versions=versions, obs_percs=obs_percs, unord_percs=unord_percs, garble_percs=garble_percs)
