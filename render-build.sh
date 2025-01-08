#!/bin/bash

# Update the package list and install Chromium and Chromium Driver
apt-get update
apt-get install -y chromium chromium-driver

# Verify installation
chromium --version
chromium-driver --version
