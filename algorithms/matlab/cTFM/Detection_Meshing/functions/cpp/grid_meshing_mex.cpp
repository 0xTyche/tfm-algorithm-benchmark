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

  if (nrhs != 3)
  {
    mexErrMsgIdAndTxt("MATLAB:mexcpp:nargin",
        "grid_meshing_mex requires 3 input arguments, V_boundary, V_internal, neigh");
  }


  State s;
  igl::matlab::parse_rhs_double(&prhs[0],s.V_boundary);
  igl::matlab::parse_rhs_double(&prhs[1],s.V_internal);
  MatrixXd temp;
  igl::matlab::parse_rhs_double(&prhs[2],temp);
  s.neigh = temp.cast<int>();

  // std::cerr << "s.V_boundary" << std::endl << s.V_boundary << std::endl << std::endl;
  // std::cerr << "s.V_internal" << std::endl << s.V_internal << std::endl << std::endl;
  // std::cerr << "s.neigh" << std::endl << s.neigh << std::endl << std::endl;

  try
  {
    s.create_initial_triangulation();
    s.fit_triangulation();
  }
  catch(...)
  {
    std::cerr << "Input invalid" << std::endl;
  }

  // Return the matrices to matlab
  switch(nlhs)
  {
    case 2:
      igl::matlab::prepare_lhs_index(s.F,plhs+1);
    case 1:
      igl::matlab::prepare_lhs_double(s.V,plhs);
    default: break;
  }

  return;
}
