#include <cassert>
#include <cstdlib>
#include <string>
#include "act_obs.hxx"
#include "pddl_string_table.hxx"
#include "PDDL.hxx"

Action_Execution_Observation::Action_Execution_Observation()
	: m_ordinal( 0 )
{
}

Action_Execution_Observation::~Action_Execution_Observation()
{
}

void Action_Execution_Observation::set_op_name( std::string& name )
{
	PDDL::Task& task = PDDL::Task::instance();
	
	m_str_codes.push_back( task.str_tab().get_code( name ) );
}

void Observation_Stream::handle_multiple_action_obs()
{
	std::vector<unsigned> occ;

	for ( unsigned i = 0; i < size(); i++ )
	{
		if ( at(i)->ordinal() != 0 ) continue;

		occ.clear();
		occ.push_back( i );
		for ( unsigned j = i+1; j < size(); j++ )
		{
			if ( at(j)->ordinal() != 0 ) continue;
			if ( at(j)->get_op_index() == at(i)->get_op_index() )
				occ.push_back( j );
		}
		for ( unsigned j = 0; j < occ.size(); j++ )
			at( occ[j] )->set_ordinal( j+1 );
	}	
}
