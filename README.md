

# Evaluation code for: Complex Observations for Plan Recognition as Planning

This program is meant to compare pr2plan (Ramirez and Geffner, 2009) 
against pr2plan_complex (Nelson and Cardona-Rivera, 2019) It requires several executables be moved to this directory. 
Each of these executables relies on an FF parser, for which bison and flex are required. See the [FF website](https://fai.cs.uni-saarland.de/hoffmann/ff.html) 
for more info. Macs should be able to use [brew](https://brew.sh) for an easy install. (`brew install bison`)

### pr2plan
See obs-compiler.tar.bz2 found [here](https://sites.google.com/site/prasplanning/file-cabinet) for download. 
Compile with `cd mod-metric-ff; make libff; cd ..; make all`, and work as best you can through any bugs. When compiled,
 copy the executable 'pr2plan' to this directory. If `make libff` gives you trouble here, likely it will give you the 
 same trouble in pr2plan_complex and LAPKT, so take notes of how you fix issues.

### pr2plan_complex
See [here](https://github.com/qed-lab/Complex-Observation-Compiler) for download. Compile with 
`cd mod-metric-ff; make libff; cd ..; make all`. When compiled, copy the executable 'pr2plan' to this directory.
 _Please_ report bugs and compilation issues to its repository.

### Compiling the planner (with tracer)
 - Download [LAPKT](http://lapkt.org/index.php?title=Download), and make sure you can use the `scons` command. (LAPKT should have resources) 

- In the planner-tracer directory, open the 'SConstruct' file and update `LAPKT_DIR=`. This can be a relative filepath.

- `scons`

- `mv planner ../planner`


> Alternatively, you could substitute your own planner and replace the 'run-wa-planner' function with your own interface. 
Make sure this planner also outputs the plan trace to a file. The format uses newlines to separate states, and commas to separate the fluents in a state.


### Running the evaluation:
To run the evaluation run `harness.py`. By default this runs a (lengthy) evaluation on the problems in 
`Benchmark_Problems`, and reports the results in both a text table and latex-ready table. This is a long process,
 so feel free to pare down the settings. Just make sure those settings match the .obs files available. (Or generate your own .obs files)