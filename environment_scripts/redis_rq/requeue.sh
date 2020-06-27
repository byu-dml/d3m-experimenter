#declare -a arr=("b3477fc6-ddfe-4f13-ac0a-3b09ce52fcc6"
#"284fbf4c-eefe-4899-812b-2d5e9054c4bb")

readarray arr < failed_job_ids.txt

echo ${#arr[@]}
## now loop through the above array
for i in "${arr[@]}"
do
   ITER=$(expr $ITER + 1)
   rq requeue -u redis://1potato:27182 ${i}
   # or do whatever with individual element of the array
done

# You can access them using echo "${arr[0]}", "${arr[1]}" also

