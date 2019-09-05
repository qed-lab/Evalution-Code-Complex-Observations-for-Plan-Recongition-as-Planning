#ifndef __LIB_FF_H__
#define __LIB_FF_H__

#ifdef __cplusplus
#define EXTERN extern "C"
#include <string>
#include <vector>
#else
#define EXTERN extern
#endif

#include "ff.h"

EXTERN int	FF_parse_problem( const char* domain_file, const char* instance_file );
EXTERN int	FF_instantiate_problem();

#ifdef __cplusplus

// C++ helper functions
namespace FF
{

inline std::string	get_domain_name()
{
	return std::string( gdomain_name );
}

inline std::string	get_problem_name()
{
	return std::string(gproblem_name);
}

inline void 		get_initial_state( std::vector<unsigned>& init_atoms )
{
	init_atoms.resize( ginitial_state.num_F );
	for ( int i = 0; i < ginitial_state.num_F; i++ )
		init_atoms[i] = ginitial_state.F[i];
}

inline void		get_goal_state( std::vector<unsigned>& goal_atoms )
{
	goal_atoms.resize( gnum_logic_goal );
	for ( int i = 0; i < gnum_logic_goal; i++ )
		goal_atoms[i] = glogic_goal[i];
}

inline float		get_op_metric_cost( int index )
{
	return gef_conn[index].cost + gtt;
}

inline std::string	get_op_name( int index )
{
	int i;
  // std::cout << "Jenni: libff.h FF::get_op_name 0 gnum_actions: "<< gnum_actions  << std::endl;
	Action *a = gop_conn[index].action;
  // std::cout << "Jenni: libff.h FF::get_op_name 1" << std::endl;
	std::string str;

	if ( !a->norm_operator && !a->pseudo_action )
	{
		return std::string( "(REACH-GOAL)" );
	}
  // std::cout << "Jenni: libff.h FF::get_op_name 2" << std::endl;
	str += "(";
 	str += a->name;
  // std::cout << "Jenni: libff.h FF::get_op_name 3" << std::endl;
	for ( i = 0; i < a->num_name_vars; i++ )
	{
		str += " ";
		str += gconstants[a->name_inst_table[i]];
	}
  // std::cout << "Jenni: libff.h FF::get_op_name 4" << std::endl;
	str += " )";
	return str;
}

inline std::string	get_ft_name( int index )
{
	Fact* f = &(grelevant_facts[index]);
	int j;

	if ( f->predicate == -3 )
	{
		return std::string( "GOAL-REACHED" );
	}

	if ( f->predicate == -1 )
	{
		std::string str( "(=" );
		for ( j=0; j<2; j++ )
		{
			str += " ";
			if ( f->args[j] >= 0 )
			{
				str += gconstants[(f->args)[j]];
			}
			else
			{
				str += "x";
				str += DECODE_VAR( f->args[j] );
			}
		}
		str += ")";
		return str;
	}

	if ( f->predicate == -2 )
	{
		std::string str( "(!=" );
		for ( j=0; j<2; j++ )
		{
			str += " ";
			if ( f->args[j] >= 0 )
			{
				str += gconstants[(f->args)[j]];
			}
			else
			{
				str += "x";
				str += DECODE_VAR( f->args[j] );
			}
		}
		str += ")";
		return str;
	}

	std::string str( "(" );
	str += gpredicates[f->predicate];
	for ( j=0; j<garity[f->predicate]; j++ )
	{
		str += " ";
		if ( f->args[j] >= 0 )
		{
			str += gconstants[(f->args)[j]];
		}
		else
		{
			str += "x";
			str += DECODE_VAR( f->args[j] );
		}
	}
	str += ")";
	return str;
}

}

#endif

#endif // libff.h
