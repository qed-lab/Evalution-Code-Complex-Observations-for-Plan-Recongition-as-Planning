#ifndef __PDDL_BASIC_TYPES__
#define __PDDL_BASIC_TYPES__

#include <vector>
#include <string>

namespace PDDL
{

typedef std::string		Token;			// A string
typedef std::vector<Token> 	Token_Vector;		// A vector of strings
typedef std::vector<Token*>	Token_Ref_Vector; 	// A vector of references to vectors
typedef int			Token_Code;
typedef std::vector<int>	Token_Code_Vector;

// Enum for indicating whether a node in a formula is an atomic expression,
// a junctor, a quantor, etc.
enum Connective
{
	TRUE,
	FALSE,
	ATOM,
	NOT,
	AND,
	OR,
	FORALL,
	EXISTS,
	WHEN,
	EQUALS
};

// strips leading/trailing whitespace from token
inline Token strip( Token& tok )
{
	Token tmp;
	tmp.reserve( tok.size() );
	for ( unsigned i = 0; i < tok.size(); i++ )
		if ( !isblank( tok[i] ) ) tmp.push_back( tok[i] );
	return tmp;
}

}

#endif // pddl_basic_types.hxx
