#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 16:37:58 2020

@author: sarashs
This is the reax forcefield simulated annealing class. The energy functions and data types are defined per reax forcefield.

    Attributes
    --------------
    structure_energies : dict of dict
        energy calculated per annealer (forcefield) per structure file.
        [forcefield_name][structure_name] = energy
    structure_charges : dict of dict
        charge calculated per annealer (forcefield) per structure file.
"""
from REAX_FF import REAX_FF 
from copy import deepcopy
from LAMMPS_Utils import lammps_input_creator
from lammps import lammps
#from mpi4py import MPI
from SA import SA
import random
#import time

class SA_REAX_FF(SA):
    def __init__(self,forcefield_path, output_path, params_path, Training_file, Input_structure_file, T=1, T_min=0.00001, Temperature_decreasing_factor=0.1, max_iter=50, number_of_points=1):
        super().__init__(forcefield_path, output_path, params_path, Training_file, Input_structure_file, T, T_min, Temperature_decreasing_factor, max_iter, number_of_points)
        self.single_best_solution = None
        # Initial forcefield (initial annealer(s))
        temp_init = REAX_FF(forcefield_path,params_path)
        temp_init.parseParamSelectionFile()
        self.structure_charges = {} 
        forcefield_name = "annealer_" + str(0) + ".reax"
        self.sol_[forcefield_name] = deepcopy(temp_init)
        self.sol_[forcefield_name].ff_filePath = self.general_path + forcefield_name
        self.sol_[forcefield_name].write_forcefield(self.general_path + forcefield_name)
        self.lammps_file_list = {} #dictionary keys: forcefield tag, values: list of lammps files
        self.lammps_file_list[forcefield_name] = lammps_input_creator(self.Input_structure_file, forcefield_name, 'reax', self.general_path)
        self.structure_energies[forcefield_name] = {} 
        self.structure_charges[forcefield_name] = {} 
        for i in range(1, number_of_points):
            forcefield_name = "anenaler_" + str(i) + ".reax"
            self.sol_[forcefield_name] = deepcopy(temp_init)
            self.sol_[forcefield_name].ff_filePath = self.general_path + forcefield_name
            self.input_generator(forcefield_name, update = "YES")
            self.structure_energies[forcefield_name] = {}
            self.structure_charges[forcefield_name] = {} 
    def input_generator(self, forcefield_name, update = "YES"):
        """Generates the next solution.

        Returns
        -------
        self : object

        """
        if "YES" in update:
            # generate values for selected params
            for param_tuple in self.sol_[forcefield_name].param_min_max_delta.keys():
                while True:
                    self.sol_[forcefield_name].params[param_tuple[0]][param_tuple[1]][param_tuple[2]] = round(self.sol_[forcefield_name].params[param_tuple[0]][param_tuple[1]][param_tuple[2]] + random.uniform(-1, 1) * self.sol_[forcefield_name].param_min_max_delta[param_tuple]['delta'], 5)
                    if self.sol_[forcefield_name].params[param_tuple[0]][param_tuple[1]][param_tuple[2]] >= self.sol_[forcefield_name].param_min_max_delta[param_tuple]['min'] and self.sol_[forcefield_name].params[param_tuple[0]][param_tuple[1]][param_tuple[2]] <= self.sol_[forcefield_name].param_min_max_delta[param_tuple]['max']:
                        break
            ####
            # save the new forcefield file
            self.sol_[forcefield_name].write_forcefield(self.general_path + forcefield_name)
            # I think these two neet to be removed
            #self._Input_data_file_list = list_of_structures(self.Input_structure_file)
            #self.Training_data = Training_data(self.Training_file)
        elif "NO" in update:
            pass
        else:
            raise ValueError("update value for inpute_generator takes YES or NO only!")
        # use the same name for the input structure file
        self.lammps_file_list[forcefield_name] = lammps_input_creator(self.Input_structure_file, forcefield_name, 'reax', self.general_path)
    def __Individual_Energy(self, parallel = "NO"):
        """
        Computes the Energy for ALL of the annealers and for ALL input file
        This is a private method that is called by objective function calculator
        :return: 
        --------
        self : object
        
        """
#####Running lammps and python in serial        
        if "NO" in parallel:
            for item in self.sol_.keys():
                for a_file in self.lammps_file_list[item]:
                    lmp = lammps()
                    lmp.file(self.general_path + a_file)
                    self.structure_energies[item][a_file] = round(lmp.get_thermo("etotal"), 5)
                    #pe = lmp.get_thermo("pe")
                    lmp.close()
        elif "YES" in parallel:
            pass
        else:
            raise ValueError("parallel value for __Individual_Energy takes YES or NO only!")
    def cost_function(self):
        """Computes the cost function.
        Returns
        -------
        self : object
        
        """
        # decide whether or not to do the charge based on self.training_charge_weight= 0
        for item in self.sol_.keys():
            ##### Cost calculation: For now mean square
            ##### Computing energy
            self.cost_[item] = self.Training_info.training_energy_weight * sum([trainee[0] * (trainee[1] * self.structure_energies[item][trainee[2] + '.dat']+ trainee[3] * self.structure_energies[item][trainee[4] + '.dat'] - trainee[5]) ** 2 for trainee in self.Training_info.training_energy])
            ##### Computing charge 
    def anneal(self, record_costs = "NO"):
        #Automatic temperature rate control initialize
        tmp_ctrl_step = 0
        total_accept = 0
        accept_rate = 0
        ###
        self.__Individual_Energy(parallel = "NO")
        self.cost_function()
        current_sol = deepcopy(self.sol_)
        cost_old = deepcopy(self.cost_)
        if "YES" in record_costs:
            self.costs.append({temp_key:cost_old[temp_key] for temp_key in cost_old.keys()})
        while self.T > self.T_min:
            i = 1
            while i <= self.max_iter:
                for item in self.sol_.keys():
                    self.input_generator(item, update = "YES")
                self.__Individual_Energy(parallel = "NO")
                self.cost_function()
                cost_new = deepcopy(self.cost_)
                ap = self.accept_prob(cost_old, cost_new)
                # counting the total number of steps for all of the annealers
                tmp_ctrl_step += 1
                for item in self.sol_.keys():
                    if ap[item] > random.random():
                        current_sol[item] = deepcopy(self.sol_[item])
                        cost_old[item] = deepcopy(cost_new[item])
                        # counting total acceptance
                        total_accept += 1
                        #
                    else:
                        self.cost_[item] = deepcopy(cost_old[item])
                        self.sol_[item] = deepcopy(current_sol[item])
                #  check the acceptance rates at every 100 steps
                if tmp_ctrl_step == 100:
                    accept_rate = total_accept / (self.number_of_points)
                    tmp_ctrl_step = 0
                    total_accept = 0
                    if accept_rate > 70:
                        self.alpha *= 1.2
#                    elif accept_rate < 1:
#                        self.alpha /= 1.1
                i += 1
                ## debug
                print(self.T, total_accept)
                ##
                if "YES" in record_costs:
                    self.costs.append({temp_key:cost_old[temp_key] for temp_key in cost_old.keys()})
            self.T = self.T * (1 - self.alpha)
        ### writing the best output
        self.single_best_solution = self.sol_[min(self.cost_, key = self.cost_.get)]
        self.single_best_solution.write_forcefield(self.general_path+"bestFF.reax")
        ###clean up
        for item in self.sol_.keys():
            names_to_be_deleted = []
            for item2 in self.lammps_file_list[item]:
                names_to_be_deleted.append(item2[:-4])
                names_to_be_deleted.append(item[:])
            self.clean_the_mess(names_to_be_deleted)
        ####