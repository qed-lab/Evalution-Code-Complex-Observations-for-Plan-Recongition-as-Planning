#include "options.hxx"
#include <getopt.h>
#include <iostream>
#include <cstdlib>

const char* Options::m_optstring = "d:i:o:vh?FPZ:";

Options::Options()
	: m_verbose( false ), m_introduce_forgo_ops( false ), m_prob_pr( false ),
	m_factor( 1.0 ), m_convert_to_integer( false ), m_multiple_obs_files(false)
{
}

Options::~Options()
{
}

Options& Options::instance()
{
	static Options instance;
	return instance;
}

void Options::parse_command_line( int argc, char** argv )
{
	int opt = getopt( argc, argv, m_optstring );
	bool domain_specified = false;
	bool instance_specified = false;
	bool obs_specified = false;

	Options& options = instance();

	while( opt != -1 )
	{
		switch (opt)
		{
		case 'd' : // domain file
			options.m_domain_fname = optarg;
			domain_specified = true;
			break;
		case 'i' : // instance file
			options.m_instance_fname = optarg;
			instance_specified = true;
			break;
		case 'o' : // observations file
      if(obs_specified){
        options.m_obs_fnames.insert(options.m_obs_fname);
        options.m_obs_fnames.insert(optarg);
        options.m_multiple_obs_files = true;
      } else {
        options.m_obs_fname = optarg;
        obs_specified = true;
      }
			break;
		case 'v' : // verbose mode activated
			options.m_verbose = true;
			break;
		case 'F' :
			options.m_introduce_forgo_ops = true;
			break;
		case 'P' : // Probabilistic PR mode activated
			options.m_prob_pr = true;
			break;
		case 'Z' : // integerize costs
			options.m_convert_to_integer = true;
			options.m_factor = atof( optarg );
			break;
		case '?':
		case 'h':
			print_usage();
			std::exit(0);
			break;
		default:
			std::cerr << "Unrecognized option" << opt << std::endl;
			print_usage();
		}
		opt = getopt( argc, argv, m_optstring );
	}

	if ( !domain_specified )
	{
		std::cerr << "Domain description not specified" << std::endl;
		print_usage();
		std::exit(1);
	}
	if ( !instance_specified )
	{
		std::cerr << "Instance description not specified" << std::endl;
		print_usage();
		std::exit(1);
	}
	if ( !obs_specified )
	{
		std::cerr << "Observations description not specified" << std::endl;
		print_usage();
		std::exit(1);
	}
}

void Options::print_usage()
{
	std::cerr << "pr2plan_complex: Plan Recognition with complex observations to Cost-Based STRIPS Planning mapping" << std::endl;
	std::cerr << "Usage: ./pr2plan_complex -d <domain file> -i <instance file> -o <obs file>" << std::endl;
	std::cerr << "Mandatory parameters:" << std::endl;
	std::cerr << "-d         Domain specification in PDDL 2.1" << std::endl;
	std::cerr << "-i         Instance specification in PDDL 2.1" << std::endl;
	std::cerr << "-o         Observation file" << std::endl;
	std::cerr << "Optional parameters: " << std::endl;
	std::cerr << "-v         Verbose Mode ON (default is OFF)" << std::endl;
	std::cerr << "-F         Introduce forgo(obs) ops" << std::endl;
	std::cerr << "-P         Generate Planning problems necessary for probabilistic PR" << std::endl;
}
