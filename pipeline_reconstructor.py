import json
import pandas as pd
import numpy as np
import re
import networkx as nx
import matplotlib.pyplot as plt
import copy

#===================================================
#TODO
#update the outputs for the entire pipeline (pipeline['outputs'])
#make sure no preceding inputs point towards the one that is being removed (can they be added that way?)
#===================================================


class PipelineReconstructor():
    """ Class for editing given pipeline at initialization, will include methods
        that can swap, add, and remove primitives, as well as edit hyperparameters 
        and generate all possible linear paths within the pipeline
    """

    def __init__(self, pipeline=None, draw=False):
        #if pipeline is a JSON file and not a json object
        #self.pipeline = self.read_json_to_dict(pipeline)
        self.pipeline = pipeline
        self.draw = draw
        self.pipeline_dict = self.construct_linked_dictionary(self.pipeline, draw=self.draw)
        
    def to_directed_graph(self, to_di):
        g = nx.DiGraph()
        for i in to_di.keys():
            for j in to_di[i]:
                g.add_edge(i,j)
        self.di_graph = g
        return g
        
    def draw_inputs(self, to_draw):
        graph = self.to_directed_graph(to_draw)
        nx.draw(graph, with_labels=True)
        plt.draw()
        plt.show()

    def construct_linked_dictionary(self, pipeline, draw=False):
        #constructs linked list according to the structure of the passed pipeline and step indices
        step_dict = dict()
        #get the list of steps from the pipeline
        steps = pipeline['steps']
        for it, i in enumerate(steps):
            for key, value in i['arguments'].items():
                if (key not in step_dict.keys()):
                    step_dict[key] = dict()
                #get the steps used for inputs
                types, num = re.findall(r"([a-z]*).([0-9])", i['arguments'][key]['data'])[0]
                num = int(num)
                if (types == "inputs"):
                    num = "pipe-in"
                else:
                    num = num    
                if (num not in step_dict[key]):
                    step_dict[key][num] = list()
                step_dict[key][num].append(it)
        if (draw is True):
            self.draw_inputs(step_dict['inputs'])
        return step_dict
          
    def get_num_steps(self):
        return len(self.pipeline['steps'])
    
    def read_json_to_dict(self, filename):
        with open(filename, 'r') as data_file:
            data = data_file.read()
        #now convert to dictionary
        pipeline_dict = json.loads(data)
        return pipeline_dict
        
    def add_attributes(self, loc, prim_edit, hyperparams=None, copy_params=True):
        """Add attributes to the new primitive according the original ones attributes
        """    
        prim_dict = dict()
        prim_dict['type'] = "PRIMITIVE"
        prim_dict['primitive'] = prim_edit
        for key, value in self.pipeline["steps"][loc].items():
            if (key == 'type'):
                prim_dict = prim_dict
            elif (key == 'primitive'):
                prim_dict = prim_dict
            else:
                prim_dict[key] = value
        #hyperparameter options
        if (hyperparams is None and copy_params is True):
            prim_dict['hyperparams'] = prim_dict['hyperparams']
        elif (hyperparams is None and copy_params is False):
            prim_dict.pop('hyperparams',None)
        else:
            prim_dict['hyperparams'] = hyperparams
        return prim_dict
    
    def replace_at_loc(self, loc, prim_edit, hyperparams=None, draw_new=False):
        """swap out the primitive step with another at a certain location
        """
        if (loc > self.get_num_steps()):
            raise ValueError("Location to add pipeline is outside number of steps") 
        #create the new primitive dictionary    
        prim_dict = self.add_attributes(loc, prim_edit, hyperparams)
        #now do the swapping, outputs and inputs should remain the same as what pipeline was declared
        new_pipeline =  copy.deepcopy(self.pipeline)
        new_pipeline['steps'][loc] = prim_dict
        if (draw_new is True):
            new_linked_dict = self.construct_linked_dictionary(new_pipeline, draw=True)
                
        #return the new json
        return json.dumps(new_pipeline)
        
    def add_at_loc(self, loc, prim_edit, hyperparams=None, draw_new=False):
        """This method only works in the linear case, because we linearly push everything back
           when we get the input primitive and location to push at
        """ 
        #create the new primitive dictionary
        prim_dict = self.add_attributes(loc, prim_edit, hyperparams=None)    
        new_pipeline = self.pipeline.copy()    
        #insert the pipeline at the new place   
        new_pipeline['steps'] = new_pipeline['steps'].insert(loc, prim_dict)
        #now loop through the original steps and update the inputs accordingly
        for key, value in self.pipeline_dict.items():
            for k, v in self.pipeline_dict[key].items():
                if (k == 'pipe_in'):
                    if (loc == 0):
                        print("trouble!")
                else:
                    for link in v:
                        ###################NOT CORRECT!!!!!!!!!###############################
                        if (link > loc and k >= loc):
                            new_piplines['steps'][link]['arguments'][key]['data']= 'steps.{}.produce'.format(k+1)
                        
            
        #return the new json
        return json.dumps(new_pipeline)
        
    def remove_at_loc(self, loc, prim_edit):
        """This method works in the linear case, because removing an attribute will cause all after
           location to shift backwards
        """
        #this will require more work, such as checking outputs and inputs, to make sure it works
        del new_pipeline['steps'][loc]
        #update the inputs from the remaining steps to work with the removal
        for i in range(loc, self.get_num_steps()):
            step_string = self.pipeline['steps'][i]['arguments']['inputs']['data']
            step_num = int(step_string[6])
            print(step_num)
            #now change the origin location inputs if it was affected by the shift
            if (step_num <= loc):
                new_pipeline['steps'][i]['arguments']['inputs']['data'] = "steps.{}.produce".format(step_num-1)
        return json.dumps(new_pipeline)
        
    
    #def edit_hyper_params(self,):
    
    #def gen_possible_paths(self,):
