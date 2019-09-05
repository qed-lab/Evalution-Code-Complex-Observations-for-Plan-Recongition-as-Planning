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
#ifndef __PDDL__
#define __PDDL__

#include "pddl_basic_types.hxx"
#include "pddl_string_table.hxx"
#include "pddl_fluent_set.hxx"
#include "nff_logic.hxx"
#include <iostream>
#include <fstream>
#include <set>
#include <cassert>

namespace NFF
{

class H2;

}

namespace PDDL
{

class Fluent // A grounded predicate
{
public:

	explicit Fluent();
	Fluent( int code );
	~Fluent();

	int			code() { return m_code; }

protected:
	int			m_code;
};

class Operator
{
public:

	explicit Operator();
	Operator( int code );

	~Operator();

	Fluent_Set&		preconds() 	{ return *m_precondition; }
	Fluent_Set&		adds() 		{ return *m_adds; }
	Fluent_Set&		dels() 		{ return *m_dels; }
	Fluent_Set&		xdels()		{ return *m_xdels; }
	std::vector<unsigned>&	prec_vec()	{ return m_prec_vec; }
	std::vector<unsigned>&	add_vec()	{ return m_add_vec; }
	std::vector<unsigned>&	del_vec()	{ return m_del_vec; }
	
	int			code()		{ return m_code; }
	float			metric_cost() { return m_metric; }
	void			set_metric_cost( float cost ) { m_metric = cost; }
protected:
	
	std::vector<unsigned>	m_prec_vec;
	std::vector<unsigned>	m_add_vec;
	std::vector<unsigned>	m_del_vec;
	Fluent_Set*		m_precondition;
	Fluent_Set*		m_adds;
	Fluent_Set*		m_dels;
	Fluent_Set*		m_xdels;
	int			m_code;
	float			m_metric;
};


class Task
{
	
private:
	Task();
public:
	~Task();
	static Task& instance();

	void setup();

	int 			fluent_count() { return (int)m_fluent_table.size(); }
	std::vector<Fluent*>&	fluents() { return m_fluent_table; }
	std::vector<Operator*>& useful_ops() { return m_useful_operator_table; }

	std::vector<unsigned>&	initial_state() { return m_initial_state; }
	std::vector<unsigned>& 	goal_state() { return m_goal_state; }

	unsigned		start() { return m_start_id; }
	unsigned		end() { return m_end_id; }

	bool			useful( unsigned op ) { return m_is_useful[op]; }

	void			print_fluents( std::ostream& os );
	void			print_fluent( Fluent* f, std::ostream& os );
	void			print_fluent( unsigned f, std::ostream& os )
	{
		assert( f > 0 && f < fluents().size() );
		print_fluent( fluents()[f], os );
	}

	void			print_operator( Operator* o, std::ostream& os );
	void			print_operator_full( Operator* o, std::ostream& os );
	void			print_operator( unsigned o, std::ostream& os )
	{
		assert( o < useful_ops().size() );
		print_operator( useful_ops()[o], os );
	}
	void			print_operators( std::ostream& os );

	void			print_initial_state( std::ostream& os );
	void			print_goal_state( std::ostream& os );

	String_Table&		str_tab() { return m_string_table; }

	bool			equal_effects( unsigned o1, unsigned o2 )
	{
		if ( o1 == o2 ) return true;
		Operator* o1ptr = useful_ops()[o1];
		Operator* o2ptr = useful_ops()[o2];
		
		if ( o1ptr->add_vec().size() != o2ptr->add_vec().size() ) return false;
		if ( o1ptr->del_vec().size() != o2ptr->del_vec().size() ) return false;

		for ( unsigned k = 0; k < o1ptr->add_vec().size(); k++ )
			if ( !o2ptr->adds().isset( o1ptr->add_vec()[k] ) ) return false;
		for ( unsigned k = 0; k < o2ptr->del_vec().size(); k++ )
			if ( !o2ptr->dels().isset( o1ptr->del_vec()[k] ) ) return false;
		
		return true;
	}

	float op_cost( unsigned op ) { return m_op_costs[op]; }

	std::string	domain_name() { return m_domain_name; }
	std::string	problem_name() { return m_problem_name; }

	void		set_domain_name( std::string name )
	{
		m_domain_name = name;
	}

	void		set_problem_name( std::string name )
	{
		m_problem_name = name;
	}

protected:
	void			create_fluents();
	void 			create_init_and_goal();
	void			create_operators();	

protected:
	std::vector< Fluent* >				m_fluent_table;
	std::vector< Operator* >			m_useful_operator_table;
	std::vector<unsigned>				m_initial_state;
	std::vector<unsigned>				m_goal_state;
	unsigned					m_start_id;
	unsigned					m_end_id;
	std::vector<bool>				m_is_useful;
	std::vector<bool>				m_is_reachable;
	String_Table&					m_string_table;
	std::ofstream					m_glog;
	std::vector<float>				m_op_costs;
	std::string					m_domain_name;
	std::string					m_problem_name;
};

}
#endif // PDDL.hxx
