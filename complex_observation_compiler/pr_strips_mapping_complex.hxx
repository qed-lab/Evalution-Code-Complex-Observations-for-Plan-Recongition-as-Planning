#ifndef __pr_strips_mapping_complex__
#define __pr_strips_mapping_complex__

#include "strips_writer.hxx"
#include "act_obs_complex.hxx"

class PR_STRIPS_Mapping_Complex : public STRIPS_Writer
{
public:

	PR_STRIPS_Mapping_Complex( Complex_Observation_Set& set);
	PR_STRIPS_Mapping_Complex( Complex_Observation_Set& set, bool negated );
	PR_STRIPS_Mapping_Complex( Complex_Observation_Set& set, bool negated, bool to_int, float factor );
	virtual ~PR_STRIPS_Mapping_Complex();

	void write();

	Name_Table&		exp_str() { return m_explained_str; }
	Name_Table&		not_exp_str() { return m_not_explained_str; }

	// Complex_Observation_Set& 	obs_set() { return m_obs_set.observations(); }

protected:

	// void	make_explained_strings();
	void	write_predicates_definitions();
	void	write_actions_definitions();
	void	write_init_definition();
	void	write_goal_definition();

	void 	write_explain_obs_op( Action_Execution_Complex_Observation* obs_ptr );
	// void	write_non_explaining_obs_op( unsigned op, unsigned k );
	void	write_regular_op( unsigned op );

protected:

	Name_Table		m_explained_str;
	Name_Table		m_not_explained_str;
	Complex_Observation_Set&	m_obs_set;
	bool			m_negated;
	bool			m_convert_to_integer;
	float			m_factor;
};

#endif // pr_strips_mapping.hxx
