#include "strips_writer.hxx"
#include "PDDL.hxx"
#include "string_ops.hxx"
#include <sstream>

STRIPS_Writer::STRIPS_Writer()
	: m_base_path("")
{
}

STRIPS_Writer::~STRIPS_Writer()
{
}

void STRIPS_Writer::make_predicate_strings()
{
	PDDL::Task& task = PDDL::Task::instance();
	m_pred_names.push_back( std::string("") );
	for ( unsigned f = 1; f < task.fluents().size(); f++ )
	{
		PDDL::Fluent* ft = task.fluents()[f];
		std::cout << task.str_tab().get_token( ft->code() ) << " -> ";
		std::string clean_ft_name = strip(task.str_tab().get_token( ft->code() ));
		std::cout << clean_ft_name << " -> ";
		m_pred_names.push_back( replace( clean_ft_name, ' ', '_' ) );
		std::cout << m_pred_names.back() << std::endl;
	}	
}

void STRIPS_Writer::make_action_strings()
{
	PDDL::Task& task = PDDL::Task::instance();
	m_op_names.push_back( std::string("") );
	m_op_names.push_back( std::string("") );

	for ( unsigned op = 2 ; op < task.useful_ops().size(); op++ )
	{
		PDDL::Operator* oi = task.useful_ops()[op];
		std::string clean_op_name = strip( task.str_tab().get_token( oi->code() ) );
		m_op_names.push_back( replace( clean_op_name, ' ', '_' ) );
	}	
}

void STRIPS_Writer::write()
{
	make_predicate_strings();
	make_action_strings();
	write_domain_definition();
	write_problem_definition();
}


void STRIPS_Writer::write_domain_definition()
{
	PDDL::Task& task = PDDL::Task::instance();
	m_domain_outfile_name = base_path() + "pr-domain.pddl";
	m_domain_stream.open( m_domain_outfile_name.c_str() );

	std::cout << "Writing resulting STRIPS domain into " << m_domain_outfile_name << std::endl;

	std::stringstream buffer;
	buffer << "grounded-" << task.domain_name();
	
	m_domain_stream << "(define" << std::endl;

	m_domain_stream << "\t(domain " << buffer.str() << ")" << std::endl;

	write_requirements();
	write_predicates_definitions();
	write_functions();
	write_actions_definitions();
	
	m_domain_stream << std::endl << ")" << std::endl;

	m_domain_stream.close();
}

void STRIPS_Writer::write_requirements()
{
	m_domain_stream << "\t(:requirements :strips :action-costs)" << std::endl;
}

void STRIPS_Writer::write_predicates_definitions()
{
	m_domain_stream << "\t(:predicates" << std::endl;
	PDDL::Task& task = PDDL::Task::instance();

	for ( unsigned f = 1; f < task.fluents().size(); f++ )
		m_domain_stream << "\t\t( " << m_pred_names[f] << " )" << std::endl;

	m_domain_stream << "\t) " << std::endl;
}

void STRIPS_Writer::write_actions_definitions()
{
	PDDL::Task& task = PDDL::Task::instance();

	for ( unsigned op = 2; op < task.useful_ops().size(); op++ )
	{
		PDDL::Operator* op_ptr = task.useful_ops()[op]; 
		m_domain_stream << "\t(:action " << m_op_names[op] << std::endl;
		m_domain_stream << "\t\t:parameters ()" << std::endl;
		// Write preconditions
		m_domain_stream << "\t\t:precondition" << std::endl;
		m_domain_stream << "\t\t(and" << std::endl;
		for ( unsigned k = 0; k < op_ptr->prec_vec().size(); k++ )
			m_domain_stream << "\t\t\t( " << m_pred_names[op_ptr->prec_vec()[k]] << " )" << std::endl;
		m_domain_stream << "\t\t)" << std::endl;
		
		// Write effects
		m_domain_stream << "\t\t:effect" << std::endl;
		m_domain_stream << "\t\t(and" << std::endl;
		// write cost		
		m_domain_stream << "\t\t\t(increase (total-cost) 1)" << std::endl;
		for ( unsigned k = 0; k < op_ptr->add_vec().size(); k++ )
			m_domain_stream << "\t\t\t( " << m_pred_names[op_ptr->add_vec()[k]] << " )" << std::endl;
		for ( unsigned k = 0; k < op_ptr->del_vec().size(); k++ )
			m_domain_stream << "\t\t\t(not ( " << m_pred_names[op_ptr->del_vec()[k]] << " ))" << std::endl;		

		m_domain_stream << "\t\t)" << std::endl;
		m_domain_stream << "\t)" << std::endl;
	}
}

void STRIPS_Writer::write_functions()
{
	m_domain_stream << "\t(:functions (total-cost))" << std::endl;
}

void STRIPS_Writer::write_problem_definition()
{
	PDDL::Task& task = PDDL::Task::instance();

	m_problem_outfile_name = base_path() + "pr-problem.pddl";

	m_problem_stream.open( m_problem_outfile_name.c_str() );

	std::cout << "Writing resulting STRIPS problem into " << m_problem_outfile_name << std::endl;
	
	std::stringstream buffer;
	buffer << "grounded-" << task.problem_name();

	m_problem_stream << "(define" << std::endl;

	m_problem_stream << "\t(problem " << buffer.str() << ")" << std::endl;

	std::stringstream buffer2;
	buffer2 << "grounded-" << task.domain_name();

	m_problem_stream << "\t(:domain " << buffer2.str() << ")" << std::endl;

	write_init_definition();
	write_goal_definition();
	write_metric_definition();

	m_problem_stream << std::endl << ")" << std::endl;

	m_problem_stream.close();
}

void STRIPS_Writer::write_init_definition()
{
	PDDL::Task& task = PDDL::Task::instance();
	
	m_problem_stream << "\t(:init" << std::endl;

	PDDL::Operator* start_op = task.useful_ops()[task.start()];

	m_problem_stream << "\t\t(= (total-cost) 0)" << std::endl;	

	for ( unsigned k = 0; k < start_op->add_vec().size(); k++ )
		m_problem_stream << "\t\t( " << m_pred_names[ start_op->add_vec()[k] ] << " )" << std::endl;

	m_problem_stream << "\t)" << std::endl;
}

void STRIPS_Writer::write_goal_definition()
{
	PDDL::Task& task = PDDL::Task::instance();

	m_problem_stream << "\t(:goal" << std::endl;
	m_problem_stream << "\t\t(and " << std::endl;
	PDDL::Operator* end_op = task.useful_ops()[task.end()];

	for ( unsigned k = 0; k < end_op->prec_vec().size(); k++ )
		m_problem_stream << "\t\t\t( " << m_pred_names[ end_op->prec_vec()[k] ] << " )" << std::endl;

	m_problem_stream << "\t\t)" << std::endl;
	m_problem_stream << "\t)" << std::endl;
}

void STRIPS_Writer::write_metric_definition()
{
	m_problem_stream << "\t(:metric minimize (total-cost))" << std::endl;
}

void STRIPS_Writer::make_domain_outfile_name()
{
	PDDL::Task& task = PDDL::Task::instance();

	std::stringstream buffer;
	buffer << base_path();
	buffer << "domain-";
	buffer << task.domain_name();
	buffer << ".pddl";
	m_domain_outfile_name = buffer.str();
}

void STRIPS_Writer::make_problem_outfile_name()
{
	PDDL::Task& task = PDDL::Task::instance();

	std::stringstream buffer;
	buffer << "instance-";
	buffer << task.problem_name();
	buffer << ".pddl";
	m_problem_outfile_name = buffer.str();
}
