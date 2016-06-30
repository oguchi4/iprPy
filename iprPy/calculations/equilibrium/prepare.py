import os
import shutil
import sys
import glob
import uuid

from DataModelDict import DataModelDict as DM
import atomman.lammps as lmp
import atomman as am

from iprPy.tools import fill_template, atomman_input, term_extractor
from .data_model import data_model
from .read_input import read_input

#Automatically identify the calculation's directory and name
__calc_dir__ = os.path.dirname(os.path.realpath(__file__))   
__calc_type__ =  os.path.basename(__calc_dir__)
__calc_name__ = 'calc_' + __calc_type__

def prepare(terms, variable):
    """This is the prepare method for the calculation"""
    
    working_dir = os.getcwd()
    
    #Read in the calc_template 
    calc_template = __calc_name__ + '.template'
    with open(os.path.join(__calc_dir__, 'calc_files', calc_template)) as f:
        template = f.read()
    
    #Identify the contents of calc_files
    calc_files = os.listdir(os.path.join(__calc_dir__, 'calc_files'))
    calc_files.remove(calc_template)  

    #Interpret and check terms and variables
    run_directory, lib_directory, v_dict = __initial_setup(terms, variable)
    
    #Loop over all potentials
    for potential_file, potential_dir in zip(variable.aslist('potential_file'), 
                                             variable.aslist('potential_dir')):
        
        #Load potential
        with open(potential_file) as f:
            potential = lmp.Potential(f)

        #Pass potential's file and directory info to v_dict
        v_dict['potential_file'] = os.path.basename(potential_file)
        v_dict['potential_dir'] = os.path.basename(potential_dir)
        
        #Loop over all systems
        for load, load_options, load_elements, box_parameters in zip(variable.aslist('load'), 
                                                                     variable.aslist('load_options'),
                                                                     variable.aslist('load_elements'), 
                                                                     variable.aslist('box_parameters')):
            
            #Divy up the load information
            load_terms = load.split()
            load_style = load_terms[0]
            load_file = ' '.join(load_terms[1:])
            load_base = os.path.basename(load_file)

            #Check for system_model fields from previous simulations
            if load_style == 'system_model':
                with open(load_file) as f:
                    model = DM(f)
                try:
                    system_family = model.find('system-info')['artifact']['family']
                except:
                    system_family = os.path.splitext(load_base)[0]
            else:
                system_family = os.path.splitext(load_base)[0]

            #Pass system's file, options and box parameters to v_dict
            v_dict['load'] = ' '.join([load_terms[0], load_base])
            v_dict['load_options'] = load_options
            v_dict['box_parameters'] = box_parameters

            #Loop over all symbols combinations
            for symbols in atomman_input.yield_symbols(load, load_options, load_elements, variable, potential):
                
                #Pass symbols to v_dict
                v_dict['symbols'] = ' '.join(symbols)

                #Define directory path for the record
                record_dir = os.path.join(lib_directory, str(potential), '-'.join(symbols), system_family, __calc_type__)
                
                for thermo_steps, dump_every, run_steps in zip(variable.aslist('thermo_steps'), 
                                                               variable.aslist('dump_every'),
                                                               variable.aslist('run_steps')):
                    v_dict['thermo_steps'] = thermo_steps
                    v_dict['dump_every'] = dump_every
                    v_dict['run_steps'] = run_steps
                    
                    for pressure in variable.aslist('pressure'):
                        v_dict['pressure'] = pressure
                        
                        for temperature in variable.aslist('temperature'):
                            v_dict['temperature'] = temperature
                
                            for size_mults in variable.aslist('size_mults'):
                                v_dict['size_mults'] = size_mults
                                
                                for random_seed in variable.aslist('random_seed'):
                                    v_dict['random_seed'] = random_seed
                                    
                                    #Check if record already exists
                                    if __is_new_record(record_dir, v_dict):
                                        UUID = str(uuid.uuid4())
                                        
                                        #Create calculation run folder
                                        sim_dir = os.path.join(run_directory, UUID)
                                        os.makedirs(sim_dir)
                                        
                                        #Copy files to run folder
                                        for fname in calc_files:
                                            shutil.copy(os.path.join(__calc_dir__, 'calc_files', fname), sim_dir)
                                        shutil.copy(potential_file, sim_dir)
                                        shutil.copy(load_file, sim_dir)
                                        
                                        #Copy potential_dir and contents to run folder
                                        os.mkdir(os.path.join(sim_dir, os.path.basename(potential_dir)))
                                        for fname in glob.iglob(os.path.join(potential_dir, '*')):
                                            shutil.copy(fname, os.path.join(sim_dir, os.path.basename(potential_dir)))
                                        
                                        #Create calculation input file by filling in template with v_dict terms
                                        os.chdir(sim_dir)
                                        calc_in = fill_template(template, v_dict, '<', '>')
                                        input_dict = read_input(calc_in, UUID)
                                        with open(__calc_name__ + '.in', 'w') as f:
                                            f.write('\n'.join(calc_in))
                                        os.chdir(working_dir)                                        
                                        
                                        #Save the incomplete record
                                        model = data_model(input_dict)
                                        with open(os.path.join(record_dir, UUID + '.json'), 'w') as f:
                                            model.json(fp=f, indent=2)
                    
                    
                    
def __initial_setup(t, v):
    """
    Pulls out the singular values in terms, t, and variables, v.
    Asserts that multi-valued variables are of appropriate lengths.
    """
    
    v_dict = DM()
    
    #read in run and library directory information
    run_directory = atomman_input.get_value(v, 'run_directory')
    lib_directory = atomman_input.get_value(v, 'lib_directory')
    
    #read in the simulation-dependent singular valued variables
    v_dict['lammps_command'] = atomman_input.get_value(v, 'lammps_command')
    v_dict['mpi_command'] =    atomman_input.get_value(v, 'mpi_command', '')
       
    v_dict['length_unit'] =    atomman_input.get_value(v, 'length_unit',   '')
    v_dict['pressure_unit'] =  atomman_input.get_value(v, 'pressure_unit', '')
    v_dict['energy_unit'] =    atomman_input.get_value(v, 'energy_unit',   '')
    v_dict['force_unit'] =     atomman_input.get_value(v, 'force_unit',    '')
       
    #Check lengths of the multi-valued variables
    assert len(v.aslist('potential_file')) == len(v.aslist('potential_dir')), 'potential_file and potential_dir must be of the same length'
    assert len(v.aslist('load')) == len(v.aslist('load_options')), 'load and load_options must be of the same length'
    assert len(v.aslist('load')) == len(v.aslist('load_elements')), 'load and load_elements must be of the same length'
    assert len(v.aslist('load')) == len(v.aslist('box_parameters')), 'load and box_parameters must be of the same length'
    assert len(v.aslist('thermo_steps')) == len(v.aslist('dump_every')), 'thermo_steps and dump_every must be of the same length' 
    assert len(v.aslist('thermo_steps')) == len(v.aslist('run_steps')), 'thermo_steps and run_steps must be of the same length'
    
    #Check that other variables are of at least length 1
    if len(v.aslist('size_mults')) == 0:
        v['size_mults'] = '1 1 1'  
    if len(v.aslist('pressure')) == 0:
        v['pressure'] = 0.0
    if len(v.aslist('temperature')) == 0:
        v['temperature'] = 100.0  
    if len(v.aslist('random_seed')) == 0:
        v['random_seed'] = 1734812
       
    #Read in terms
    #NO TERMS DEFINED FOR THIS CALCULATION
    #t = term_extractor(t, [])
    #v_dict[] = atomman_input.get_value(t, '', '')
            
    return run_directory, lib_directory, v_dict
    
def __is_new_record(record_dir, v_dict):
    """Check if a matching record already exists."""
    try:
        flist = os.listdir(record_dir) 
    except:
        os.makedirs(record_dir) 
        return True

    is_new = True
    for fname in flist:
        if os.path.splitext(fname)[1] in ['.xml', '.json']:
            with open(os.path.join(record_dir, fname)) as f:
                record = DM(f)
           
            sys_file = record.find('system-info')['artifact']['file']
            
            load_file = ' '.join(v_dict['load'].split()[1:])
            if sys_file != load_file:
                continue
            
            run_parameters = record.find('run-parameter')
            
            if int(run_parameters['thermo_steps']) != int(v_dict['thermo_steps']):
                continue
            if float(run_parameters['pressure']) != float(v_dict['pressure']):
                continue
            if int(run_parameters['run_steps']) != int(v_dict['run_steps']):
                continue
            if int(run_parameters['random_seed']) != int(v_dict['random_seed']):
                continue
            if float(run_parameters['temperature']) != float(v_dict['temperature']):
                continue
                
            a_mult = run_parameters['a-multiplyer']
            b_mult = run_parameters['b-multiplyer']
            c_mult = run_parameters['c-multiplyer']
            
            mults = v_dict['size_mults'].split()
            if len(mults) == 3:
                a_m = abs(int(mults[0]))
                b_m = abs(int(mults[1]))
                c_m = abs(int(mults[2]))
            elif len(mults) == 6:
                a_m = int(mults[1]) - int(mults[0])
                b_m = int(mults[3]) - int(mults[2])
                c_m = int(mults[5]) - int(mults[4])
            else:
                raise ValueError('Invalid size_mults term')
                
            if (a_m, b_m, c_m) == (a_mult, b_mult, c_mult):
                is_new = False
                break
        
    return is_new    