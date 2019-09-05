#ifndef __OPTIONS__
#define __OPTIONS__

#include <string>
#include <set>

class Options
{
public:
	static Options& 	instance();
	static void 		parse_command_line( int argc, char** argv );
	~Options();
	static void		print_usage();

	std::string& 		domain_filename() { return m_domain_fname; }
	std::string& 		instance_filename() { return m_instance_fname; }
	std::string&		obs_filename() { return m_obs_fname; }
	std::set<std::string>&		obs_filenames() { return m_obs_fnames; }
  bool          multipl_obs_files() { return m_multiple_obs_files; }
	bool	     		verbose_mode() { return m_verbose; }
	bool			introduce_forgo_ops() { return m_introduce_forgo_ops; }
	bool			prob_pr_mode() { return m_prob_pr; }
	bool			convert_to_integer() { return m_convert_to_integer; }
	float			factor( ) { return m_factor; }
private:
	Options();
private:

	std::string		m_domain_fname;
	std::string		m_instance_fname;
	std::string		m_obs_fname;
  std::set<std::string> m_obs_fnames;
  bool      m_multiple_obs_files;
	bool			m_verbose;
	static const char*	m_optstring;
	bool			m_introduce_forgo_ops;
	bool			m_prob_pr;
	float			m_factor;
	bool			m_convert_to_integer;
};



#endif // options.hxx
