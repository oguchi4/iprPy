# Standard Python libraries
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

# https://github.com/usnistgov/DataModelDict 
from DataModelDict import DataModelDict as DM

# iprPy imports
from ...compatibility import range
from .interatomicpotential import interatomicpotential

__all__ = ['atomicparent']

def atomicparent(database, keys, record=None, load_key='atomic-system',
                 query=None, **kwargs):
    
    # Get potentials
    if 'potential_file' in keys:
        potential_kwargs = {}
        for key in list(kwargs.keys()):
            if key[:10] == 'potential_':
                potential_kwargs[key[10:]] = kwargs.pop(key)
        
        pot_inputs = interatomicpotential(database, **potential_kwargs)
        
        potentials = {}
        for i in range(len(pot_inputs['potential_dir'])):
            potentials[pot_inputs['potential_dir'][i]] = pot_inputs['potential_content'][i]
    
    parents, parent_df = database.get_records(style=record, return_df=True,
                                           query=query, **kwargs)
    
    inputs = {}
    for key in keys:
        inputs[key] = []
    
    for i, parent_info in parent_df.iterrows():
        parent = parents[i]
        
        nparents = len(DM(parent.content).finds(load_key))
        
        if nparents == 0:
            if parent_info.status == 'error':
                continue
            nparents = 1
        
        # Add parent info containing system_model information
        for j in range(nparents):
            if j == 0:
                load_options = 'key ' + load_key
            else:
                load_options = 'key ' + load_key + ' index ' + str(j)
            
            for key in keys:
                if key == 'potential_file':
                    potential_name = parent_info.potential_LAMMPS_id
                    inputs['potential_file'].append(potential_name + '.json')
                elif key == 'potential_content':
                    potential_name = parent_info.potential_LAMMPS_id
                    potential_content = potentials[potential_name]
                    inputs['potential_content'].append(potential_content)
                elif key == 'potential_dir':
                    potential_name = parent_info.potential_LAMMPS_id
                    inputs['potential_dir'].append(potential_name)
                elif key == 'load_file':
                    inputs['load_file'].append(parent.name + '.json')
                elif key == 'load_content':
                    inputs['load_content'].append('record ' + parent.name)
                elif key == 'load_style':
                    inputs['load_style'].append('system_model')
                elif key == 'load_options':
                    inputs['load_options'].append(load_options)
                elif key == 'family':
                    inputs['family'].append(parent_info.family)
                else:
                    inputs[key].append('')
    return inputs