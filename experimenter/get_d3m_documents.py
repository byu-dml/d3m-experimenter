import os
import json
import elasticsearch as el

try:
    username = os.environ['USERNAME']
    password = int(os.environ['PASSWORD'])
except Exception as E:
    print("Exception: environment variables not set")
    raise E


def get_documents_elastic(name_of_index):
    es = el.Elasticsearch(
          ['https://metalearning.datadrivendiscovery.org/es/'],
          http_auth=(username, password))

    doc = {
            'size': 10,
            'query': {
                'match_all': {}
           }
       }
    data = es.search(index=name_of_index, body=doc, scroll='1m')
    # Get the scroll ID
    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    # Before scroll, process current batch of hits
    list_of_json = []
    list_of_json.append(data['hits']['hits'])

    while scroll_size > 0:
        "Scrolling..."
        data = es.scroll(scroll_id=sid, scroll='2m')

        # Process current batch of hits
        list_of_json.append(data['hits']['hits'])

        # Update the scroll ID
        sid = data['_scroll_id']

        # Get the number of results that returned in the last scroll
        scroll_size = len(data['hits']['hits'])

    json_files = [item for sublist in list_of_json for item in sublist]
    return json_files

# json_files = get_documents_elastic("pipelines")
# for data, index in enumerate(json_files):
#     with open('d3m_data/pipelines/{}.json'.format(index), 'w') as outfile:
#         json.dump(data, outfile)
#
# json_files_runs = get_documents_elastic("pipeline_runs")
# for data, index in enumerate(json_files_runs):
#     with open('d3m_data/pipeline_runs/{}.json'.format(index), 'w') as outfile:
#         json.dump(data, outfile)

print("Done")