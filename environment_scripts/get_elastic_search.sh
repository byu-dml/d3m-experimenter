es_url=https://metalearning.datadrivendiscovery.org/es
index=pipelines

response=$(curl -u 'username:password!' -s $es_url/$index/_search?size=1\&scroll=1m)
scroll_id=$(echo $response | jq -r ._scroll_id)
hits_count=$(echo $response | jq -r '.hits.hits | length')
hits_so_far=hits_count
echo Got initial response with $hits_count hits and scroll ID $scroll_id

echo $response >> results_from_query_2.json
echo Done outputting to initial file

while [ "$hits_count" -ne "0" ]; do
  echo In Loop
  response=$(curl -u 'username:password!' -s $es_url/_search/scroll?scroll=1m -d "$scroll_id")
  scroll_id=$(echo $response | jq -r ._scroll_id)
  hits_count=$(echo $response | jq -r '.hits.hits | length')
  hits_so_far=$((hits_so_far + hits_count))
  echo "Got response with $hits_count hits (hits so far: $hits_so_far), new scroll ID $scroll_id"
  
  echo $response >> results_from_query_2.json
  echo Done outputting to initial file
done


echo Done