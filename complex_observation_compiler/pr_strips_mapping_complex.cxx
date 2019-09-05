#include "pr_strips_mapping_complex.hxx"
#include <sstream>
#include "PDDL.hxx"
#include "options.hxx"

PR_STRIPS_Mapping_Complex::PR_STRIPS_Mapping_Complex( Complex_Observation_Set& set )
	: m_obs_set( set ), m_negated( false ), m_convert_to_integer( false ),
	m_factor( 1.0 )
{

}

PR_STRIPS_Mapping_Complex::PR_STRIPS_Mapping_Complex( Complex_Observation_Set& set, bool neg )
	: m_obs_set( set ), m_negated( neg ), m_convert_to_integer( false ),
	m_factor( 1.0 )
{
}

PR_STRIPS_Mapping_Complex::PR_STRIPS_Mapping_Complex( Complex_Observation_Set& set, bool neg, bool to_int, float factor )
	: m_obs_set( set ), m_negated( neg ), m_convert_to_integer( to_int ),
	m_factor( factor )
{
}

PR_STRIPS_Mapping_Complex::~PR_STRIPS_Mapping_Complex()
{

}

void PR_STRIPS_Mapping_Complex::write()
{
	make_predicate_strings();
	make_action_strings();
	// make_explained_strings();
	write_domain_definition();
	write_problem_definition();

}

// void PR_STRIPS_Mapping_Complex::make_explained_strings()
// {
// 	for ( unsigned obs = 0; obs < m_obs_set.size(); obs++ )
// 	{
// 		std::stringstream buffer;
// 		buffer << "EXPLAINED_" << action_str()[m_obs_set[obs]->get_op_index()];
// 		if ( m_obs_set[obs]->ordinal() != 0 )
// 		{
// 			buffer << "_" << m_obs_set[obs]->ordinal();
// 		}
// 		exp_str().push_back( buffer.str() );
// 		std::cout << "Predicate: " << std::endl;
// 		std::cout << "\t" << buffer.str() << std::endl;
// 		std::cout << "created" << std::endl;
// 	}
// 	std::stringstream buffer;
// 	buffer << "EXPLAINED_FULL_OBS_SEQUENCE";
// 	exp_str().push_back( buffer.str() );
// 	std::cout << "Predicate: " << std::endl;
// 	std::cout << "\t" << buffer.str() << std::endl;
// 	std::cout << "created" << std::endl;
//
// 	for ( unsigned obs = 0; obs < m_obs_set.size(); obs++ )
// 	{
// 		std::stringstream buffer_not;
// 		buffer_not << "NOT_EXPLAINED_" << action_str()[m_obs_set[obs]->get_op_index()];
// 		if ( m_obs_set[obs]->ordinal() != 0 )
// 		{
// 			buffer_not << "_" << m_obs_set[obs]->ordinal();
// 		}
// 		not_exp_str().push_back( buffer_not.str() );
// 		std::cout << "Predicate: " << std::endl;
// 		std::cout << "\t" << buffer_not.str() << std::endl;
// 		std::cout << "created" << std::endl;
// 	}
//
// 	std::stringstream buffer_not;
// 	buffer_not << "NOT_EXPLAINED_FULL_OBS_SEQUENCE";
// 	not_exp_str().push_back( buffer_not.str() );
// 	std::cout << "Predicate: " << std::endl;
// 	std::cout << "\t" << buffer_not.str() << std::endl;
// 	std::cout << "created" << std::endl;
//
//
// }

void PR_STRIPS_Mapping_Complex::write_predicates_definitions()
{

	domain_stream() << "\t(:predicates" << std::endl;
	PDDL::Task& task = PDDL::Task::instance();

	for ( unsigned f = 1; f < task.fluents().size(); f++ )
		domain_stream() << "\t\t( " << pred_str()[f] << " )" << std::endl;

	// EXPLAINED/NOT_EXPLAINED predicates
  for (std::set<std::string>::iterator obs_fluent = m_obs_set.observation_fluents().begin(); obs_fluent != m_obs_set.observation_fluents().end(); ++obs_fluent){
		domain_stream() << "\t\t( " << *(obs_fluent) << " )" << std::endl;
    // domain_stream() << "\t\t( " << "NOT_" << *(obs_fluent) << " )" << std::endl;
  }

	domain_stream() << "\t) " << std::endl;
}

void PR_STRIPS_Mapping_Complex::write_init_definition()
{
	PDDL::Task& task = PDDL::Task::instance();

	problem_stream() << "\t(:init" << std::endl;

	PDDL::Operator* start_op = task.useful_ops()[task.start()];

	problem_stream() << "\t\t(= (total-cost) 0)" << std::endl;

	for ( unsigned k = 0; k < start_op->add_vec().size(); k++ )
		problem_stream() << "\t\t( " << pred_str()[ start_op->add_vec()[k] ] << " )" << std::endl;

	// for ( unsigned obs = 0; obs < m_obs_set.observation_fluents().size(); obs++ )
	// 	problem_stream() << "\t\t( " << "NOT_" << *(m_obs_set.observation_fluents()[obs]) << " )" << std::endl;

	problem_stream() << "\t)" << std::endl;

}

void PR_STRIPS_Mapping_Complex::write_goal_definition()
{
	PDDL::Task& task = PDDL::Task::instance();

	problem_stream() << "\t(:goal" << std::endl;
	problem_stream() << "\t\t(and " << std::endl;

	// Write input file goals (they're assumed to be the hypothesis)
	PDDL::Operator* end_op = task.useful_ops()[task.end()];
	for ( unsigned k = 0; k < end_op->prec_vec().size(); k++ )
		problem_stream() << "\t\t( " << pred_str()[ end_op->prec_vec()[k] ] << " )" << std::endl;

// Complex observations won't have just the last one. Need all explanation predicates
	// if ( m_negated )
	// 	problem_stream() << "\t\t( " << not_exp_str().back() << " )" << std::endl;
	// else
	// 	problem_stream() << "\t\t( " << exp_str().back() << " )" << std::endl;

  for (std::set<std::string>::iterator obs_fluent = m_obs_set.observation_fluents().begin(); obs_fluent != m_obs_set.observation_fluents().end(); ++obs_fluent){
    problem_stream() << "\t\t( " << *obs_fluent << " )" << std::endl;
  }

	problem_stream() << "\t\t)" << std::endl; // (and
	problem_stream() << "\t)" << std::endl; // (:goal

}

void PR_STRIPS_Mapping_Complex::write_actions_definitions()
{
	PDDL::Task& task = PDDL::Task::instance();
	// Options& opt = Options::instance();

	// std::vector<bool> is_obs;
	// is_obs.resize( task.useful_ops().size() );
	// for ( unsigned k = 0; k < is_obs.size(); k++ )
	// 	is_obs[k] = false;

	for ( unsigned k = 0; k < m_obs_set.observations().size(); k++ )
	{
		write_explain_obs_op( m_obs_set.observations()[k]);
		// write_non_explaining_obs_op( m_obs_set.observations()[k]);
		// is_obs[m_obs_set.observations()[k]->get_op_index()] = true;
	}

	for ( unsigned op = 2; op < task.useful_ops().size(); op++ )
		// if (  !is_obs[op] )
			write_regular_op( op );

}

void PR_STRIPS_Mapping_Complex::write_explain_obs_op( Action_Execution_Complex_Observation* obs_ptr )
{

  if( obs_ptr->is_action_observation()){

  	PDDL::Task& task = PDDL::Task::instance();

    unsigned op_ID = obs_ptr->get_op_index();

  	PDDL::Operator* op_ptr = task.useful_ops()[op_ID];

  	std::stringstream op_name_buffer;
  	op_name_buffer << "EXPLAIN_OBS_";
  	op_name_buffer << action_str()[op_ID];

    // Add an ordinal if duplicate observations possible
  	if ( obs_ptr->ordinal() != 0 )
  		op_name_buffer << "_" << obs_ptr->ordinal();

  	domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;
  	domain_stream() << "\t\t:parameters ()" << std::endl;

  	domain_stream() << "\t\t:precondition" << std::endl;
  	domain_stream() << "\t\t(and" << std::endl;


    domain_stream() << "\t\t\t( not ( " << obs_ptr->observation_ID() << " ) )" <<std::endl;

    // The normal preconditions of this action
  	for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
  	{
  		domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;
  	}

    // This observation's ordering fluents
    for (std::set<std::string>::iterator order_fluent = obs_ptr->ordering_prec_fluents().begin(); order_fluent != obs_ptr->ordering_prec_fluents().end(); ++order_fluent) {
      domain_stream() << "\t\t\t( " << *order_fluent << " )" <<std::endl;
    }

  	domain_stream() << "\t\t)" << std::endl;

  	// Write effects
  	domain_stream() << "\t\t:effect" << std::endl;
  	domain_stream() << "\t\t(and" << std::endl;

  	// Cost of the action, possibly multiplied by a factor
  	domain_stream() << "\t\t\t(increase (total-cost) ";
  	if ( !m_convert_to_integer ){
  		domain_stream() << task.op_cost(op_ID);
  	} else {
  		float new_cost = task.op_cost(op_ID)*m_factor;
  		domain_stream() << (int)new_cost;
  	}
  	domain_stream() <<  ")" << std::endl;

    // The normal effects of the action
  	for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
  		domain_stream() << "\t\t\t( " << pred_str()[op_ptr->add_vec()[k]] << " )" << std::endl;
    for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
      domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;

    // This action's observation fluent
  	domain_stream() << "\t\t\t( " << obs_ptr->observation_ID() << " )" << std::endl;

  	domain_stream() << "\t\t)" << std::endl;
  	domain_stream() << "\t)" << std::endl;
  }

  else {

  	std::stringstream op_name_buffer;
  	op_name_buffer << "EXPLAIN_";
  	op_name_buffer << obs_ptr->observation_ID();
    if (obs_ptr->option_group_idx() != 0) {
      op_name_buffer << "_" << obs_ptr->option_group_idx();
    }

  	domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;
  	domain_stream() << "\t\t:parameters ()" << std::endl;

  	domain_stream() << "\t\t:precondition" << std::endl;
  	domain_stream() << "\t\t(and" << std::endl;

    domain_stream() << "\t\t\t( not ( " << obs_ptr->observation_ID() << " ) )" <<std::endl;

    // The observed fluents
    for ( std::set<unsigned>::iterator fl_idx = obs_ptr->observed_fluents().begin(); fl_idx != obs_ptr->observed_fluents().end(); ++fl_idx){
      domain_stream() << "\t\t\t( " << pred_str()[*fl_idx] << " )" << std::endl;
    }

    // This observation's ordering fluents
    for (std::set<std::string>::iterator order_fluent = obs_ptr->ordering_prec_fluents().begin(); order_fluent != obs_ptr->ordering_prec_fluents().end(); ++order_fluent) {
      domain_stream() << "\t\t\t( " << *order_fluent << " )" <<std::endl;
    }

  	domain_stream() << "\t\t)" << std::endl;

  	// Write effects
  	domain_stream() << "\t\t:effect" << std::endl;
  	domain_stream() << "\t\t(and" << std::endl;

  	// Zero cost action
  	domain_stream() << "\t\t\t(increase (total-cost) 0 )\n";

    // No effect but ordering effects

    // This action's observation fluent
  	domain_stream() << "\t\t\t( " << obs_ptr->observation_ID() << " )" << std::endl;

  	domain_stream() << "\t\t)" << std::endl;
  	domain_stream() << "\t)" << std::endl;
  }

}

// void PR_STRIPS_Mapping_Complex::write_non_explaining_obs_op( unsigned op, unsigned i )
// {
// 	PDDL::Task& task = PDDL::Task::instance();
//
// 	PDDL::Operator* op_ptr = task.useful_ops()[op];
// 	/*
// 	if ( i == 0 )
// 	{
// 		std::stringstream op_name_buffer;
// 		op_name_buffer << action_str()[op];
// 		domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;
//
// 		domain_stream() << "\t\t:parameters ()" << std::endl;
// 		// Write preconditions
// 		domain_stream() << "\t\t:precondition" << std::endl;
// 		domain_stream() << "\t\t(and" << std::endl;
//
// 		for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
// 			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;
// 		domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;
//
// 		domain_stream() << "\t\t)" << std::endl;
//
// 		// Write effects
// 		domain_stream() << "\t\t:effect" << std::endl;
// 		domain_stream() << "\t\t(and" << std::endl;
// 		// write cost
// 		domain_stream() << "\t\t\t(increase (total-cost) " << task.op_cost(op) <<  ")" << std::endl;
//
// 		for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
// 			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->add_vec()[k]] << " )" << std::endl;
//
// 		//if ( i == m_obs_set.size() - 1 )
// 		//	domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;
//
// 		for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
// 			domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;
//
// 		domain_stream() << "\t\t)" << std::endl;
// 		domain_stream() << "\t)" << std::endl;
// 	}
// 	*/
// 	for ( unsigned j = 0; j < i; j++ )
// 	{
// 		std::stringstream op_name_buffer;
// 		op_name_buffer << action_str()[op];
// 		domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;
//
// 		domain_stream() << "\t\t:parameters ()" << std::endl;
// 		// Write preconditions
// 		domain_stream() << "\t\t:precondition" << std::endl;
// 		domain_stream() << "\t\t(and" << std::endl;
//
// 		for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
// 			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;
// 		domain_stream() << "\t\t\t( " << not_exp_str()[j] << " )" << std::endl;
// 		domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;
//
// 		domain_stream() << "\t\t)" << std::endl;
//
// 		// Write effects
// 		domain_stream() << "\t\t:effect" << std::endl;
// 		domain_stream() << "\t\t(and" << std::endl;
// 		// write cost
// 		domain_stream() << "\t\t\t(increase (total-cost) ";
// 		if ( !m_convert_to_integer )
// 			domain_stream() << task.op_cost(op);
// 		else
// 		{
// 			float new_cost = task.op_cost(op)* m_factor;
// 			domain_stream() << (int)new_cost;
// 		}
// 		domain_stream() <<  ")" << std::endl;
//
// 		for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
// 			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->add_vec()[k]] << " )" << std::endl;
//
// 		//if ( i == m_obs_set.size() - 1 )
// 		//	domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;
//
// 		for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
// 			domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;
//
// 		domain_stream() << "\t\t)" << std::endl;
// 		domain_stream() << "\t)" << std::endl;
// 	}
// }

void PR_STRIPS_Mapping_Complex::write_regular_op( unsigned op )
{
	PDDL::Task& task = PDDL::Task::instance();

	PDDL::Operator* op_ptr = task.useful_ops()[op];
	std::stringstream op_name_buffer;
	op_name_buffer << action_str()[op];
	domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;

	domain_stream() << "\t\t:parameters ()" << std::endl;
	// Write preconditions
	domain_stream() << "\t\t:precondition" << std::endl;
	domain_stream() << "\t\t(and" << std::endl;

	for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
		domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;

	domain_stream() << "\t\t)" << std::endl;

	// Write effects
	domain_stream() << "\t\t:effect" << std::endl;
	domain_stream() << "\t\t(and" << std::endl;
	// write cost
	domain_stream() << "\t\t\t(increase (total-cost) ";
	if ( !m_convert_to_integer )
		domain_stream() << task.op_cost(op);
	else
	{
		float new_cost = task.op_cost(op)*m_factor;
		domain_stream() << (int)new_cost;
	}
	domain_stream() <<  ")" << std::endl;

	for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
		domain_stream() << "\t\t\t( " << pred_str()[op_ptr->add_vec()[k]] << " )" << std::endl;

	for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
		domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;

	domain_stream() << "\t\t)" << std::endl;
	domain_stream() << "\t)" << std::endl;

}
