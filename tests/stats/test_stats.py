import docopt                                                                   
import numpy as np                                                              
import os                                                                       
import pandas                                                                   
import pytest                                                                   
import tempfile                                                                 

from de_toolkit.stats import base                                                                               
def test_stats_base(fake_counts_obj): 
	output = base(fake_counts_obj)
	assert output[0]==3 and output[1]==5 
