#!/bin/bash

# Install necessary libraries
apt-get update
apt-get install -y wget unzip curl gnupg

# Install Chrome Browser
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y

# Verify Chrome installation
google-chrome --version
