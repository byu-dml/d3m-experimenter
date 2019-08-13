docker-compose up -d --build
sudo docker exec -it experimenter-test bash -c "ls"
sudo docker exec -it experimenter-test bash -c "python3 run_tests.py"
