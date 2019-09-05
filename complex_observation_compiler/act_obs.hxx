#ifndef __ACTION_EXECUTION_OBSERVATION__
#define __ACTION_EXECUTION_OBSERVATION__

#include <vector>

class Action_Execution_Observation
{
public:
	Action_Execution_Observation();
	~Action_Execution_Observation();

	void 		set_op_name( std::string& name );
	void		set_op_index( unsigned index ) { m_operator = index; }
	unsigned	get_op_index() const;
	unsigned	ordinal() const { return m_ordinal; }
	void		set_ordinal( unsigned new_ord ) { m_ordinal = new_ord; }
private:
	
	std::vector<unsigned>	m_str_codes;
	unsigned		m_operator;
	unsigned		m_ordinal;
};

class Observation_Stream : public std::vector<Action_Execution_Observation*>
{
public:
	void		handle_multiple_action_obs();
};

inline unsigned Action_Execution_Observation::get_op_index() const
{
	return m_operator;
}


#endif // act_obs.hxx
