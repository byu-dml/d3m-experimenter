mkdir build
cp ../requirements.txt build/requirements.txt
cp ../Dockerfile build/test-Dockerfile
sed -i '$ d' build/test-Dockerfile  # removes the last line
echo "RUN pip3 install -r build/requirements.txt" >> build/test-Dockerfile  # add in the new requirements file location
docker-compose up -d --build
sudo docker exec -it experimenter-test bash -c "python3 run_tests.py"
rm -rf build/
