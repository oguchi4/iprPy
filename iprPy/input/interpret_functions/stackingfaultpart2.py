# Standard Python libraries
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

# http://www.numpy.org/
import numpy as np

# https://github.com/usnistgov/atomman
import atomman as am

__all__ = ['stackingfaultpart2']

def stackingfaultpart2(input_dict, build=True, **kwargs):
    """
    Interprets calculation parameters associated with a stacking-fault record.
    This function should be called after iprPy.input.systemmanupulate.
    
    The input_dict keys used by this function (which can be renamed using the 
    function's keyword arguments):
    
    - **'stackingfault_faultpos'** the relative position within a unit cell
      where the stackingfault is to be placed.
    - **'stackingfault_shiftvector1'** one of the two fault shifting vectors
      as a crystallographic vector.
    - **'stackingfault_shiftvector2'** one of the two fault shifting vectors
      as a crystallographic vector.
    - **'sizemults'** the system size multipliers. Only accessed here.
    - **'ucell'** the unit cell system. Only accessed here.
    - **'axes'** the 3x3 matrix of axes. Only accessed here.
    - **'faultpos'** the absolute fault position relative to the initial
      system.
    - **'shiftvector1'** one of the two fault shifting vectors as a Cartesian
      vector.
    - **'shiftvector2'** one of the two fault shifting vectors as a Cartesian
      vector.
       
    Parameters
    ----------
    input_dict : dict
        Dictionary containing input parameter key-value pairs.
    stackingfault_faultpos : str
        Replacement parameter key name for 'stackingfault_faultpos'.
    stackingfault_shiftvector1 : str
        Replacement parameter key name for 'stackingfault_shiftvector1'.
    stackingfault_shiftvector2 : str
        Replacement parameter key name for 'stackingfault_shiftvector2'.
    sizemults : str
        Replacement parameter key name for 'sizemults'.
    ucell : str
        Replacement parameter key name for 'ucell'.
    axes : str
        Replacement parameter key name for 'axes'.
    faultpos : str
        Replacement parameter key name for 'faultpos'.
    shiftvector1 : str
        Replacement parameter key name for 'shiftvector1'.
    shiftvector2 : str
        Replacement parameter key name for 'shiftvector2'.
    """
    
    # Set default keynames
    keynames = ['stackingfault_faultpos', 'stackingfault_shiftvector1',
                'stackingfault_shiftvector2', 'stackingfault_cutboxvector',
                'sizemults', 'ucell', 'axes', 'faultpos', 'shiftvector1',
                'shiftvector2']
    for keyname in keynames:
        kwargs[keyname] = kwargs.get(keyname, keyname)
    
    if build is True:
        
        # Extract input values and assign default values
        stackingfault_faultpos = input_dict[kwargs['stackingfault_faultpos']]
        stackingfault_shiftvector1 = input_dict[kwargs['stackingfault_shiftvector1']]
        stackingfault_shiftvector2 = input_dict[kwargs['stackingfault_shiftvector2']]
        stackingfault_cutboxvector = input_dict[kwargs['stackingfault_cutboxvector']]
        sizemults = input_dict[kwargs['sizemults']]
        ucell = input_dict[kwargs['ucell']]
        axes = input_dict[kwargs['axes']]
        
        # Convert string terms to arrays
        stackingfault_shiftvector1 = np.array(stackingfault_shiftvector1.strip().split(),
                                              dtype=float)
        stackingfault_shiftvector2 = np.array(stackingfault_shiftvector2.strip().split(),
                                              dtype=float)
        
        # Convert crystallographic vectors to Cartesian vectors
        shiftvector1 = (stackingfault_shiftvector1[0] * ucell.box.avect +
                        stackingfault_shiftvector1[1] * ucell.box.bvect +
                        stackingfault_shiftvector1[2] * ucell.box.cvect)
        
        shiftvector2 = (stackingfault_shiftvector2[0] * ucell.box.avect +
                        stackingfault_shiftvector2[1] * ucell.box.bvect +
                        stackingfault_shiftvector2[2] * ucell.box.cvect)
        
        # Transform using axes
        T = am.tools.axes_check(axes)
        shiftvector1 = T.dot(shiftvector1)
        shiftvector2 = T.dot(shiftvector2)

        # Identify number of size multiples, m, along cutboxvector
        if   stackingfault_cutboxvector == 'a': 
            m = sizemults[0]
        elif stackingfault_cutboxvector == 'b': 
            m = sizemults[1]
        elif stackingfault_cutboxvector == 'c': 
            m = sizemults[2]
         
        if isinstance(m, (list, tuple)):
            m = m[1] - m[0]
        
        # For odd m, initial position of 0.5 goes to 0.5
        if m % 2 == 1:
            faultpos = (stackingfault_faultpos + (m-1) * 0.5) / m
        # For even m, initial position of 0.0 goes to 0.5
        else:
            faultpos = (2 * stackingfault_faultpos + m) / (2 * m)
    
    else:
        faultpos = None
        shiftvector1 = None
        shiftvector2 = None
    
    # Save processed terms
    input_dict[kwargs['faultpos']] = faultpos
    input_dict[kwargs['shiftvector1']] = shiftvector1
    input_dict[kwargs['shiftvector2']] = shiftvector2