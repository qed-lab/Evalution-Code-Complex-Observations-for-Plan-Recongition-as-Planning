#include <cassert>
#include <cstdlib>
#include <string>
#include <iostream>
#include "act_obs_complex.hxx"
#include "PDDL.hxx"

#include "string_ops.hxx"

///////// SINGLE OBSERVATIONS ////////////

Action_Execution_Complex_Observation::Action_Execution_Complex_Observation(std::string op_name, unsigned op_index, std::set<std::string> ordering_prec_fluents, std::string observation_ID, unsigned option_group_idx)
	: m_ordinal( 0 ), m_observation_ID(observation_ID), m_is_action_obs(true), m_option_group_idx(option_group_idx)
{
  set_op_name(op_name);
  set_op_index(op_index);
  set_ordering_prec_fluents(ordering_prec_fluents);
}


Action_Execution_Complex_Observation::Action_Execution_Complex_Observation(std::set<unsigned> observed_fluents, std::set<std::string> ordering_prec_fluents, std::string observation_ID, unsigned option_group_idx)
	: m_ordinal( 0 ), m_observation_ID(observation_ID), m_is_action_obs(false), m_option_group_idx(option_group_idx)
{
  set_observed_fluents(observed_fluents);
  set_ordering_prec_fluents(ordering_prec_fluents);
}


Action_Execution_Complex_Observation::~Action_Execution_Complex_Observation()
{
}

void Action_Execution_Complex_Observation::set_op_name( std::string& name )
{
	PDDL::Task& task = PDDL::Task::instance();
	m_str_codes.push_back( task.str_tab().get_code( name ) );
}

void Action_Execution_Complex_Observation::print(std::ostream& os)
{
	os << m_observation_ID << ":"; // << m_observation_string;
  if (m_is_action_obs) {
    os << "\tobserved action #: "<< m_operator;
  } else {
    os << "\tobserved fluents:\n";
    for (std::set<unsigned>::iterator fl = m_observed_fluents.begin(); fl != m_observed_fluents.end(); ++fl) {
      os << ", " << *fl;
    }
  }
  os << "\n\tpreconditions:\n";
  for (std::set<std::string>::iterator fl = m_ordering_prec_fluents.begin(); fl != m_ordering_prec_fluents.end(); ++fl) {
    os << "\t\t" << *fl << "\n";
  }
  os << std::endl;
}





// void Complex_Observation_Set::handle_multiple_action_obs()
// {
// 	std::vector<unsigned> occ;
//
// 	for ( unsigned i = 0; i < size(); i++ )
// 	{
// 		if ( at(i)->ordinal() != 0 ) continue;
//
// 		occ.clear();
// 		occ.push_back( i );
// 		for ( unsigned j = i+1; j < size(); j++ )
// 		{
// 			if ( at(j)->ordinal() != 0 ) continue;
// 			if ( at(j)->get_op_index() == at(i)->get_op_index() )
// 				occ.push_back( j );
// 		}
// 		for ( unsigned j = 0; j < occ.size(); j++ )
// 			at( occ[j] )->set_ordinal( j+1 );
// 	}
// }

////////////// OBSERVATION SETS //////////////////


Complex_Observation_Set::Complex_Observation_Set(std::string observation_filename)
: m_observation_ID_counter(0), m_observations()
{

  std::ifstream in( observation_filename.c_str() );

	if ( in.fail() )
	{
		std::cerr << "Could not read observations file ";
		std::cerr << observation_filename << std::endl;
		std::cerr << "Bailing out!" << std::endl;
		std::exit(1);
	}

  // Get the operators/fluents from the domain, for easy referencing
  make_operator_and_fluent_indexes();

  std::stringstream buffer;
  buffer << in.rdbuf();
  std::string observations = buffer.str();
  observations = strip( observations );

  // std::cout << observations << std::endl;

  std::set<std::string> no_preconditions;
  m_observation_fluents = parse(observations, no_preconditions);

  in.close();

	std::cout << "Read from " << observation_filename << " " << m_observation_fluents.size() << " observations" << std::endl;
	// m_set.handle_multiple_action_obs();

}

Complex_Observation_Set::~Complex_Observation_Set()
{
  // Clean up the allocated memory for observations
  for (int i = 0; i < m_observations.size(); i++) {
    delete m_observations[i];
  }
}


void Complex_Observation_Set::print_all(std::ostream& os){
  os << "Observations: \n";
  for (int i = 0; i < m_observations.size(); i++) {
    m_observations[i]->print(os);
  }
  os <<std::endl;
}


// Get all the operators/fluents from the domain, for easy referencing
void Complex_Observation_Set::make_operator_and_fluent_indexes()
{
	PDDL::Task& task = PDDL::Task::instance();

	#ifdef DEBUG
	std::cout << "Building operator index..." << std::endl;
	#endif
  // TODO: Why 2????
	for ( unsigned op = 2; op < task.useful_ops().size(); op++ )
	{
		PDDL::Operator* op_ptr = task.useful_ops()[op];
		std::string clean_op_name = strip( task.str_tab().get_token( op_ptr->code() ) );
		operator_index().insert( std::make_pair( clean_op_name, op ) );
	}

  for ( unsigned f = 1; f < task.fluents().size(); f++ )
	{
		PDDL::Fluent* ft = task.fluents()[f];
		// std::cout << task.str_tab().get_token( ft->code() ) << " -> ";
		std::string clean_ft_name = strip(task.str_tab().get_token( ft->code() ));
		// std::cout << clean_ft_name << " -> ";
	  fluent_index().insert( std::make_pair( replace( clean_ft_name, ' ', '_' ), f) );
		// std::cout << m_pred_names.back() << std::endl;
	}
}

std::set<std::string> Complex_Observation_Set::parse(std::string observations, std::set<std::string> ordering_fluent_preconditions)
{
  std::set<std::string> contained_observation_fluents;

  observations = strip( observations );
  // std::cout << observations << std::endl;
  std::string::iterator obs_start = observations.begin();
  std::string::iterator obs_end = std::prev(observations.end());
  char begin_char = *(obs_start);
  char end_char = *(obs_end);

  // Case: unordered group
  if( begin_char == '{' && end_char == '}')
  {
    std::vector<std::string> group_members = separate_members(std::next(obs_start), std::prev(obs_end));

    // Parse every subgroup and add to the set of all observation fluents
    for (std::vector<std::string>::iterator member = group_members.begin(); member != group_members.end(); ++member) {
      std::set<std::string> member_observation_fluents = parse(*member, ordering_fluent_preconditions);
      contained_observation_fluents.insert(member_observation_fluents.begin(), member_observation_fluents.end());
    }
  }

  // Case: ordered group
  else if( begin_char == '[' && end_char == ']')
  {
    std::vector<std::string> group_members = separate_members(std::next(obs_start), std::prev(obs_end));

    std::set<std::string> current_observation_fluents;

    // Parse every subgroup and add to the set of all observation fluents
    for (std::vector<std::string>::iterator member = group_members.begin(); member != group_members.end(); ++member) {
      // Be sure to add the outside preconditions back in
      current_observation_fluents.insert(ordering_fluent_preconditions.begin(), ordering_fluent_preconditions.end());
      // The fluents from this group continue as preconditions to the next group
      current_observation_fluents = parse(*member, current_observation_fluents);
      contained_observation_fluents.insert(current_observation_fluents.begin(), current_observation_fluents.end());
    }
  }

  // Case: option group
  else if( begin_char == '|' && end_char == '|')
  {
    // Split by commas and parse each as a base case
    std::vector<std::string> members = split(std::next(obs_start), std::prev(obs_end), ',');
    std::string observation_ID = "MUTEX_" + std::to_string(m_observation_ID_counter);
    m_observation_ID_counter++;
    unsigned option_group_idx = 1;
    for (std::vector<std::string>::iterator member = members.begin(); member != members.end(); ++member) {
      observation_ID = add_observation(strip(*member), observation_ID, ordering_fluent_preconditions, option_group_idx++);
      contained_observation_fluents.insert(observation_ID);
    }

  }
  // Base case: a single observation
  else
  {
    std::string observation_ID = "OBSERVATION_" + std::to_string(m_observation_ID_counter);
    m_observation_ID_counter++;
    observation_ID = add_observation(observations, observation_ID, ordering_fluent_preconditions);
    contained_observation_fluents.insert(observation_ID);

  }

  return contained_observation_fluents;

}



std::string Complex_Observation_Set::normalize_fluent(std::string fl_str){
  fl_str = strip(fl_str);
  std::string normalized;

  // Replace whitespaces with underscores, and capitalize everything else
  for(std::string::iterator place = fl_str.begin(); place != fl_str.end(); ++place){
    if( isspace(*place)){
      while(isspace(*place) && place != fl_str.end()){
        ++place;
      }
      normalized.append(1,'_');
    }
    normalized.append(1,toupper(*place));
  }
  // std::cout << "NORMALIZED: "<< normalized << std::endl;
  return normalized;
}

std::string Complex_Observation_Set::add_observation(std::string observation, std::string observation_ID, std::set<std::string> ordering_fluents, unsigned option_group_idx){

  observation = strip(observation);
  std::string::iterator obs_start = observation.begin();
  std::string::iterator obs_end = std::prev(observation.end());
  char begin_char = *(obs_start);
  char end_char = *(obs_end);

  // Fluent observation
  if( begin_char == '~' && end_char == '~'){
    std::vector<std::string> fluentlist = split(std::next(obs_start), std::prev(obs_end), '^');
    std::set<unsigned> fluent_indices;
    for (int i = 0; i < fluentlist.size(); i++) {
      fluentlist[i] = normalize_fluent(fluentlist[i]);
      std::map< std::string, unsigned>::iterator it = fluent_index().find(fluentlist[i]);
      if ( it == fluent_index().end() )
  		{
  			std::cout << "Could not find fluent ";
  			std::cout << "(" << fluentlist[i] << ")" << std::endl;
  			std::cout << "Bailing out!" << std::endl;
  			std::exit(1);
  		}
      fluent_indices.insert(it->second);
    }
    // std::set<std::string> fluents(fluentlist.begin(), fluentlist.end());
    Action_Execution_Complex_Observation* new_obs = new Action_Execution_Complex_Observation(fluent_indices, ordering_fluents, observation_ID, option_group_idx);
		m_observations.push_back( new_obs );
    return new_obs->observation_ID();
  }
  // Action observation
  else {
    for ( unsigned k = 0; k < observation.size(); k++ ){
			observation[k] = toupper(observation[k]);
      if(observation[k] == '?'){
        return add_garbled_observation(observation, observation_ID, ordering_fluents);
      }
    }
		std::map< std::string, unsigned>::iterator it = operator_index().find( observation );
		if ( it == operator_index().end() )
		{
			std::cout << "Could not find operator ";
			std::cout << "(" << observation << ")" << std::endl;
			std::cout << "Bailing out!" << std::endl;
			std::exit(1);
		}
		Action_Execution_Complex_Observation* new_obs = new Action_Execution_Complex_Observation(observation, it->second, ordering_fluents, observation_ID, option_group_idx);
		m_observations.push_back( new_obs );
    return new_obs->observation_ID();
  }

}

std::string Complex_Observation_Set::add_garbled_observation(std::string observation, std::string observation_ID, std::set<std::string> ordering_fluents){

  observation = strip(observation);
  for(auto& x: observation){
    x = toupper(x);
  }
  std::string::iterator obs_start = observation.begin();
  std::string::iterator obs_end = std::prev(observation.end());
  char begin_char = *(obs_start);
  char end_char = *(obs_end);

  int q_pos = observation.find("?");
  if ( q_pos == std::string::npos){
    std::cout << "Tried to garble an observation without a question mark." << std::endl;
    std::cout << "Bailing out!" << std::endl;
    std::exit(1);
  }
  std::string before_q = observation.substr(0, q_pos);
  std::string after_q = observation.substr(q_pos+1);
  // std::cout << before_q << " __?__ " << after_q << std::endl;

  int option_group_idx = 1;
  std::string obs_fluent = ""; // Start empty so if no operator matches, no harm done
  for(std::map<std::string,unsigned>::iterator it = m_operator_index.begin(); it != m_operator_index.end(); ++it){
    std::string this_op_name = it->first;
    int missing_size = this_op_name.size() - before_q.size() - after_q.size();
    // If this operator is big enough to be it
    if(missing_size > 0){
      std::string head = this_op_name.substr(0,q_pos);
      std::string tail = this_op_name.substr(q_pos+missing_size);
      // Everything around the question mark matches:
      if(before_q.compare(head) ==0 && after_q.compare(tail) ==0){
        obs_fluent = add_observation(this_op_name, observation_ID, ordering_fluents, option_group_idx++);
        // std::cout << "GARBLE: " << this_op_name << std::endl;
      }
    }

  }
  return obs_fluent;


}



std::vector<std::string> Complex_Observation_Set::separate_members(std::string::iterator begin, std::string::iterator end){
  std::vector<std::string> members;

  int braces = 0; // How many enclosing braces we're inside
  int brackets = 0; // How many enclosing brackets we're inside
  char bar = 0; // In an option group or not

  std::string::iterator itemStart = begin;
  std::string::iterator place = begin;
  for(; place != end; ++place) {
    char the_char = *place;
    if(the_char == '{') {
      braces++;
      continue;
    }
    if(the_char == '}') {
      braces--;
      continue;
    }
    if(the_char == '[') {
      brackets++;
      continue;
    }
    if(the_char == ']') {
      brackets--;
      continue;
    }
    if( the_char == '|') {
      bar = !bar;
      continue;
    }
    if(the_char == ',' && braces == 0 && brackets == 0 && !bar) {
      std::string member(itemStart, place);
      members.push_back(member);
      itemStart = std::next(place);
    }
  }
  std::string member(itemStart, place);
  members.push_back(member);

  return members;


}


std::vector<std::string> Complex_Observation_Set::split(std::string::iterator begin, std::string::iterator end, char delim) {
    std::vector<std::string> members;

    std::string::iterator itemStart = begin;
    std::string::iterator place = begin;
    for(; place != end; ++place){
      if(*place == delim){
        std::string member(itemStart, place);
        members.push_back(strip(member));
        itemStart = std::next(place);
      }
    }
    std::string member(itemStart, std::next(place));
    members.push_back(strip(member));

    return members;
}
