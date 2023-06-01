The loading of the configuration needs to add additional debug-level logging to facilitate the user to debug. 

For this reason, I specifically added the configuration loading source to the deep_update function in utils.py. 

At the same time, in order to be able to pass the instantiated Settings class, additional Added a variable, set it to None where it is not necessary to perform such an operation, and modified it in function-related positions