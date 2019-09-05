#include "pr_strips_mapping.hxx"
#include <sstream>
#include "PDDL.hxx"
#include "options.hxx"

PR_STRIPS_Mapping::PR_STRIPS_Mapping( Observation_Stream& stream )
	: m_obs_stream( stream ), m_negated( false ), m_convert_to_integer( false ),
	m_factor( 1.0 )
{

}

PR_STRIPS_Mapping::PR_STRIPS_Mapping( Observation_Stream& stream, bool neg )
	: m_obs_stream( stream ), m_negated( neg ), m_convert_to_integer( false ),
	m_factor( 1.0 )
{
}

PR_STRIPS_Mapping::PR_STRIPS_Mapping( Observation_Stream& stream, bool neg, bool to_int, float factor )
	: m_obs_stream( stream ), m_negated( neg ), m_convert_to_integer( to_int ),
	m_factor( factor )
{
}

PR_STRIPS_Mapping::~PR_STRIPS_Mapping()
{

}

void PR_STRIPS_Mapping::write()
{
  // strips_writer base class grounds predicates like so: (CLEAR P) -> CLEAR P -> CLEAR_P
	make_predicate_strings();
  // strips_writer base class grounds actions like above
	make_action_strings();
  // Make the predicates for explaining / not explaining observations. (Not added to domain yet)
	make_explained_strings();
  // strips_writer base class takes care of -- but calls overridden write_predicates_definition and
	write_domain_definition();
	write_problem_definition();

}

void PR_STRIPS_Mapping::make_explained_strings()
{
	for ( unsigned obs = 0; obs < m_obs_stream.size(); obs++ )
	{
		std::stringstream buffer;
		buffer << "EXPLAINED_" << action_str()[m_obs_stream[obs]->get_op_index()];
    // Duplicate observations get indexed
		if ( m_obs_stream[obs]->ordinal() != 0 )
		{
			buffer << "_" << m_obs_stream[obs]->ordinal();
		}
		exp_str().push_back( buffer.str() );
		std::cout << "Predicate: " << std::endl;
		std::cout << "\t" << buffer.str() << std::endl;
		std::cout << "created" << std::endl;
	}
	std::stringstream buffer;
	buffer << "EXPLAINED_FULL_OBS_SEQUENCE";
	exp_str().push_back( buffer.str() );
	std::cout << "Predicate: " << std::endl;
	std::cout << "\t" << buffer.str() << std::endl;
	std::cout << "created" << std::endl;

	for ( unsigned obs = 0; obs < m_obs_stream.size(); obs++ )
	{
		std::stringstream buffer_not;
		buffer_not << "NOT_EXPLAINED_" << action_str()[m_obs_stream[obs]->get_op_index()];
		if ( m_obs_stream[obs]->ordinal() != 0 )
		{
			buffer_not << "_" << m_obs_stream[obs]->ordinal();
		}
		not_exp_str().push_back( buffer_not.str() );
		std::cout << "Predicate: " << std::endl;
		std::cout << "\t" << buffer_not.str() << std::endl;
		std::cout << "created" << std::endl;
	}

	std::stringstream buffer_not;
	buffer_not << "NOT_EXPLAINED_FULL_OBS_SEQUENCE";
	not_exp_str().push_back( buffer_not.str() );
	std::cout << "Predicate: " << std::endl;
	std::cout << "\t" << buffer_not.str() << std::endl;
	std::cout << "created" << std::endl;


}

void PR_STRIPS_Mapping::write_predicates_definitions()
{

	domain_stream() << "\t(:predicates" << std::endl;
	PDDL::Task& task = PDDL::Task::instance();

	for ( unsigned f = 1; f < task.fluents().size(); f++ )
		domain_stream() << "\t\t( " << pred_str()[f] << " )" << std::endl;

	// EXPLAINED predicates
	for ( unsigned obs = 0; obs < m_obs_stream.size(); obs++ )
		domain_stream() << "\t\t( " << exp_str()[obs] << " )" << std::endl;

	for ( unsigned obs = 0; obs < m_obs_stream.size(); obs++ )
		domain_stream() << "\t\t( " << not_exp_str()[obs] << " )" << std::endl;

	domain_stream() << "\t\t( " << exp_str().back() << " )" << std::endl;
	domain_stream() << "\t\t( " << not_exp_str().back() << " )" << std::endl;

	domain_stream() << "\t) " << std::endl;
}

void PR_STRIPS_Mapping::write_init_definition()
{
	PDDL::Task& task = PDDL::Task::instance();

	problem_stream() << "\t(:init" << std::endl;

	PDDL::Operator* start_op = task.useful_ops()[task.start()];

	problem_stream() << "\t\t(= (total-cost) 0)" << std::endl;

	for ( unsigned k = 0; k < start_op->add_vec().size(); k++ )
		problem_stream() << "\t\t( " << pred_str()[ start_op->add_vec()[k] ] << " )" << std::endl;

	for ( unsigned obs = 0; obs < m_obs_stream.size(); obs++ )
		problem_stream() << "\t\t( " << not_exp_str()[obs] << " )" << std::endl;
	problem_stream() << "\t\t( " << not_exp_str().back() << " )" << std::endl;

	problem_stream() << "\t)" << std::endl;

}

void PR_STRIPS_Mapping::write_goal_definition()
{
	PDDL::Task& task = PDDL::Task::instance();

	problem_stream() << "\t(:goal" << std::endl;
	problem_stream() << "\t\t(and " << std::endl;

	// Write input file goals (they're assumed to be the hypothesis)
	PDDL::Operator* end_op = task.useful_ops()[task.end()];
	for ( unsigned k = 0; k < end_op->prec_vec().size(); k++ )
		problem_stream() << "\t\t( " << pred_str()[ end_op->prec_vec()[k] ] << " )" << std::endl;

	if ( m_negated )
		problem_stream() << "\t\t( " << not_exp_str().back() << " )" << std::endl;
	else
		problem_stream() << "\t\t( " << exp_str().back() << " )" << std::endl;

	problem_stream() << "\t\t)" << std::endl; // (and
	problem_stream() << "\t)" << std::endl; // (:goal

}

void PR_STRIPS_Mapping::write_actions_definitions()
{
	PDDL::Task& task = PDDL::Task::instance();
	Options& opt = Options::instance();

	std::vector<bool> is_obs;
	is_obs.resize( task.useful_ops().size() );
	for ( unsigned k = 0; k < is_obs.size(); k++ )
		is_obs[k] = false;

	for ( unsigned k = 0; k < obs_stream().size(); k++ )
	{
		write_explain_obs_op( obs_stream()[k]->get_op_index(), k );
		write_non_explaining_obs_op( obs_stream()[k]->get_op_index(), k );
		is_obs[obs_stream()[k]->get_op_index()] = true;
	}

	for ( unsigned op = 2; op < task.useful_ops().size(); op++ )
		if (  !is_obs[op] )
			write_regular_op( op );

}

void PR_STRIPS_Mapping::write_explain_obs_op( unsigned op, unsigned i )
{
	PDDL::Task& task = PDDL::Task::instance();

	PDDL::Operator* op_ptr = task.useful_ops()[op];
	std::stringstream op_name_buffer;
	op_name_buffer << "EXPLAIN_OBS_";
	op_name_buffer << action_str()[op];
	if ( m_obs_stream[i]->ordinal() != 0 )
		op_name_buffer << "_" << m_obs_stream[i]->ordinal();
	domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;

	domain_stream() << "\t\t:parameters ()" << std::endl;
	// Write preconditions
	domain_stream() << "\t\t:precondition" << std::endl;
	domain_stream() << "\t\t(and" << std::endl;

	for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
	{
		domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;
	}

	//for ( unsigned k = 0; k < i; k++ )
  // If not the first observation (with no precondition)
	if ( i > 0 )
		domain_stream() << "\t\t\t( " << exp_str()[i-1] << " )" << std::endl;

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

	domain_stream() << "\t\t\t ( " << exp_str()[i] << " )" << std::endl;
	if ( i == m_obs_stream.size()-1 )
		domain_stream() << "\t\t\t ( " << exp_str().back() << " )" << std::endl;

	for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
		domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;

	domain_stream() << "\t\t\t (not ( " << not_exp_str()[i] << " ))" << std::endl;
	if ( i == m_obs_stream.size()-1 )
		domain_stream() << "\t\t\t (not ( " << not_exp_str().back() << " ))" << std::endl;

	domain_stream() << "\t\t)" << std::endl;
	domain_stream() << "\t)" << std::endl;

}

void PR_STRIPS_Mapping::write_non_explaining_obs_op( unsigned op, unsigned i )
{
	PDDL::Task& task = PDDL::Task::instance();

	PDDL::Operator* op_ptr = task.useful_ops()[op];
	/*
	if ( i == 0 )
	{
		std::stringstream op_name_buffer;
		op_name_buffer << action_str()[op];
		domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;

		domain_stream() << "\t\t:parameters ()" << std::endl;
		// Write preconditions
		domain_stream() << "\t\t:precondition" << std::endl;
		domain_stream() << "\t\t(and" << std::endl;

		for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;
		domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;

		domain_stream() << "\t\t)" << std::endl;

		// Write effects
		domain_stream() << "\t\t:effect" << std::endl;
		domain_stream() << "\t\t(and" << std::endl;
		// write cost
		domain_stream() << "\t\t\t(increase (total-cost) " << task.op_cost(op) <<  ")" << std::endl;

		for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->add_vec()[k]] << " )" << std::endl;

		//if ( i == m_obs_stream.size() - 1 )
		//	domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;

		for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
			domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;

		domain_stream() << "\t\t)" << std::endl;
		domain_stream() << "\t)" << std::endl;
	}
	*/
	for ( unsigned j = 0; j < i; j++ )
	{
		std::stringstream op_name_buffer;
		op_name_buffer << action_str()[op];
		domain_stream() << "\t(:action " << op_name_buffer.str() << std::endl;

		domain_stream() << "\t\t:parameters ()" << std::endl;
		// Write preconditions
		domain_stream() << "\t\t:precondition" << std::endl;
		domain_stream() << "\t\t(and" << std::endl;

		for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->prec_vec()[k]] << " )" << std::endl;
		domain_stream() << "\t\t\t( " << not_exp_str()[j] << " )" << std::endl;
		domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;

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
			float new_cost = task.op_cost(op)* m_factor;
			domain_stream() << (int)new_cost;
		}
		domain_stream() <<  ")" << std::endl;

		for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
			domain_stream() << "\t\t\t( " << pred_str()[op_ptr->add_vec()[k]] << " )" << std::endl;

		//if ( i == m_obs_stream.size() - 1 )
		//	domain_stream() << "\t\t\t( " << not_exp_str().back() << " )" << std::endl;

		for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
			domain_stream() << "\t\t\t(not ( " << pred_str()[op_ptr->del_vec()[k]] << " ))" << std::endl;

		domain_stream() << "\t\t)" << std::endl;
		domain_stream() << "\t)" << std::endl;
	}
}

void PR_STRIPS_Mapping::write_regular_op( unsigned op )
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
