from query import query_on_seeds, query_on_primitive


class ModifyGenerator:
    """ Generator to be used for creating modified pipelines based on existing
        pipelines in the database
    """
    def __init__(self, *args):
        self.args = args
        #intialize commonly used variables
        self.modifier_type = args.modifier_type
        self.num_pipelines_to_run = args.num_pipelines_to_run
        self.num_complete = 0
        #run the query on initializing to define the query results
        self.query_results = self._query(self.modifier_type, self.args)

    def __next__(self):
        #iterate through query results
        for query_result in self.query_results:
            pipeline, dataset, pipeline_run = query_result
            #iterate through modifier results
            for new_pipeline, dataset in self._modify(self.args):
                self.num_complete += 1
                #check to run until the generator stops iterating (if no input for num_pipelines_to_run)
                if (self.num_pipelines_to_run):
                    if (self.num_complete >= self.num_pipelines_to_run):
                        raise StopIteration
                return (new_pipeline, new_dataset)
        raise StopIteration

    def __iter__(self):
        return self
            
    def _query(self, *args):
        if (self.modifier_type=='random-seed'):
            return query_on_seeds(args.pipeline_id, args.seed_limit, args.submitter):
        if (self.modifier_type=='swap-primitive'):
            return query_on_primitive(args.primitive_id, args.limit_indeces)
        else:
            raise ValueError("This type of modification is not yet an option")
            
    def _modify(self,*args):
        if self.modifier_type=='random-seed':
            self._modify_random_seed(args.random_seed, args.seed_limit)
        if self.modifier_type=='swap-primitive':
            self._modifiy_swap_primitive(args.pipeline, args.primitive_loc, args.new_primitive)
        else:
            raise ValueError("This type of modification is not yet an option")
    
    def _modify_random_seed(self, pipeline, dataset, args):
        ##======== Create the random seed modifier
        #yield random seeds and the pipeline/dataset to run on
