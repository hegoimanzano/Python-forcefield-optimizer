import re

class Training_data(object):
    """
    At this point only charge and Energy training are implemented
    TO DO:
        -complete the energy and charge training parameters prepration
    """
# This would be a list like: self.training_energy=[[Weight,Coefficient,name_string,Coefficient,name_string,Energy_number],[],...]
    def __init__(self, train_data_filepath):
        self.training_charge= []
        self.training_energy= []
        self.training_charge_weight= 0
        self.training_energy_weight= 0
        try:
            temp_file=open(train_data_filepath,"r")
            temp_list=temp_file.readlines()
            Energy_pattern=re.compile(r'ENERGY')
            charge_pattern=re.compile(r'CHARGE')
            Energy_flag=False
            charge_flag=False
            for line_item in temp_list:
                if Energy_pattern.search(line_item):
                    Energy_flag=True
                    charge_flag=False
                    self.training_energy_weight=float(re.findall(r'[-+]?\d*\.\d+|\d+',line_item)[0])
                    continue
                if charge_pattern.search(line_item):
                    Energy_flag=False
                    charge_flag=True
                    self.training_charge_weight=float(re.findall(r'[-+]?\d*\.\d+|\d+',line_item)[0])
                    continue
                if (Energy_flag and not(charge_flag)):
                    if re.findall(r'[-+]?\d*\.\d+|\d+',line_item):
                        begining_of_first_string=re.search('\*',line_item).span()[0]+1
                        end_of_first_string=re.search('\s',line_item[begining_of_first_string:]).span()[0]+begining_of_first_string
                        begining_of_second_string=re.search('\*',line_item[end_of_first_string:]).span()[0]+1+end_of_first_string
                        end_of_second_string=re.search('\s',line_item[begining_of_second_string:]).span()[0]+begining_of_second_string #r'[-+]?\d*\.\d+|\d+'
                        self.training_energy.append([float(re.findall('-?\d+\.?\d*',line_item)[0]),float(re.findall('-?\d+\.?\d*',line_item)[1]),line_item[begining_of_first_string:end_of_first_string],float(re.findall('-?\d+\.?\d*',line_item[end_of_first_string+1:])[0]),line_item[begining_of_second_string:end_of_second_string],float(re.findall('-?\d+\.?\d*',line_item[end_of_second_string+1:])[0])])
                elif (charge_flag and not(Energy_flag)):
                    if re.findall(r'[-+]?\d*\.\d+|\d+',line_item):
                        pass
        except IOError:
            print('An error occured trying to read the training data file.')
