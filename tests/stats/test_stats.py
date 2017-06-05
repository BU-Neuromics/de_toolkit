import docopt                                                                   
import numpy as np                                                              
import os                                                                       
import pandas                                                                   
import pytest                                                                   
import tempfile                       
import json                                          

from de_toolkit.stats import base                                                                               
def test_stats_base(fake_counts_obj): 
	json_output = base(fake_counts_obj)
	output=json.loads(json_output)
	cols = output.get('stats', {}).get('num_cols')
	rows = output.get('stats', {}).get('num_rows')
	assert cols==3 and rows==5 



