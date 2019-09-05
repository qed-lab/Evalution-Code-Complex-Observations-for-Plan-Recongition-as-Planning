#ifndef __pr_strips_mapping__
#define __pr_strips_mapping__

#include "strips_writer.hxx"
#include "act_obs.hxx"

class PR_STRIPS_Mapping : public STRIPS_Writer
{
public:

	PR_STRIPS_Mapping( Observation_Stream& stream);
	PR_STRIPS_Mapping( Observation_Stream& stream, bool negated );
	PR_STRIPS_Mapping( Observation_Stream& stream, bool negated, bool to_int, float factor );
	virtual ~PR_STRIPS_Mapping();

	void write();

	Name_Table&		exp_str() { return m_explained_str; }
	Name_Table&		not_exp_str() { return m_not_explained_str; }

	Observation_Stream& 	obs_stream() { return m_obs_stream; }

protected:

	void	make_explained_strings();
	void	write_predicates_definitions();
	void	write_actions_definitions();
	void	write_init_definition();
	void	write_goal_definition();

	void 	write_explain_obs_op( unsigned op, unsigned k );
	void	write_non_explaining_obs_op( unsigned op, unsigned k );
	void	write_regular_op( unsigned op );

protected:

	Name_Table		m_explained_str;
	Name_Table		m_not_explained_str;
	Observation_Stream&	m_obs_stream;
	bool			m_negated;
	bool			m_convert_to_integer;
	float			m_factor;
};

#endif // pr_strips_mapping.hxx
