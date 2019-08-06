*** NOTE *** This document is outdated. We will be updating this document soon!!


Contents:
=========
seed_datasets/
	A growing set of seed datasets released to D3M performers. These datasets have been converted to D3M format and schematized. They have also been redacted to remove identifying information and test data has been withheld.

	There are two kinds of seed datasets:
		o_* datasets are openml datasets (featurized, tabular datasets)
		r_* datasets are datasets that contain raw data (image, video, graph, tabular, etc.)

	The datasets also contain baseline information
		r_* datasets: 
			/dataset/solution/baseline/pipeline.py or pipeline.ipynb - the source code for baseline
			/dataset/solution/baseline/conda-requirements.yml - a requirements file for establishing a Conda env to run the baseline
			/dataset/solution/baseline/performance.json - a file which documents the performance of the baeline pipeline
			/dataset/solution/baseline/testTargets.csv - the output predictions of the baseline pipeline on /data/testData.csv (serves as a reference for what performer systems should be producing as output)
		o_* datasets:
			Note: Slacker system was used as the baseline system for all the OpenML datasets. The output of Slacker is a specification of a pipeline it produces for a given dataset and the performance of that pipeline on that testData
			/dataset/solution/baseline/pipeline.json - the output of the Slacker system
				** The specification of the pipeline in this file uses custom Classes from Slacker code. For more information about these classes please see Slacker code included here **

slacker.tar.gz
	Source code for the Slacker system


The seed datasets contained in this directory belong to one of these problem types. The same problem types are also represented in the eval datasets of the 2017 September dry-run event. Below is a description of the problem types and how the data is structured for each.

Problem Types:
==============
1. classification
	Given input data, determine the class(es) of the data points.
	
	Input: 
		data/raw_data/* (these can be [tabular, image, video, graphs, audio, timeseries, ...] files)
		data/trainData.csv
		data/trainTargets.csv
		data/testData.csv
	
	Output: testTargets.csv

2. regression
    Given input data, predict outputs of the data points.
	
	Input: 
		data/raw_data/* (these can be [tabular, image, video, graphs, audio, timeseries, ...] files)
		data/trainData.csv
		data/trainTargets.csv
		data/testData.csv
	
	Output: testTargets.csv

3. linkPrediction
	Given a graph with missing edges, predict if a given edge exists in the original complete graph. The graph can be node-/edge-attributed graph.
	
	Input: 
		data/raw_data/graph.gml
		data/testData.csv
	
	Output: testTargets.csv

	Notes: 	testData.csv has edges, testTargets.csv has a boolen field indicating if egdes in testData.csv exists or not.
			traindata.csv and trainTargets.csv are not part of this problem type and will be absent in data/
	
	Sample testDataData.csv
		d3mIndex,graph,source_nodeID,target_nodeID,linkType
		0,graph.gml,50,125,43
		1,graph.gml,4,107,24
		2,graph.gml,30,39,32
		3,graph.gml,51,75,2
		4,graph.gml,102,119,40
		5,graph.gml,99,129,20
	
	Sample testTargets.csv (to be predicted by the system)
		d3mIndex,linkExists
		0,1
		1,1
		2,1
		3,0
		4,1
		5,0

4. graphMatching
	There are two graphs with a subset of matching nodes. Given a partial mapping between the matching nodes, the task is to predict the rest of the mapping.

	Input: 
		data/raw_data/G1.gml
		data/raw_data/G2.gml 
		data/trainData.csv
		data/trainTargets.csv 
		data/testData.csv
	
	Output: testTargets.csv

	Notes: trainData.csv has nodes of G1, trainTargets.csv has nodes of G2 that are mapped to G1. Together, they represent the partial mapping between the matched nodes of G1 and G2.
	
	testData.csv has the nodes of G1 for which the system has to predict the matched nodes in G2.

	Sample trainData.csv
	d3mIndex,graph,G1.nodeID
	0,G1.gml,7
	1,G1.gml,152
	2,G1.gml,742
	3,G1.gml,12
	4,G1.gml,277
	5,G1.gml,279

	Sample trainTargets.csv
	d3mIndex,graph,G2.nodeID
	0,G2.gml,32
	1,G2.gml,433
	2,G2.gml,831
	3,G2.gml,616
	4,G2.gml,515
	5,G2.gml,796

	Sample testData.csv
	d3mIndex,graph,G1.nodeID
	0,G1.gml,2
	1,G1.gml,26
	2,G1.gml,27
	3,G1.gml,310
	4,G1.gml,318
	5,G1.gml,8

	Sample testTargets.csv (to be predicted by the system)
	d3mIndex,graph,G2.nodeID
	0,G2.gml,656
	1,G2.gml,140
	2,G2.gml,786
	3,G2.gml,560
	4,G2.gml,546
	5,G2.gml,150

timeseriesForecasting
Training data consists of one or more time series ending at a given time. The task is to predict the time series in the future to the times listed in test data.
	Inputs: 
		data/raw_data/<ts1>.timeseries, data/raw_data/<ts2>.timeseries, ... (e.g. sunspot.month.timeseries, sunspot.year.timeseries)
			raw time series files, one per variable. There can be multiple variables (e.g., stock prices of Yahoo!, Google, ... - each will have an separate .timeseries file)
		data/trainData.csv
			contains pointers to the raw time series files
			Sample:
				d3mIndex,timeSeriesName,timeSeriesDataFile
				0,sunspot.month,sunspot.month.timeseries
				1,sunspot.year,sunspot.year.timeseriee
		data/testData.csv
			contains points for prediction - can include multiple variables in the same file
			Sample:
				d3mIndex,time,timeSeriesName,timeSeriesDataFile
				0,1960.500000003,sunspot.month,sunspot.month.timeseries
				1,1960.58333333634,sunspot.month,sunspot.month.timeseries
				2,1960.66666666967,sunspot.month,sunspot.month.timeseries
				3,1960.750000003,sunspot.month,sunspot.month.timeseries
				4,1960.83333333634,sunspot.month,sunspot.month.timeseries
				5,1960.91666666967,sunspot.month,sunspot.month.timeseries
				...
				...
				...
				282,1960.0,sunspot.year,sunspot.year.timeseries
				283,1961.0,sunspot.year,sunspot.year.timeseries
				284,1962.0,sunspot.year,sunspot.year.timeseries
				285,1963.0,sunspot.year,sunspot.year.timeseries
				286,1964.0,sunspot.year,sunspot.year.timeseries
				287,1965.0,sunspot.year,sunspot.year.timeseries

	Output:
		testTargets.csv (to be predicted by the system)
			d3mIndex,value
			0,121.7
			1,134.1
			2,127.2
			3,82.8
			4,89.6
			5,85.6
			...
			...
			...
			282,112.3
			283,53.9
			284,37.5
			285,27.9
			286,10.2
			287,15.1

collaborativeFiltering
Given ratings from N users for M items, predict ratings on other items.
	Inputs: data/trainData.csv, data/trainTargets.csv, data/testData.csv

	Output: data/testTargets.csv

	Notes: trainData contains known ratings for user-item pairs
		User-Item pairs are contained in trainData.csv
		Sample trianData.csv
			d3mIndex,user_id,item_id
			0,37916,34
			1,37704,66
			2,2998,140
			3,42567,119
			4,62771,148
			5,8662,17

		Known ratings for the above are contained in trainTargets.csv
		Sample trainTargets.csv
			d3mIndex,rating
			0,-2.031
			1,0.656
			2,0.781
			3,7.75
			4,6.625
			5,-0.344

		User-Item pairs for unknown ratings are contained in testData.csv
		Sample testData.csv
			d3mIndex,user_id,item_id
			0,39053,54
			1,46105,16
			2,4172,16
			3,7464,19
			4,988,134
			5,57245,113

		Predicted ratings for User-Items pairs (in TestData.csv) are contained in testTargets.csv
		Sample testTargets.csv
			d3mIndex,rating
			0,-0.219
			1,-0.375
			2,-6.438
			3,7.344
			4,-2.531
			5,3.094

