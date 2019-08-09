/*
Lightweight Automated Planning Toolkit
Copyright (C) 2012
Miquel Ramirez <miquel.ramirez@rmit.edu.au>
Nir Lipovetzky <nirlipo@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

// MRJ: In this example, I'll try to show how can one assemble a simple
// STRIPS planning problem from objects and data structures through the embedded FF
// parser.
#include <strips_prob.hxx>
#include <ff_to_aptk.hxx>

#include <fluent.hxx>
#include <action.hxx>
#include <cond_eff.hxx>
#include <strips_state.hxx>

#include <fwd_search_prob.hxx>
#include <h_1.hxx>
#include <rp_heuristic.hxx>

#include <aptk/open_list.hxx>
#include "at_bfs_tracer.hxx"

#include <iostream>
#include <iterator>
#include <fstream>

#include <boost/program_options.hpp>

namespace po = boost::program_options;

using   aptk::STRIPS_Problem;
using	aptk::agnostic::Fwd_Search_Problem;

using 	aptk::agnostic::H1_Heuristic;
using	aptk::agnostic::H_Add_Evaluation_Function;
using	aptk::agnostic::H_Max_Evaluation_Function;
using	aptk::agnostic::Relaxed_Plan_Heuristic;


using 	aptk::search::Open_List;
using	aptk::search::Node_Comparer;

using 	aptk::search::bfs_tracer::Node;
using	aptk::search::bfs_tracer::AT_BFS_SQ_SH_TRACER;

// MRJ: We start defining the type of nodes for our planner
typedef		Node< aptk::State >						Search_Node;

// MRJ: Then we define the type of the tie-breaking algorithm
// for the open list we are going to use
typedef		Node_Comparer< Search_Node >					Tie_Breaking_Algorithm;

// MRJ: Now we define the Open List type by combining the types we have defined before
typedef		Open_List< Tie_Breaking_Algorithm, Search_Node >		BFS_Open_List;

// MRJ: Now we define the heuristics we could use
typedef		H1_Heuristic<Fwd_Search_Problem, H_Add_Evaluation_Function>	H_Add_Fwd; // Non-admissible :(
typedef 	H1_Heuristic<Fwd_Search_Problem, H_Max_Evaluation_Function>	H_Max_Fwd; // Admissible?
typedef		Relaxed_Plan_Heuristic< Fwd_Search_Problem, H_Add_Fwd >		H_Add_Rp_Fwd;// Non-admissible :(

// MRJ: Now we're ready to define the BFS algorithm we're going to use
typedef		AT_BFS_SQ_SH_TRACER< Fwd_Search_Problem, H_Max_Fwd, BFS_Open_List >		Anytime_BFS_H_Add_Rp_Fwd;

template <typename Search_Engine>
float do_search( Search_Engine& engine, const STRIPS_Problem& plan_prob, float budget, std::string logfile, std::string tracefile ) {

	std::ofstream out( logfile.c_str() );
	std::ofstream trace_out( tracefile.c_str() );
  // out << "Bound: "<< engine.bound() << std::endl;
	engine.set_budget( budget );
	engine.start();
  out << "Bound: "<< engine.bound() << std::endl;

  std::vector< aptk::Action_Idx > plan;
	std::vector< aptk::State > trace;
	float				cost;

	float ref = aptk::time_used();
	float t0 = aptk::time_used();

	unsigned expanded_0 = engine.expanded();
	unsigned generated_0 = engine.generated();

  std::vector< aptk::Action_Idx > best_plan;
  std::vector< aptk::State > best_trace;
  float       best_cost = infty;
  float best_time;
  unsigned best_expanded;
  unsigned best_generated;
  unsigned num_plans_found = 0;
	// while ( engine.find_solution( cost, plan, trace ) ) {
	// 	out << "Plan found with cost: " << cost << std::endl;
	// 	// for ( unsigned k = 0; k < plan.size(); k++ ) {
	// 	// 	out << k+1 << ". ";
	// 	// 	const aptk::Action& a = *(plan_prob.actions()[ plan[k] ]);
	// 	// 	out << a.signature();
	// 	// 	out << std::endl;
	// 	// }
  //   // for ( unsigned k = 0; k < trace.size(); k++){
  //   //   // trace_out << trace[k];
  //   //   for(unsigned i = 0; i < trace[k].fluent_vec().size(); i++) {
  //   //     trace_out << trace[k].problem().fluents()[trace[k].fluent_vec()[i]]->signature();
  //   //     if(i != trace[k].fluent_vec().size()-1){
  //   //       trace_out << ", ";
  //   //     }
  //   //   }
  //   //   trace_out << std::endl;
  //   // }
	// 	float tf = aptk::time_used();
	// 	unsigned expanded_f = engine.expanded();
	// 	unsigned generated_f = engine.generated();
	// 	// out << "Time: " << tf - t0 << std::endl;
	// 	// out << "Generated: " << generated_f - generated_0 << std::endl;
	// 	// out << "Expanded: " << expanded_f - expanded_0 << std::endl;
  //   if (cost < best_cost){
  //     best_plan.swap(plan);
  //     best_trace.swap(trace);
  //     best_cost = cost;
  //     best_time = tf - t0;
  //     best_generated = generated_f - generated_0;
  //     best_expanded = expanded_f - expanded_0;
  //   }
	// 	t0 = tf;
	// 	expanded_0 = expanded_f;
	// 	generated_0 = generated_f;
  //   num_plans_found += 1;
	// 	plan.clear();
  //   trace.clear();
	// }
  engine.find_solution( best_cost, best_plan, best_trace );
  if(best_cost != infty){
    out << num_plans_found << " plan(s) found with best cost: " << best_cost << std::endl;
    for ( unsigned k = 0; k < best_plan.size(); k++ ) {
    	out << k+1 << ". ";
    	const aptk::Action& a = *(plan_prob.actions()[ best_plan[k] ]);
    	out << a.signature();
    	out << std::endl;
    }
    for ( unsigned k = 0; k < best_trace.size(); k++){
      // trace_out << trace[k];
      for(unsigned i = 0; i < best_trace[k].fluent_vec().size(); i++) {
        trace_out << best_trace[k].problem().fluents()[best_trace[k].fluent_vec()[i]]->signature();
        if(i != best_trace[k].fluent_vec().size()-1){
          trace_out << ", ";
        }
      }
      trace_out << std::endl;
    }
    out << "Best Time: " << best_time << std::endl;
    out << "Generated: " << best_generated << std::endl;
    out << "Expanded: " << best_expanded << std::endl;
  } else {
    out << "No plan found." << std::endl;
  }

	float total_time = aptk::time_used() - ref;
	out << "Total time: " << total_time << std::endl;
	out << "Nodes generated during search: " << engine.generated() << std::endl;
	out << "Nodes expanded during search: " << engine.expanded() << std::endl;
	out << "Nodes pruned by bound: " << engine.pruned_by_bound() << std::endl;
	out << "Dead-end nodes: " << engine.dead_ends() << std::endl;
	out << "Nodes in OPEN replaced: " << engine.open_repl() << std::endl;

	out.close();
  trace_out.close();

	return total_time;
}

void process_command_line_options( int ac, char** av, po::variables_map& vars ) {
	po::options_description desc( "Options:" );

	desc.add_options()
		( "help", "Show help message" )
		( "domain", po::value<std::string>(), "Input PDDL domain description" )
		( "problem", po::value<std::string>(), "Input PDDL problem description" )
		( "time", po::value<int>()->default_value(10), "Time to find a solution (in seconds)")
		( "bound", po::value<float>()->default_value(infty), "Bounds search to only search plans which may be less than bound. Defaults to infty")
    ( "output", po::value<std::string>()->default_value("solution.details"), "Where the plan description (including steps) goes. Defaults to solution.details" )
    ( "trace_output", po::value<std::string>()->default_value("solution.trace"), "Where the trace of the plan goes. Defaults to solution.trace" )
	;

	try {
		po::store( po::parse_command_line( ac, av, desc ), vars );
		po::notify( vars );
	}
	catch ( std::exception& e ) {
		std::cerr << "Error: " << e.what() << std::endl;
		std::exit(1);
	}
	catch ( ... ) {
		std::cerr << "Exception of unknown type!" << std::endl;
		std::exit(1);
	}

	if ( vars.count("help") ) {
		std::cout << desc << std::endl;
		std::exit(0);
	}

}

int main( int argc, char** argv ) {

	po::variables_map vm;

	process_command_line_options( argc, argv, vm );

	if ( !vm.count( "domain" ) ) {
		std::cerr << "No PDDL domain was specified!" << std::endl;
		std::exit(1);
	}

	if ( !vm.count( "problem" ) ) {
		std::cerr << "No PDDL problem was specified!" << std::endl;
		std::exit(1);
	}

	STRIPS_Problem	prob;

	aptk::FF_Parser::get_problem_description( vm["domain"].as<std::string>(), vm["problem"].as<std::string>(), prob );

	std::cout << "PDDL problem description loaded: " << std::endl;
	std::cout << "\tDomain: " << prob.domain_name() << std::endl;
	std::cout << "\tProblem: " << prob.problem_name() << std::endl;
	std::cout << "\t#Actions: " << prob.num_actions() << std::endl;
	std::cout << "\t#Fluents: " << prob.num_fluents() << std::endl;

	prob.initialize_successor_generator();


	Fwd_Search_Problem	search_prob( &prob );

  Anytime_BFS_H_Add_Rp_Fwd bfs_engine( search_prob );
  bfs_engine.set_bound(vm["bound"].as<float>());
	float time = vm["time"].as<int>();
  std::string output_file = vm["output"].as<std::string>();
  std::string trace_output_file = vm["trace_output"].as<std::string>();
	do_search( bfs_engine, prob, time - 0.005f, output_file, trace_output_file);

	return 0;
}
