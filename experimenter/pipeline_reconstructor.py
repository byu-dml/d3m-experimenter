import json
import pandas as pd
import numpy as np
import re
import networkx as nx
import matplotlib.pyplot as plt
import copy
from d3m import index
from d3m.metadata.base import ArgumentType
from d3m.metadata.pipeline import Pipeline, PrimitiveStep

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
    
    def update_steps(self, key, pipe_copy, python_path, loc, new_pipeline_description, hyperparams):
        step_list = list()
        #add steps to the new pipeline including the substition step
        for it, i in enumerate(pipe_copy['steps']):
            if (it == loc):
                step = PrimitiveStep(primitive=index.get_primitive(python_path))
            else:
                step = PrimitiveStep(primitive=index.get_primitive(pipe_copy['steps'][it]['primitive']['python_path']))
            for key, value in pipe_copy['steps'][it].items():
                if (key == 'arguments'):
                    for k, v in pipe_copy['steps'][it][key].items():
                        step.add_argument(name=k, argument_type=ArgumentType.CONTAINER, data_reference=pipe_copy['steps'][it][key][k]['data'])
                if (key == 'outputs'):
                    for iterA, j in enumerate(pipe_copy['steps'][it][key]):
                        step.add_output(pipe_copy['steps'][it][key][iterA]['id'])                 
                if (key == 'hyperparams'):
                    if (it == loc):
                        if (hyperparams is not None):
                            for param in hyperparams:
                                step.add_hyperparameter(name=param['name'], data=param['data'], argument_type=ArgumentType.VALUE)
                    else:
                        for name, dictionary in pipe_copy['steps'][it][key].items():
                            step.add_hyperparameter(name=name, data=pipe_copy['steps'][it][key][name]['data'],  argument_type=ArgumentType.VALUE)
            step_list.append(step)
        return step_list
                
    def replace_at_loc(self, loc, prim_edit, hyperparams=None, draw_new=False):
        """swap out the primitive step with another at a certain location
        """
        python_path = prim_edit['python_path']
        if (loc > self.get_num_steps()):
            raise ValueError("Location to add pipeline is outside number of steps") 
        pipe_copy = copy.deepcopy(self.pipeline)    
        #create the new pipeline dictionary 
        new_pipeline_description = Pipeline()
        #now use the same inputs and outputs in the higher level of the new_pipeline
        for keys, values in pipe_copy.items():
            if (keys == 'inputs'):
                for it, i in enumerate(pipe_copy['inputs']):
                    new_pipeline_description.add_input(name=pipe_copy['inputs'][it]['name'])                       
            if (keys == 'steps'):
                step_list = self.update_steps(keys, pipe_copy, python_path, loc, new_pipeline_description, hyperparams)
                for step in step_list:
                    new_pipeline_description.add_step(step)
        for it, i in enumerate(pipe_copy['outputs']):
            new_pipeline_description.add_output(name=pipe_copy['outputs'][it]['name'], data_reference=pipe_copy['outputs'][it]['data'])
        #validation by changing to json
        new_pipeline = new_pipeline_description.to_json(indent=4)
        #draw the new linked list if desired from the given pipeline
        if (draw_new is True):
            new_linked_dict = self.construct_linked_dictionary(new_pipeline, draw=True)
                
        #return the new json
        return new_pipeline
        
    #def add_at_loc(self, loc, prim_edit, hyperparams=None, draw_new=False):
    #def remove_at_loc(self, loc, prim_edit):
    #def edit_hyper_params(self,):
    #def gen_possible_paths(self,):
