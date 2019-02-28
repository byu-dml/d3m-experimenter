# this script enters the docker container, installs the requisite python libraries and becomes a worker
# (it does it this way because using docker "host" mode makes it unable to install python libraries at set up)
sudo docker exec -it experimenter bash
pip3 install pymongo
pip3 install rq
pip3 install redis
pip3 install d3m
python3 rq-worker.py