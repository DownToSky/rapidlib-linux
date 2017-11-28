#include <vector>
#include <string>
#include <map>
#include <tuple>

using namespace std;

// List formating
#define START_CHAR	'S'
#define DELIM_CHAR	'_'

// Easy way to get at each part of the address index_t triplet 
#define INDEX_TOP(idx)		get<0>(idx)
#define INDEX_LEVEL(idx)	get<1>(idx)
#define INDEX_BASIC(idx)	get<2>(idx)

// Get edge_t and xml_edge_t fields
#define EDGE_VALUE(edge)	get<0>(edge)	// mission value / weight
#define EDGE_COST(edge)		get<1>(edge)	// energy cost
#define EDGE_INDEX(edge)	get<2>(edge)	// Scheme edge has index
#define EDGE_NAME(edge)		get<2>(edge)	// XML has string

// Sets all 3 values of the index_t triple to 0
#define ZERO_OUT_IDX_T(idx)		\
		get<0>(idx) = 0;		\
		get<1>(idx) = 0;		\
		get<2>(idx) = 0;

// Check's if string is a node representation 
#define IS_NODE(str)							\
		str.find(START_CHAR) != string::npos	\
		&& str.find(DELIM_CHAR) != string::npos 

#define MIN 0
#define MAX 1

// top | level | basic - unsigned shorts to fit in an 8 byte hashed value for map key
typedef tuple<unsigned short,unsigned short, unsigned short> index_t;

// value | cost | index_t = address (source of dependency
typedef tuple<float, float, index_t > edge_t;	

// XML version of edge_t  address is a string 
typedef tuple<float, float, string> xml_edge_t;

extern bool DEBUG_MSGS, SUPPRESS_ERRORS;

// Base class for Top, Level, and Basic nodes
class Node 
{
    private:
        vector<vector<edge_t>> edges;			// Scheme
        vector<vector<xml_edge_t>> xml_edges;	// XML
	vector<vector<xml_edge_t>> xml_outedges;
        index_t address;
        string name;
        bool basic, level, top;
    public:
        vector<vector<edge_t>> *getSchemeEdges(void);
        vector<vector<xml_edge_t>> *getXMLEdges(void);
	vector<vector<xml_edge_t>> *getXMLOutEdges(void);
        index_t *getAddr(void);
        string getName();
        void setEdgeWeight(index_t, float value = 0, float cost = 0);		// Might not need cost default = 0
        void addEdges(vector<edge_t>);
        void addEdges(vector<xml_edge_t>);
	void addOutEdges(vector<xml_edge_t>);
        void setAddr(index_t *);	// Scheme
        void setType(int type);		// 0 = top , 1 = level, 2 = basic
        void setName(string name);
        bool isBasic(void);
        bool isLevel(void);
        bool isTop(void);
};

// Basic nodes - represent redundant implementations
class Basic : public Node 
{	
	private:
		double value;
		float cost;
	public:
		void setValue(double );
		void setCost(float);
		double getValue(void);
		float getCost(void);
		Basic(index_t *, string = "");		// Scheme
		Basic(string);						// XML
};

// Level nodes (container for a group of basic nodes) - represent functions of a service 
class Level : public Node 
{
	private:
		int level;		// XML level number
		vector<Basic *> basic_nodes;	
	public:
		vector<Basic *> *getBasicNodes(void);
		void addBasicNode(Basic *);
		int getLevelNum();
		Level(index_t *);	// Scheme
		Level(string);			// XML
		~Level();
};

// Top nodes - represent a single service 
class Top : public Node
{
	private:
		vector<Level *> level_nodes;	// XML data structure
	public:
		vector<Level *> *getLevelNodes(void);
		void addLevelNode(Level *);
		Top(index_t *, string = "");	// Scheme
		Top(string);					// XML
		~Top();
};

// Main Data Structure for both XML and Scheme List representations of RSDG
class RSDG
{
	private:
		double	budget;
		long long hashIndex(index_t *);
		map<long long, Node *> rsdg;	// Scheme 	
		vector<Top *> xml_rsdg;			// XML
		vector<string> forceOn;
		vector<string> forceOnTmp;
		vector<string> forceOff;
	public:
		double  targetMV;
		bool minmax;
		Node* getNodeFromIndex(index_t *);		// Scheme 
		Node* getNodeFromName(string);			// XML
		void parseSchemeList(string infile);	// parse Scheme List
		void parseXML(string infile);			// parse XML 
		void addNode(index_t *);				// Scheme format
		void addNode(string);					// XML format  
		void writeSchemeLp(string);				// lp from Scheme 
		void writeXMLLp(string,bool);				// lp from XML
		void setBudget(double);					// Set energy budget
		bool getSolution(void);					// Solve using heuristics
		void updateMissionValue(string serviceName, int value, bool exp);
		void updateCost(string name, double cost);
		void updateEdgeCost(string, string, double);
		void addOn(string);
		void addTmpOn(string);
		void resetTmpOn();
		void addOff(string);
		vector<string> getOn();
		vector<string> getOff();

		~RSDG();
};

RSDG* rsdgGen(string);