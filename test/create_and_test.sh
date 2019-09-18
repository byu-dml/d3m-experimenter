mkdir build
cp ../requirements.txt build/requirements.txt
cp ../Dockerfile build/test-Dockerfile
sed -i '$ d' build/test-Dockerfile  # removes the last line
echo "RUN pip3 install -r build/requirements.txt" >> build/test-Dockerfile  # add in the new requirements file location
# request codecov to detect CI environment to pass through to docker
export ci_env=`bash <(curl -s https://codecov.io/env)`
docker-compose up -d --build
sudo docker exec -it experimenter-test bash -c "pip3 install coverage"
sudo docker exec -it experimenter-test bash -c "pip3 install codecov"
sudo docker exec -it experimenter-test bash -c "export CODECOV_TOKEN='66edf814-d6e1-40ae-b98a-dfea63a7e197'"
sudo docker exec -it experimenter-test bash -c "coverage run run_tests.py"
 sudo docker exec -it experimenter-test bash -c "bash <(curl -s https://codecov.io/bash)"
rm -rf build/
