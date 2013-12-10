#include <algorithm>
#include <ostream>
#include <boost/foreach.hpp>
#include <orang/table.h>
#include <orang/graph.h>

#include "test.h"

using std::copy;
using std::ostream_iterator;

namespace orang {
bool operator==(const Graph& g1, const Graph& g2) {
  Var g1Vertices = g1.numVertices();
  if (g1Vertices != g2.numVertices()) {
    return false;
  }

  for (Var v = 0; v < g1Vertices; ++v) {
    if (g1.degree(v) != g2.degree(v)
        || !equal(g1.adjacencyBegin(v), g1.adjacencyEnd(v), g2.adjacencyBegin(v))) {
      return false;
    }
  }

  return true;
}

std::ostream& operator<<(std::ostream& out, const Graph& g) {
  out << "Graph(";
  Var numVerts = g.numVertices();
  for (Var v = 0; v < numVerts; ++v) {
    for (Graph::iterator adjIter = g.adjacencyBegin(v), adjEnd = g.adjacencyEnd(v); adjIter != adjEnd; ++adjIter) {
      out << '<' << v << ',' << *adjIter << '>' << (v == numVerts - 1 ? ')' : ',');
    }
  }
  return out;
}

template<typename Y>
std::ostream& operator<<(std::ostream& out, const orang::Table<Y>& t) {
  out << "Table(vars:";
  BOOST_FOREACH( const TableVar& v, t.vars() ) {
    out << "<" << v.index << "," << v.domSize << "," << v.stepSize << ">";
  }
  out << " values=[";
  copy(t.begin(), t.end(), ostream_iterator<Y>(out, ","));
  out << "])";
  return out;
}


template<typename Y>
std::ostream& operator<<(std::ostream& out, const orang::MinSolution<Y>& s) {
  out << "MinSolution(value=" << s.value << " solution=[";
  copy(s.solution.begin(), s.solution.end(), ostream_iterator<Var>(out, ","));
  out << "])";
  return out;
}

template<typename Y>
std::ostream& operator<<(std::ostream& out, const orang::MinSolutionSet<Y>& s) {
  out << "MinSolutionSet(maxSolutions=" << s.maxSolutions() << " solutions=[";
  copy(s.solutions().begin(), s.solutions().end(), ostream_iterator<MinSolution<Y> >(out, ";"));
  out << "])";
  return out;
}

template std::ostream& operator<< <int>(std::ostream& out, const Table<int>& t);
template std::ostream& operator<< <int>(std::ostream& out, const orang::MinSolution<int>& s);
template std::ostream& operator<< <int>(std::ostream& out, const orang::MinSolutionSet<int>& s);

} // namespace orang

namespace tableAssign {
const VarsSentinel vars = VarsSentinel();
const DomSizesSentinel domSizes = DomSizesSentinel();
const ValuesSentinel values = ValuesSentinel();
const NullSentinel none = NullSentinel();
}
