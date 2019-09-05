#ifndef __STRIPS_WRITER__
#define __STRIPS_WRITER__

#include <vector>
#include <string>
#include <fstream>

class STRIPS_Writer
{
public:
	typedef std::vector<std::string> Name_Table;

	STRIPS_Writer();
	virtual ~STRIPS_Writer();

	void write();

	Name_Table&	pred_str() { return m_pred_names; }
	Name_Table&	action_str() { return m_op_names; }
	std::ofstream&	problem_stream() { return m_problem_stream; }
	std::ofstream&  domain_stream() { return m_domain_stream; }
	void		set_base_path( std::string path ) { m_base_path = path; }
	std::string	base_path() { return m_base_path; }


protected:

	virtual void write_domain_definition();
	virtual void write_problem_definition();

	virtual void write_requirements();
	virtual void write_predicates_definitions();
	virtual void write_actions_definitions();
	virtual void write_functions();

	virtual void write_init_definition();
	virtual void write_goal_definition();
	virtual void write_metric_definition();

	void make_domain_outfile_name();
	void make_problem_outfile_name();

	void make_predicate_strings();
	void make_action_strings();
private:

	
	Name_Table	m_pred_names;
	Name_Table	m_op_names;


	std::string	m_domain_outfile_name;
	std::string	m_problem_outfile_name;
	std::ofstream	m_domain_stream;
	std::ofstream	m_problem_stream;
	std::string	m_base_path;
};



#endif // strips_writer.hxx
