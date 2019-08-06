import os, sys, json, subprocess, time, threading
import pandas as pd 
from d3mds import D3MDataset, D3MProblem, D3MDS
import networkx as nx
from sklearn.metrics import accuracy_score
from collections import OrderedDict

here = os.path.dirname(os.path.abspath(__file__))
dspath = os.path.join(here, '..', '..', '49_facebook_dataset')
prpath = os.path.join(here, '..', '..', '49_facebook_problem')
solpath = os.path.join(here, '..')
graphpath = os.path.join(dspath, 'graphs')
assert os.path.exists(dspath)
assert os.path.exists(prpath)

d3mds = D3MDS(dspath, prpath) # this checks that the problem and dataset correspond

NETAL_CONFIG = {'a':0,'b':0,'c':1, 'i':10}

def run_subProcess(cmd):
	# print(cmd)
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	out, err = p.communicate() 
	result = out.decode("utf-8").split('\n')
	for lin in result:
		if not lin.startswith('#'):
			print(lin)
	return out

class Spinner:
	busy = False
	delay = 0.1

	@staticmethod
	def spinning_cursor():
		while 1: 
			for cursor in '|/-\\': yield cursor

	def __init__(self, delay=None):
		self.spinner_generator = self.spinning_cursor()
		if delay and float(delay): self.delay = delay

	def spinner_task(self):
		while self.busy:
			sys.stdout.write(next(self.spinner_generator))
			sys.stdout.flush()
			time.sleep(self.delay)
			sys.stdout.write('\b')
			sys.stdout.flush()

	def start(self):
		self.busy = True
		threading.Thread(target=self.spinner_task).start()

	def stop(self):
		self.busy = False
		time.sleep(self.delay)

def convert_graphs():
	G1 = nx.read_gml(os.path.join(graphpath, 'G1.gml'))
	nx.write_edgelist(G1, os.path.join(here, 'G1.tab'),  delimiter='\t', data=False)

	G2 = nx.read_gml(os.path.join(graphpath, 'G2.gml'))
	nx.write_edgelist(G2, os.path.join(here, 'G2.tab'),  delimiter='\t', data=False)

def run_graph_align():
	os.chdir(here)
	cmd = './NETAL G1.tab G2.tab -a %s -b %s -c %s -i %s'%(NETAL_CONFIG['a'], NETAL_CONFIG['b'], NETAL_CONFIG['c'], NETAL_CONFIG['i'])
	spinner = Spinner()
	spinner.start()
	run_subProcess(cmd)
	spinner.stop()
	os.chdir(solpath)

def get_solution_map(solutionFile):
	pdf = pd.read_csv(os.path.join(here, solutionFile), sep='->', header=None)
	pdf[0]=pdf[0].apply(str)
	pdf[0]=pdf[0].apply(str.strip)

	pdf[1]=pdf[1].apply(str)
	pdf[1]=pdf[1].apply(str.strip)

	pdf0 = pdf[0].values.tolist()
	pdf1 = pdf[1].values.tolist()
	d = OrderedDict(zip(pdf0, pdf1))
	return d


if __name__ == '__main__':
	
	convert_graphs()
	run_graph_align()
	solutionFile = '(G1.tab-G2.tab)-a%s-b%s-c%s-i%s.alignment'%(NETAL_CONFIG['a'], NETAL_CONFIG['b'], NETAL_CONFIG['c'], NETAL_CONFIG['i'])
	solutionMap = get_solution_map(solutionFile)
	testData = d3mds.get_test_data()
	matchCol = []
	for row in testData.iterrows():
		node1 = str(row[1]['G1.nodeID'])
		node2 = str(row[1]['G2.nodeID'])
		if node1 not in solutionMap:
			matchCol.append(0)
		else:
			node2_tilde = solutionMap[node1]
			if node2.strip() == node2_tilde.strip():
				matchCol.append(1)
			else:
				matchCol.append(0)
	
	testData['match'] = matchCol

	testData.pop('G1.nodeID')
	testData.pop('G2.nodeID')
	testData.to_csv('predictions.csv')

	y_pred = matchCol

	try:
		y_truth =  d3mds.get_test_targets().ravel()
		accuracy = accuracy_score(y_truth, y_pred)
		print('accuracy on test data', accuracy)
		df = pd.DataFrame(columns=['metric', 'value','randomSeed','fold'])
		df.loc[len(df)] = ['accuracy', accuracy, None, 0]
		df.to_csv(os.path.join(solpath, 'scores.csv'), index=None)
	except:
		pass



		

	 




