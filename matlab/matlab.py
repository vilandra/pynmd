"""
Tools for managing matfiles or matlab suff

Gabriel Garcia Medina
ggarcia@coas.oregonstate.edu
May 2015

Dependencies:
-------------
datetime, numpy

Internal dependencies:
----------------------
none

"""

# Import modules
import datetime
import numpy as np
from scipy import io as sio

# ==============================================================================
# Tools to convert from datenum (matlab) to datetime (python)
# ==============================================================================
def datenum_to_datetime(ma_datenum):
    '''
    Tool to convert from Matlab's datenum to python's datetime
    
    PARAMETERS
    ----------
    ma_datenum    : matlab datetime numpy array
    
    RETURNS
    -------
    py_datetime   : numpy array with ma_datenum in python's datetime format
    
    '''
    
   
    py_datetime = np.array([datetime.datetime.fromordinal(int(ma_datenum[aa])) +
                   datetime.timedelta(days=ma_datenum[aa]%1) -
                   datetime.timedelta(days=366)
                   for aa in range(ma_datenum.shape[0])])
                   
    return py_datetime
    

#===============================================================================
# Read pre-hdf5 matfiles
#===============================================================================
def read_mat(matfile):
    '''
    Read matfiles prior to v7.3 (i.e. not HDF5)
    
    USAGE:
    ------
    s = matlab.read_mat(matfile)
    
    PARAMETERS:
    -----------
    matfile : Full path to the matfile to read
    
    RETURNS:
    --------
    s      : data structure of matfile
    
    NOTES:
    ------
    This function is really a wrapper for 
    s = sio.loadmat(matfile,squeeze_me=True,struct_as_record=False)
    '''
    
    try:
        s = sio.loadmat(matfile,squeeze_me=True,struct_as_record=False)        
    except NotImplementedError:
        print('Could not read mat file, it may be HDF5')
        print('If that is the case use h5py module to read')
        s = []
        
    return s
