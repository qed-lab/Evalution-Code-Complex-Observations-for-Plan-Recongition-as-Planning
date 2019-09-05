#ifndef __ACTION_EXECUTION_OBSERVATION_COMPLEX__
#define __ACTION_EXECUTION_OBSERVATION_COMPLEX__

#include <string>
#include <map>
#include <vector>
#include <set>

class Action_Execution_Complex_Observation
{
public:
  /*
   * Create an action observation
   * op_name - The name of the observed action (with parameters)
   * op_index - The index of the observed action
   * ordering_prec_fluents - A set of those fluents (as strings) which must precede this observation
   * observation_ID - The identifying fluent this observation uses for ordering
   * option_group_idx - Default 0 if not in an option group, else used to separately identify observations with the same observation_ID
   */
	Action_Execution_Complex_Observation(std::string op_name, unsigned op_index, std::set<std::string> ordering_prec_fluents, std::string observation_ID, unsigned option_group_idx=0);

  /*
   * Create a fluent observation with the observed_fluents
   * observed_fluents - A set of the fluent indices observed
   * ordering_prec_fluents - A set of those fluents (as strings) which must precede this observation
   * observation_ID - The identifying fluent this observation uses as a name and ordering
   * option_group_idx - Default 0 if not in an option group, else used to separately identify observations with the same observation_ID
   */
  Action_Execution_Complex_Observation(std::set<unsigned> observed_fluents, std::set<std::string> ordering_prec_fluents, std::string observation_ID, unsigned option_group_idx=0);
	~Action_Execution_Complex_Observation();

	void 		set_op_name( std::string& name );
	void		set_op_index( unsigned index ) { m_operator = index; }
	unsigned	get_op_index() const;
  /*
   * Distinguishes observations of the same action
  */
	unsigned	ordinal() const { return m_ordinal; }
	void		set_ordinal( unsigned new_ord ) { m_ordinal = new_ord; }

  std::string observation_ID() { return m_observation_ID; }
  unsigned option_group_idx() {return m_option_group_idx; }

  std::set<std::string>& ordering_prec_fluents() { return m_ordering_prec_fluents; }
  void set_ordering_prec_fluents(std::set<std::string>& ordering_preconditions) { m_ordering_prec_fluents = ordering_preconditions;}

  std::set<unsigned>& observed_fluents() { return m_observed_fluents; }
  void set_observed_fluents(std::set<unsigned>& observed_fluents) { m_observed_fluents = observed_fluents;}

  bool  is_action_observation() {return m_is_action_obs;}

  void print(std::ostream& os);

private:

	std::vector<unsigned>	m_str_codes; // IDK what this is used for, tbh
  std::set<std::string> m_ordering_prec_fluents;
  std::set<unsigned> m_observed_fluents;
	unsigned		m_operator;
	unsigned		m_ordinal;
  bool    m_is_action_obs;
  std::string    m_observation_ID;
  unsigned m_option_group_idx;
};

/*
 * An object to parse and contain a list of observations and the relevant fluents that indicate the observations are satisfied,
*/
class Complex_Observation_Set
{
public:
  /*
   * Constructs a Complex_Observation_Set from a file description
  */
  Complex_Observation_Set(std::string observation_filename);
  /*
   * Safely deletes pointers
  */
  ~Complex_Observation_Set();

  /*
   * Add a single observation (action or fluent) to the set.
   * observation - the observation. ~f1^f2^...^fn~ is used for fluent observations
   * observation_ID - The identifying fluent this observation uses for ordering
   * ordering_fluents - A set of those fluents (as strings) which must precede this observation
   * option_group_idx - Default 0 if not in an option group, else used to separately identify observations with the same observation_ID
  */
  std::string add_observation(std::string observation, std::string observation_ID, std::set<std::string> ordering_fluents, unsigned option_group_idx=0);

  /*
   * Add a 'garbled' observed action -- an action missing a parameter. This creates an option group with all possible actions it might be.
   * observation - the observation.
   * observation_ID - The identifying fluent this observation uses for ordering
   * ordering_fluents - A set of those fluents (as strings) which must precede this observation
  */
  std::string add_garbled_observation(std::string observation, std::string observation_ID, std::set<std::string> ordering_fluents);


  void print_all(std::ostream& os);

  /*
   * The fluents which, if all true, indicate the observation set is satisfied
  */
  std::set<std::string>& observation_fluents() {return m_observation_fluents;}
  /*
   * All observations
  */
  std::vector<Action_Execution_Complex_Observation*>& observations() { return m_observations;}


protected:
  std::map< std::string, unsigned >&	operator_index() { return m_operator_index; }
  std::map< std::string, unsigned >&	fluent_index() { return m_fluent_index; }
  std::set<std::string> parse(std::string observations, std::set<std::string> ordering_fluent_preconditions);
  std::vector<std::string> separate_members(std::string::iterator begin, std::string::iterator end);
  std::vector<std::string> split(std::string::iterator begin, std::string::iterator end, char delim);

  /*
   * Cache operators and fluents so the constructor can search indices by name
  */
  void		make_operator_and_fluent_indexes();
  std::string normalize_fluent(std::string fl_str);

private:
  std::vector<Action_Execution_Complex_Observation*> m_observations;
  std::set<std::string> m_observation_fluents;
	std::map< std::string, unsigned>	m_operator_index;
	std::map< std::string, unsigned>	m_fluent_index;
  unsigned m_observation_ID_counter;
};

inline unsigned Action_Execution_Complex_Observation::get_op_index() const
{
	return m_operator;
}


#endif // act_obs_complex.hxx
