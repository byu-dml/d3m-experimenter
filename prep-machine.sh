# This script sets up docker, builds the container, and enters it
echo "Starting"
sudo apt-get install docker -y
sudo apt-get install docker-compose -y
sudo docker-compose up -d
sudo docker exec -it experimenter bash
echo "Done creating enviroment"
