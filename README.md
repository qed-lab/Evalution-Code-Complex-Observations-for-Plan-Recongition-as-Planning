

# Evaluation code for: Complex Observations for Plan Recognition as Planning

This program is meant to compare pr2plan (Ramirez and Geffner, 2009)
against pr2plan_complex (Nelson and Cardona-Rivera, 2020) It requires several executables be moved to this directory.
Each of these executables relies on an FF parser, for which bison and flex are required. See the [FF website](https://fai.cs.uni-saarland.de/hoffmann/ff.html)
for more info. You may be able to use [brew](https://brew.sh) for an easy install. (`brew install bison`)

### pr2plan (Ramirez and Geffner, 2009)
See obs-compiler.tar.bz2 found in the main directory, or download [here](https://sites.google.com/site/prasplanning/file-cabinet).
Compile with `cd mod-metric-ff; make libff; cd ..; make all`, and work as best you can through any bugs. It may help
to comment out the STATIC line in the Makefile, as some systems (including Mac) don't like it. When compiled,
 copy the executable 'pr2plan' to this directory. If `make libff` gives you trouble here, likely it will give you the
 same trouble in pr2plan_complex and LAPKT, so take notes of how you fix issues.

### pr2plan_complex
See the complex_observation_compiler folder. Compile with
`cd mod-metric-ff; make libff; cd ..; make all`. When compiled, copy the executable 'pr2plan' to this directory.
 _Please_ report bugs, questions, and compilation issues to its repository [here](https://github.com/qed-lab/Complex-Observation-Compiler).

### Compiling an optimal planner (with tracer)
This evaluation uses a specially built optimal planner that produces a plan-trace. This plan trace was used to generate new complex observations. If you don't need to generate new observations and would like to use your own planner, replace the 'run_planner' function in harness.py with your own interface.
 - Download [LAPKT](http://lapkt.org/index.php?title=Download), and set it up. (LAPKT should have resources. You'll need boost.)
    - Make sure to set up LAPKT's FF parser in 'external/libff', as in [these](http://lapkt.org/index.php?title=GettingStarted)
     instructions. If it has issues finding '/usr/include/<anything>' you may have to remove the explicit paths from the bottom. Regex in an IDE works best for this.

 - Make sure you can use the `scons` command. Brew, or `sudo apt-get` is your friend here, or else look [here](https://scons.org).

- In the planner-tracer directory, open the 'SConstruct' file and update `LAPKT_DIR=`. This can be a relative filepath.

    - You may also have to update 'include_paths' and 'lib_paths' if you have a nonstandard boost installation.

- `scons`

- `mv planner ../planner`


> Alternatively, you could substitute your own planner and replace the 'run_planner' in harness.py function with your own interface.
Make sure this planner also outputs the plan trace to a file. The format uses newlines to separate states, and commas to separate the fluents in a state.


### Running the evaluation:
To run the evaluation run `harness.py`. By default this runs a (lengthy) evaluation on the problems in
`Benchmark_Problems`, and reports the results in both a text table and latex-ready table. This is a long process,
 so feel free to pare down the settings. Just make sure those settings match the .obs files available. (Or generate your own .obs files)

### Analyzing the evaluation:
Results from our run can be found in the pickle files `block-words-results-with-cpx-base.object`, `easy-ipc-grid-results-with-cpx-base.object`, `easy-grid-navigation-results-with-cpx-base.object`, and `logistics1-and-2-combined.object` (logistics was run in two separate processes and combined later).

The analysis from our paper (Nelson and Cardona-Rivera, 2020) was conducted using `analysis.py` and those .object pickle files . It's a mess of commented-out code, but Jenni didn't want to leave any code out that went into the evaluation. This file was used to print the latex table and figures. The file `get_hypothesis_files.py` was used to average the size of the possible goal sets, per domain.
