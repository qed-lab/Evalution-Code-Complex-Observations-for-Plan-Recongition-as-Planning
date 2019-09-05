#include "pr_obs_reader.hxx"
#include "string_ops.hxx"
#include "PDDL.hxx"
#include <fstream>
#include <cstdlib>
#include <cctype>

PR_Observation_Stream_Reader::PR_Observation_Stream_Reader()
{
	make_operator_index();
}

PR_Observation_Stream_Reader::~PR_Observation_Stream_Reader()
{
}

void PR_Observation_Stream_Reader::make_operator_index()
{
	PDDL::Task& task = PDDL::Task::instance();

	#ifdef DEBUG
	std::cout << "Building operator index..." << std::endl;
	#endif
	
	for ( unsigned op = 2; op < task.useful_ops().size(); op++ )
	{
		PDDL::Operator* op_ptr = task.useful_ops()[op];
		std::string clean_op_name = parse_operator( task.str_tab().get_token( op_ptr->code() ) );
		operator_index().insert( std::make_pair( clean_op_name, op ) );	
	}
}

std::string PR_Observation_Stream_Reader::parse_operator( std::string& line )
{
	std::string::iterator start = line.begin();
	std::string::iterator end = line.end();
	
	for ( ;start != line.end(); start++)
		if ( isalnum(*start) ) break;
	for ( ;end != start; end-- )
		if ( isalnum(*end) ) 
		{
			end++;
			break;
		}
	
	std::string name( start, end );
	#ifdef DEBUG
	std::cout << "Operator found:" << name << std::endl;
	#endif
	return name;
} 

void PR_Observation_Stream_Reader::parse( const std::string& fname )
{
	std::ifstream in( fname.c_str() );

	if ( in.fail() )
	{
		std::cerr << "Could not read observations file ";
		std::cerr << fname << std::endl;
		std::cerr << "Bailing out!" << std::endl;
		std::exit(1);
	}	

	char line_buffer[256000];
	bool op_name_parsed = false;

	std::string line;
	unsigned n_line = 0;	

	while ( !in.eof() )
	{
		std::string::iterator head;
		n_line++;
		in.getline( line_buffer, 255999, '\n' );
		line.assign( line_buffer );
		head = line.begin();
		std::string op_name = parse_operator( line );
		if ( op_name.empty() ) continue;
		for ( unsigned k = 0; k < op_name.size(); k++ )
			op_name[k] = toupper(op_name[k]);
		std::map< std::string, unsigned>::iterator it = operator_index().find( op_name );
		if ( it == operator_index().end() )
		{
			std::cout << "Could not find operator ";
			std::cout << "(" << op_name << ")" << std::endl;
			std::cout << "Bailing out!" << std::endl;
			std::exit(1);
		}
		Action_Execution_Observation* new_obs = new Action_Execution_Observation();
		new_obs->set_op_name( op_name );
		new_obs->set_op_index( it->second );	
		m_stream.push_back( new_obs );
	}

	in.close();

	std::cout << "Read from " << fname << " " << m_stream.size() << " observations" << std::endl;
	m_stream.handle_multiple_action_obs();
}
