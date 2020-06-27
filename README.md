# Camunda external task worker

This repository contains a worker class for executing external service tasks. The worker is written in Python and uses the package <a href="https://pypi.org/project/pycamunda/">PyCamunda</a> for communicating with Camunda. It is able to

*  subscribe to multiple external service task topics,
*  request variables from the process instance,
*  send variables back to the process instance,
*  handle failures and retry failing service tasks.

This repository comes with a simple example process with 2 service tasks. One generates a random number and the other one prints that number. 
