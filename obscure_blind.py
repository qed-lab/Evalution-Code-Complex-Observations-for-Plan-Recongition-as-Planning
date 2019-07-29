
import random
from math import ceil, factorial
import re
import os


class unordered_group:
    def __init__(self, members):
        self.members = members
    def __str__(self):
        return "{\n" + ",\n".join([str(mem) for mem in self.members]) + "\n}"
    def __len__(self):
        return sum(len(memb) for memb in self.members)
    def without_fl_obs(self):
        group = unordered_group(list(filter(lambda mem: mem.without_fl_obs() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group
    def without_option_groups(self):
        group = unordered_group(list(filter(lambda mem: mem.without_option_groups() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group
    def without_unordered_groups(self):
        return None

class option_group:
    def __init__(self, members):
        self.members = members
    def __str__(self):
        return "|\n" + ",\n".join([str(mem) for mem in self.members]) + "\n|"
    def __len__(self):
        return 1
    def without_fl_obs(self):
        group = option_group(list(filter(lambda mem: mem.without_fl_obs() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group
    def without_option_groups(self):
        return None
    def without_unordered_groups(self):
        group = option_group(list(filter(lambda mem: mem.without_unordered_groups() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group

class ordered_group:
    def __init__(self, members):
        self.members = members
    def __str__(self):
        return "[\n" + ",\n".join([str(mem) for mem in self.members]) + "\n]"
    def __len__(self):
        return sum(len(memb) for memb in self.members)
    def without_fl_obs(self):
        group = ordered_group(list(filter(lambda mem: mem.without_fl_obs() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group

    def without_option_groups(self):
        group = ordered_group(list(filter(lambda mem: mem.without_option_groups() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group
    def without_unordered_groups(self):
        group = ordered_group(list(filter(lambda mem: mem.without_unordered_groups() is not None, self.members)))
        if len(group.members) == 0:
            return None
        if len(group.members) == 1:
            return group.members[0]
        return group

class action_observation:
    def __init__(self, action): # set of strings
        self.action = action
    def __str__(self):
        return "(" + " ".join(self.action) + ")"
    def __len__(self):
        return 1
    def without_fl_obs(self):
        return self
    def without_option_groups(self):
        if '?' not in self.action:
            return self
        else:
            return None
    def without_unordered_groups(self):
        return self

class fluent_observation:
    def __init__(self, fluents):
        self.fluents = fluents
    def __str__(self):
        str = "~" + " ^ ".join( ["("+ " ".join(fl) + ")" for fl in self.fluents] ) + "~"
        return str
    def __len__(self):
        return 1
    def without_fl_obs(self):
        return None
    def without_option_groups(self):
        return self
    def without_unordered_groups(self):
        return self


def read_plan_details(solution_filename):
    steps = []
    cost = None
    with open(solution_filename, 'r') as file:
        for line_count, line in enumerate(file):
            step_matcher = re.match(r'[0-9]*\. \((.*)\)', line)
            cost_matcher = re.match(r'Plan found with cost: ([0-9]*)', line)
            if step_matcher is not None:
                # print(step_matcher.group())
                step = step_matcher.group(1)
                step = action_observation(step.split())
                steps.append(step)
            elif cost_matcher is not None:
                cost = int(cost_matcher.group(1))
    return steps, cost

def read_trace(trace_filename):
    trace = []
    with open(trace_filename, 'r') as trace_file:
        for line_count, line in enumerate(trace_file):
            fluents = [ fl.strip(" ()").split() for fl in line.split(',')]
            trace.append(fluent_observation( fluents))
    return trace


def count_obs_from_file(filename):
    return len(read_complex_obs(filename))

def read_complex_obs(filename):

    with open(filename, 'r') as file:
        observations = file.read()
        print(observations)
        # if observations.strip()[0] != '[': # list is assumed if not present. Accounts for pr2plan-style observation files
        #     begin = "["
        # if observations.strip()[-1] != ']':
        #     end = "]"
        # print(begin + observations + end)
        return parse_complex_obs("["+ observations + "]")

def parse_complex_obs(observation_string):
    if len(observation_string) == 0:
        return ordered_group([])
    obs_s = observation_string.strip()
    if obs_s[0] == '[' and obs_s[-1] == ']':
        members = [parse_complex_obs(memb) for memb in obs_s.strip("[]").split(',')]
        return ordered_group(members)
    elif obs_s[0] == '{' and obs_s[-1] == '}':
        members = [parse_complex_obs(memb) for memb in obs_s.strip("{}").split(',')]
        return unordered_group(members)
    elif obs_s[0] == '|' and obs_s[-1] == '|':
        members = [parse_complex_obs(memb) for memb in obs_s.strip("|").split(',')]
        return option_group(members)
    elif obs_s[0] == '~' and obs_s[-1] == '~':
        fluents = [ memb.strip(" \t\n()") for memb in obs_s.strip("~").split('^')]
        return fluent_observation(fluents)
    else:
        return action_observation(obs_s.strip("() \t\n"))

# does not return with the first and goal states
def merge_steps_and_states(steps, states):

    if len(steps) != len(states):
        return None

    merged_list = []
    for i in range(len(steps)):
        merged_list.append(steps[i])
        merged_list.append(states[i])
    return merged_list[:-1]



def obscure_states_positive_fl(states, visibility=.5):
    visible_states = []
    intermediate_states = states
    for state in intermediate_states:
        visible_amount = int(ceil(len(state.fluents) * visibility))
        obscured_state = random.sample(state.fluents, visible_amount)
        visible_states.append(fluent_observation(obscured_state))

    return visible_states

# def obscure_states_new_fl(states, visibility=.5):
#
#     lost_fluent_states = []
#     with_lost_fluents = []
#
#     last_state = states[0]
#     for i in range(1,len(states)):
#         lost_fluents = last_state - states[i]
#         negated = set()
#         for fluent in lost_fluents:
#             negated.add(( ('not',) + fluent ))
#         lost_fluent_states.append(negated)
#         last_state = states[i]
#
#     combined_states = []
#     for i in range(1,len(states)-1):
#         combined = states[i].union(lost_fluent_states[i-1])
#         visible_amount = int(ceil(len(combined)*visibility))
#         combined_states.append(random.sample(combined, visible_amount))
#
#     return combined_states

# def make_option_group(observed_action, domain_prob):
#     deleted_param = random.sample(list(observed_action.variable_list), 1)[0]
#     # print(deleted_param)
#     blank_op = domain_prob.domain.operators[observed_action.operator_name]
#     typ = blank_op.variable_list[deleted_param]
#     alternative_params = [var for var, v_type in domain_prob.problem.objects.items() if v_type == typ]
#
#     alternative_ops = set()
#     for alt in alternative_params:
#         new_variables = observed_action.variable_list
#         new_variables[deleted_param] = alt
#         new_op = plan_tracer.instantiate_action(blank_op, list(new_variables.values()))
#         alternative_ops.add(new_op)
#
#     return option_group(alternative_ops)

def write_ignore_all_uncertainty_to_file(obs_group, file):

    if not isinstance(obs_group, ordered_group):
        print("Tried to write a not ordered group to file for previous work eval.")
        exit(1)

    obs_group = obs_group.without_fl_obs()
    if obs_group is not None:
        obs_group = obs_group.without_option_groups()
    if obs_group is not None:
        obs_group = obs_group.without_unordered_groups()

    if obs_group is None:
        return obs_group

    with open(file, 'w') as out:
        if isinstance(obs_group, ordered_group):
            for obs in obs_group.members:
                if not isinstance(obs, action_observation):
                    print("Non-action observation found in supposedly simplified ordered group.")
                    exit(1)
                out.write(str(obs) + "\n")
        elif isinstance(obs_group, action_observation):
            out.write(str(obs_group))

    return obs_group



def obscure_AF(steps, states, observed_perc, unordered_perc, garble_perc, fluent_visibility):

    states = obscure_states_positive_fl(states, fluent_visibility)

    observations = merge_steps_and_states(steps, states)

    observed_amount = int(ceil(len(observations) * observed_perc))
    observed_indices = sorted(random.sample(range(len(observations)), observed_amount))
    observations = [observations[idx] for idx in observed_indices]

    garbled_amount = int(ceil(len(observations) * garble_perc))
    num_actions = len(list(filter(lambda o: isinstance(o,action_observation), observations)))
    garbled_amount = min(garbled_amount, num_actions)
    # garbled_indices = random.sample(range(0,len(observations)))
    garbled_indices = set()
    while len(garbled_indices) < garbled_amount:
        rand_idx = random.randint(0,len(observations)-1)
        if isinstance(observations[rand_idx], action_observation):
            if len(observations[rand_idx].action) > 1:
                garbled_indices.add(rand_idx)

    for idx in garbled_indices:
        # observations[idx] = make_option_group(observations[idx], domain_prob)
        deleted_param = random.randint(1,len(observations[idx].action)-1)
        observations[idx].action[deleted_param] = "?"

    fully_obscured = unordered_groups_of_size_about_3(observations, unordered_perc)

    return fully_obscured

def obscure_A(steps : list, observed_perc, unordered_perc, garble_perc):

    observations = steps

    observed_amount = int(ceil(len(observations) * observed_perc))
    observed_indices = sorted(random.sample(range(len(observations)), observed_amount))
    observations = [observations[idx] for idx in observed_indices]

    garbled_amount = int(ceil(len(observations) * garble_perc))
    # garbled_indices = random.sample(range(0,len(observations)))
    garbled_indices = set()
    while len(garbled_indices) < garbled_amount:
        rand_idx = random.randint(0,len(observations)-1)
        if isinstance(observations[rand_idx], action_observation):
            if len(observations[rand_idx].action) > 1:
                garbled_indices.add(rand_idx)

    for idx in garbled_indices:
        # observations[idx] = make_option_group(observations[idx], domain_prob)
        deleted_param = random.randint(1,len(observations[idx].action)-1)
        observations[idx].action[deleted_param] = "?"

    fully_obscured = unordered_groups_of_size_about_3(observations, unordered_perc)

    return  fully_obscured


def obscure_AF_to_file(out_filename, steps, states, observed_perc, unordered_perc, garble_perc, fluent_visibility):
    obscured_steps = obscure_AF(steps, states, observed_perc, unordered_perc, garble_perc, fluent_visibility)
    # observation_string = obs_string(obscured_steps)


    out_file = open(out_filename, "w")
    out_file.write(str(obscured_steps))
    out_file.close()

    return obscured_steps

def obscure_A_to_file(out_filename, steps, observed_perc, unordered_perc, garble_perc):
    obscured_steps = obscure_A(steps, observed_perc, unordered_perc, garble_perc)
    # observation_string = obs_string(obscured_steps)

    out_file = open(out_filename, "w")
    out_file.write(str(obscured_steps))
    out_file.close()

    return obscured_steps

def remove_fluent_obs(obs_group):
    if isinstance(obs_group, set): # fluent obs
        return None
    if isinstance(obs_group, action_observation):
        return obs_group
    if isinstance(obs_group, option_group):
        without_fluents = set()
        for option in obs_group.members:
            if isinstance(option, action_observation):
                without_fluents.add(option)
        if len(without_fluents) > 1:
            return option_group(without_fluents)
        elif len(without_fluents) == 1:
            return without_fluents.pop()
        else:
            return None
    if isinstance(obs_group, unordered_group):
        without_fluents = []
        for member in obs_group.members:
            filtered_member = remove_fluent_obs(member)
            if filtered_member is not None:
                without_fluents.append(filtered_member)
        if len(without_fluents) > 1:
            return unordered_group(without_fluents)
        elif len(without_fluents) == 1:
            return without_fluents[0]
        else:
            return None
    if isinstance(obs_group, list):
        without_fluents = []
        for member in obs_group:
            filtered_member = remove_fluent_obs(member)
            if filtered_member is not None:
                without_fluents.append(filtered_member)
        if len(without_fluents) > 1:
            return without_fluents
        elif len(without_fluents) == 1:
            return without_fluents[0]
        return without_fluents

def remove_option_groups(obs_group):
    if isinstance(obs_group, set): # fluent obs
        return obs_group
    if isinstance(obs_group, action_observation):
        return obs_group
    if isinstance(obs_group, option_group):
            return None
    if isinstance(obs_group, unordered_group):
        without_options = []
        for member in obs_group.members:
            filtered_member = remove_option_groups(member)
            if filtered_member is not None:
                without_options.append(filtered_member)
        if len(without_options) > 1:
            return unordered_group(without_options)
        elif len(without_options) == 1:
            return without_options[0]
        else:
            return None
    if isinstance(obs_group, list):
        without_options = []
        for member in obs_group:
            filtered_member = remove_option_groups(member)
            if filtered_member is not None:
                without_options.append(filtered_member)
        if len(without_options) > 1:
            return without_options
        elif len(without_options) == 1:
            return without_options[0]
        return without_options

def count_total_orderings(obs_group, exclude_options=False):
    if isinstance(obs_group, set): # fluent obs
        return 1
    elif isinstance(obs_group, action_observation):
        return 1
    elif isinstance(obs_group, option_group) and not exclude_options:
        return len(obs_group.members)
    elif isinstance(obs_group, unordered_group):
        factor = 1
        for member in obs_group.members:
            factor *= count_total_orderings(member, exclude_options)
        return factorial(len(obs_group.members)) * factor
    elif isinstance(obs_group, list):
        factor = 1
        for member in obs_group:
            factor *= count_total_orderings(member, exclude_options)
        return factor
    else:
        return 1

def count_orderings_ramirez(obs_group):
    obs_group = remove_fluent_obs(obs_group)

    return count_total_orderings(obs_group,True)


def obs_string(obs_group, indents=""):
    if isinstance(obs_group, option_group): # option group
        return option_group_string(obs_group)

    elif isinstance(obs_group, unordered_group): # unordered group
        indents += "\t"
        s = "{\n" + indents
        for member in obs_group.members:
            s += obs_string(member,indents) + ",\n" + indents
        s = s.strip(", \n" + indents)
        indents = indents[:-1]
        return s + "\n" + indents + "}"

    elif isinstance(obs_group, fluent_observation): # fluents
        s = "~"
        for fl in obs_group.fluents:
            fl_str = ""
            for param in fl:
                fl_str += param + " "
            fl_str = fl_str.strip()
            s += fl_str + '^'
        return s.strip("^ ") + "~"

    elif isinstance(obs_group, ordered_group): # ordered group
        indents += "\t"
        s = "[\n" + indents
        for member in obs_group.members:
            s += obs_string(member,indents) + ",\n" + indents
        s = s.strip(", \n" + indents)
        indents = indents[:-1]
        return s + "\n" + indents + "]"

    elif isinstance(obs_group, action_observation): # action
        return str(obs_group)



def option_group_string(option_group):
    obs_string = "|"
    for option in option_group.members:
        obs_string += str(option) + ", "
    obs_string = obs_string.strip(", ") + "|"
    return obs_string



def unordered_groups_of_size_about_3(steps, unordered_perc):
    class group_int:
        def __init__(self, x):
            self.x = x

    class space_int:
        def __init__(self, x):
            self.x = x

    unordered_amount = int(ceil(len(steps) * unordered_perc))
    leftover_amount = len(steps) - unordered_amount
    # print(unordered_amount)
    if unordered_amount < 2:
        return ordered_group(steps)
    group_sizes = [group_int(3)] * (int(unordered_amount / 3) )
    if unordered_amount % 3 == 2:
        group_sizes.append(group_int(2))
    elif unordered_amount % 3 == 1:
        group_sizes[-1] = group_int(4)

    num_spaces = len(group_sizes)+ 1
    a = [0] + sorted([random.randint(0, leftover_amount) for _ in range(num_spaces - 1)]) + [leftover_amount]
    spaces = [ space_int(a[i + 1] - a[i]) for i in range(len(a) - 1)]

    random.shuffle(group_sizes)
    groups_and_spacing = [spaces[0]]
    for i in range(len(group_sizes)):
        groups_and_spacing.append(group_sizes[i])
        groups_and_spacing.append(spaces[i+1])

    # print(len(steps))
    # print([str(g.x) + ('u' if isinstance(g, group_int) else 's') for g in groups_and_spacing])

    i = 0
    final_result = []
    for group in groups_and_spacing:
        if group.x == 0:
            pass
        elif isinstance(group, group_int):
            final_result.append(unordered_group( steps[i:i+group.x]) )
            i += group.x
        elif isinstance(group, space_int):
            final_result.extend(steps[i:i+group.x])
            i += group.x
    return ordered_group(final_result)


if __name__ == '__main__':
    domain_f = 'TestFiles/block_domain.pddl'
    problem_f = 'TestFiles/block_prob.pddl'
    solution_f = 'optimal.details'

    # domain_prob = plan_tracer.get_domain_problem(domain_f, problem_f)
    # steps, trace, cost = plan_tracer.plan_and_trace_and_cost(solution_f,domain_prob)

    steps, cost = read_plan_details(solution_f)
    # for step in steps:
    #     print(plan_tracer.action_name(step), end=", ")
    # print()

    # veiled_fluents = obscure_states_new_fl(trace)
    # for state in veiled_fluents:
    #     print(state)

    # obscured_obs = obscure_AF(steps, trace, 1, 1, 0.25, .5)
    # obscured_removing_fluents = remove_fluent_obs(obscured_obs)
    obscured_steps = obscure_A(steps, 1, 1, 0.25)
    print(cost)
    # print(obs_string(obscured_obs))
    # print("With fluents and option groups: ", count_total_orderings(obscured_obs, False))
    # print(obs_string(obscured_removing_fluents))
    # print("Without fluents and with option groups: ", count_total_orderings(obscured_removing_fluents,False))
    # print("Without fluents and without option groups: ", count_orderings_ramirez(obscured_obs))
    print(obs_string(obscured_steps), "\n\n")
    print(str(obscured_steps))
    # print("With option groups: ", count_total_orderings(obscured_steps,False))
    # print("Without option groups: ", count_orderings_ramirez(obscured_steps))

    # print(unordered_groups_of_size_about_3( [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16] , .01))

    # print(str(read_complex_obs("")))

    # exit(1)



