from query import query_on_seeds, query_on_primitive


class ModifyGenerator:
    """ Generator to be used for creating modified pipelines based on existing
        pipelines in the database
    """
    def __init__(self, modify_type: str='random-seed', max_jobs: int=None, *args):
        self.args = args
        #intialize commonly used variables
        self.modifier_type = modify_type
        self.max_jobs = max_jobs
        self.num_complete = 0
        #run the query on initializing to define the query results
        self.query_results = self._query(self.modifier_type, self.args)


    def __next__(self):
        #iterate through query results
        for query_result in self.query_results:
            #iterate through modifier results
            for job in self._modify(query_result, self.args):
                self.num_complete += 1
                #check to run until the generator stops iterating (if no input for num_pipelines_to_run)
                if (self.max_jobs):
                    if (self.num_complete >= self.max_jobs):
                        raise StopIteration
                return job
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
    
            
    def _modify(self, query_args: dict, *args):
        if self.modifier_type=='random-seed':
            return self._modify_random_seed(args.seed_limit, query_args)
        if self.modifier_type=='swap-primitive':
            return self._modifiy_swap_primitive(args.pipeline, args.primitive_loc, args.new_primitive)
        else:
            raise ValueError("This type of modification is not yet an option")
    
    
    def _modify_random_seed(self, seed_limit, query_args):
        used_seeds = query_args.tested_seeds
        num_run = len(used_seeds)
        #run until the right number of seeds have been run
        while (num_run < seed_limit):
            new_seed = randint(1,100000)
            if (new_seed in used_seeds):
                continue
            num_run += 1
            used_seeds.append(new_seed)
            #yield the necessary job requirements
            yield query_args.pipeline, query_args.problem_ref, new_seed
        
