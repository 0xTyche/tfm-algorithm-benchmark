#include "mex.h"

#include <igl/readOBJ.h>
#include <igl/matlab/prepare_lhs.h>
#include <igl/matlab/parse_rhs.h>
#include <Eigen/Core>
#include "src/state.h"


void mexFunction(
     int          nlhs,
     mxArray      *plhs[],
     int          nrhs,
     const mxArray *prhs[]
     )
{
  using namespace Eigen;
  /* Check for proper number of arguments */

  if (nrhs != 1)
  {
    mexErrMsgIdAndTxt("MATLAB:mexcpp:nargin",
        "is_neigh_valid_mex requires 1 input argument: neigh");
  }


  State s;
  MatrixXd temp;
  igl::matlab::parse_rhs_double(&prhs[0],temp);
  s.neigh = temp.cast<int>();

  //std::cerr << "s.neigh" << std::endl << s.neigh << std::endl << std::endl;

  MatrixXd ret(1,1);

  MatrixXi tempi = s.find_pairs_by_tracing(s.neigh);
  if (tempi.size() != 0)
    ret(0,0) = 1;
  else
    ret(0,0) = 0;

  // Return the matrices to matlab
  switch(nlhs)
  {
    case 1:
      igl::matlab::prepare_lhs_double(ret,plhs);
    default: break;
  }

  return;
}
