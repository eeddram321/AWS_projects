#!/bin/bash

set -e  # Exit script if any command fails

# Update the instance and prepare /opt
sudo yum update -y
sudo chown ec2-user:ec2-user -R /opt

# Install Java (OpenJDK 11)
sudo amazon-linux-extras install java-openjdk11 -y

# Install Maven
MVN_VERSION="3.9.4"
cd /opt

# Clean up if previous download failed
rm -f apache-maven.tar.gz
rm -rf apache-maven-${MVN_VERSION}
sudo rm -f /opt/maven

# Download and extract Maven
wget https://dlcdn.apache.org/maven/maven-3/${MVN_VERSION}/binaries/apache-maven-${MVN_VERSION}-bin.tar.gz -O apache-maven.tar.gz
tar xvf apache-maven.tar.gz -C /opt
sudo ln -s /opt/apache-maven-${MVN_VERSION} /opt/maven

# Configure environment variables
echo 'export M2_HOME=/opt/maven' | sudo tee /etc/profile.d/maven.sh
echo 'export PATH=${M2_HOME}/bin:${PATH}' | sudo tee -a /etc/profile.d/maven.sh
sudo chmod +x /etc/profile.d/maven.sh
source /etc/profile.d/maven.sh

# Verify installation
mvn -version
