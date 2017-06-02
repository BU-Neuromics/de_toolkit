import docopt                                                                   
import numpy as np                                                              
import os                                                                       
import pandas                                                                   
import pytest                                                                   
import tempfile                                                                 

from de_toolkit.stats import base                                                                               
def test_stats_base(fake_counts_obj): 
	output = base(fake_counts_obj)
	cols = output.get('stats', {}).get('num_cols')
	rows = output.get('stats', {}).get('num_rows')
	assert cols==3 and rows==5 



