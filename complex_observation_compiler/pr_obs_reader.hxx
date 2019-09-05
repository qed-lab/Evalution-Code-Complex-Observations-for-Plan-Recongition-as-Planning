#ifndef __PR_OBS_READER__
#define __PR_OBS_READER__

#include <string>
#include <map>
#include "act_obs.hxx"

class PR_Observation_Stream_Reader
{
public:

	PR_Observation_Stream_Reader();
	~PR_Observation_Stream_Reader();

	void parse( const std::string& fname );

	Observation_Stream& 			obs_stream() { return m_stream; }
	std::map< std::string, unsigned >&	operator_index() { return m_operator_index; }

protected:
	
	std::string	parse_operator( std::string& text );
	void		make_operator_index();	

private:
	std::map< std::string, unsigned>	m_operator_index;
	Observation_Stream 			m_stream;

};

#endif // pr-obs-reader.hxx
