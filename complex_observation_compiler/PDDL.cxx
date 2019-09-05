/*
    Miguel Ramirez, Nir Lipovetzky, Hector Geffner
    C^3: A planner for the sequential, satisficing track of the IPC-6
    Copyright (C) 2008

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
#include "PDDL.hxx"
#include <iostream>
#include <cassert>
#include "utils.hxx"
#include "options.hxx"
#include "libff.h"

namespace PDDL
{

Fluent::Fluent( int code )
	: m_code( code )
{
}

Fluent::~Fluent()
{
}
Operator::Operator()
	: m_xdels( NULL ), m_metric(0.0f)
{
	PDDL::Task& task = PDDL::Task::instance();
	m_precondition = new Fluent_Set( task.fluent_count() );
	m_adds = new Fluent_Set( task.fluent_count() );
	m_dels = new Fluent_Set( task.fluent_count() );
}

Operator::Operator( int code )
	: m_xdels(NULL), m_code( code ), m_metric(0.0f)
{
	PDDL::Task& task = PDDL::Task::instance();
	m_precondition = new Fluent_Set( task.fluent_count() );
	m_adds = new Fluent_Set( task.fluent_count() );
	m_dels = new Fluent_Set( task.fluent_count() );
}

Operator::~Operator()
{
	delete m_precondition;
	delete m_adds;
	delete m_dels;
}

Task::Task()
	: m_string_table( String_Table::instance() ), m_glog( "grounding.stats" )
{
}

Task::~Task()
{
}

Task& Task::instance()
{
	static Task the_instance;
	return the_instance;
}

void Task::setup()
{
	Options& opt = Options::instance();

	float t0 = time_used();
	FF_parse_problem( opt.domain_filename().c_str(), opt.instance_filename().c_str() );
	float tf = time_used();
	m_glog << "Parsing="; report_interval( t0, tf, m_glog );

	t0 = time_used();
	FF_instantiate_problem();
	tf = time_used();
	m_glog << "Instantiation="; report_interval( t0, tf, m_glog );

	t0 = time_used();
	create_fluents();
	tf = time_used();
	m_glog << "Fluent_Copying="; report_interval( t0, tf, m_glog );

	t0 = time_used();
	create_init_and_goal();
	tf = time_used();
	m_glog << "Init_And_Goal_Copying="; report_interval( t0, tf, m_glog );

	t0 = time_used();
	create_operators();
	tf = time_used();
	m_glog << "Operators_Copying="; report_interval( t0, tf, m_glog );

	// Setup costs
	m_op_costs.resize( useful_ops().size() );
	for ( unsigned o = 0; o < useful_ops().size(); o++ )
		m_op_costs[o] = useful_ops()[o]->metric_cost();

	set_domain_name( FF::get_domain_name() );
	set_problem_name( FF::get_problem_name() );
}

void Task::create_fluents()
{
	fluents().push_back( NULL );

	for ( int i = 0; i < gnum_ft_conn; i++ )
	{
		std::string ft_name = FF::get_ft_name(i);
		int str_code = str_tab().get_code( ft_name );
		fluents().push_back( new Fluent( str_code ) );
	}
}

void Task::create_init_and_goal()
{
	FF::get_initial_state( m_initial_state );
	for ( unsigned i = 0; i < m_initial_state.size(); i++ )
		m_initial_state[i]++;
	std::string start_name( "(START)" );
	m_start_id = 0;
	useful_ops().push_back( new Operator( str_tab().get_code( start_name ) ) );
	for ( unsigned i = 0; i < m_initial_state.size(); i++ )
	{
		useful_ops()[0]->adds().set( m_initial_state[i] );
		useful_ops()[0]->add_vec().push_back( m_initial_state[i] );
	}

	FF::get_goal_state( m_goal_state );
	for ( unsigned i = 0; i < m_goal_state.size(); i++ )
		m_goal_state[i]++;
	std::string end_name( "(END)" );
	m_end_id = 1;
	useful_ops().push_back( new Operator( str_tab().get_code( end_name ) ) );
	for ( unsigned i = 0; i < m_goal_state.size(); i++ )
	{
		useful_ops()[1]->preconds().set( m_goal_state[i] );
		useful_ops()[1]->prec_vec().push_back( m_goal_state[i] );
	}
}

void Task::create_operators()
{
	for ( int i = 0; i < gnum_ef_conn; i++ )
	{
		if ( gef_conn[i].removed == TRUE ) continue;
		if ( gef_conn[i].illegal == TRUE ) continue;

		std::string op_name = FF::get_op_name(i);
		useful_ops().push_back( new Operator( str_tab().get_code( op_name ) ) );
		Operator* curr_op = useful_ops().back();

		for ( int j = 0; j < gef_conn[i].num_PC; j++ )
		{
			unsigned p = gef_conn[i].PC[j] + 1;
			curr_op->preconds().set( p );
			curr_op->prec_vec().push_back( p );
		}

		for ( int j = 0; j < gef_conn[i].num_A; j++ )
		{
			unsigned p = gef_conn[i].A[j] + 1;
			curr_op->adds().set( p );
			curr_op->add_vec().push_back( p );
		}

		for ( int j = 0; j < gef_conn[i].num_D; j++ )
		{
			unsigned p = gef_conn[i].D[j] + 1;
			curr_op->dels().set( p );
			curr_op->del_vec().push_back( p );
		}
		if ( gef_conn[i].num_IN == 0 )
			curr_op->set_metric_cost( 1 );
		else if ( gef_conn[i].num_IN >= 1 )
			curr_op->set_metric_cost( gef_conn[i].cost );//IN_c[0] );
	}
}

void Task::print_fluent( Fluent* fi, std::ostream& os )
{
	os << str_tab().get_token( fi->code() );
}

void Task::print_fluents( std::ostream& os )
{
	for ( unsigned i = 1; i < fluents().size(); i++ )
	{
		os << i << " ";
		Fluent* fi = fluents()[i];
		print_fluent( fi, os );
		os << std::endl;
	}
}

void Task::print_initial_state( std::ostream& os )
{
	os << "Initial state:" << std::endl;
	for ( unsigned i = 0;  i < initial_state().size(); i++ )
	{
		print_fluent( fluents()[initial_state()[i]], os );
		os << std::endl;
	}
}

void Task::print_goal_state( std::ostream& os )
{
	os << "Goal state:" << std::endl;
	for ( unsigned i = 0; i < goal_state().size(); i++ )
	{
		print_fluent( fluents()[goal_state()[i]], os );
		os << std::endl;
	}
}

void Task::print_operator_full( Operator* oi, std::ostream& os )
{
	os << str_tab().get_token( oi->code() );
	os << ":" << std::endl;
	os << "\t" << "Preconditions:" << std::endl;
	for ( unsigned i = 0; i < oi->prec_vec().size(); i++ )
	{
		unsigned pi = oi->prec_vec()[i];
		os << "\t\t";
		print_fluent( fluents()[pi], os );
		os << std::endl;
	}
	os << "\t" << "Adds:" << std::endl;
	for ( unsigned i = 0; i < oi->add_vec().size(); i++ )
	{
		unsigned pi = oi->add_vec()[i];
		os << "\t\t";
		print_fluent( fluents()[pi], os );
		os << std::endl;
	}

	os << "\t" << "Deletes:" << std::endl;
	for ( unsigned i = 0; i < oi->del_vec().size(); i++ )
	{
		unsigned pi = oi->del_vec()[i];
		os << "\t\t";
		print_fluent( fluents()[pi], os );
		os << std::endl;
	}

}

void Task::print_operator( Operator* oi, std::ostream& os )
{
	os << str_tab().get_token( oi->code() );
}

void Task::print_operators( std::ostream& os )
{
	for ( unsigned i = 0; i < useful_ops().size(); i++ )
	{
		Operator* oi = useful_ops()[i];
		os << "Name:" << std::endl;
		print_operator_full( oi, os );
		os << "Cost: " << oi->metric_cost() << std::endl;
	}
}

}
