#ifndef __STRING_OPS__
#define __STRING_OPS__

#include <string>
#include <vector>
#include <iostream>
#include <sstream>

typedef std::vector<std::string>   TokenList;

inline TokenList split( std::string s, char splitter )
{
	TokenList tokens;

	unsigned offset = s.find( splitter );

	if ( offset == std::string::npos )
		return tokens;


	std::string token = s.substr( 0, offset );
	if ( !token.empty() )
		tokens.push_back( token );
	s = s.substr( offset + 1, s.size() - (offset+1) );

	while( !s.empty() )
	{
		offset = s.find( splitter );
		if (offset == std::string::npos )
		{
			tokens.push_back(s);
			return tokens;
		}
		token = s.substr( 0, offset );
		if ( !token.empty() )
			tokens.push_back( token );
		s = s.substr( offset + 1, s.size() - (offset+1));
	}

	return tokens;
}

template <class T>
std::string to_string( T& value, std::ios_base& (*converter)( std::ios_base& ) )
{
	std::stringstream ss;
	ss << converter << value;
	return ss.str();
}

template <class T>
bool from_string( T& value, const std::string& s, std::ios_base& (*converter)( std::ios_base& ) )
{
	std::istringstream iss( s );
	return !(iss >> converter >> value).fail();
}

inline std::string	strip(std::string input)
{
	std::string::iterator start = input.begin();
	std::string::iterator end = input.end();

	for ( ;start != input.end(); start++)
		if ( isalnum(*start) || *start == '[' || *start == '{' || *start == '|' || *start == '~' || *start == '^' || *start == '?') break;
	for ( ;end != start; end-- )
		if ( isalnum(*end) || *end == ']' || *end == '}' || *end == '|' || *end == '~' || *end == '^' || *end == '?')
		{
			end++;
			break;
		}

	std::string stripped;
	stripped.assign( start, end );
	return stripped;
}

inline	std::string	replace( std::string input, char o, char n )
{
	std::string repl;
	repl.reserve( input.size() );
	for ( unsigned k = 0; k < input.size(); k++ )
		if ( input[k] == o ) repl.push_back( n );
		else repl.push_back( input[k] );
	return repl;
}

#endif // string_ops.hxx
