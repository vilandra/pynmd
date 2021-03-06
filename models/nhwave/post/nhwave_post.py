# -*- coding: utf-8 -*-
"""
Tools to manage NHWAVE input

Authors:
-------
Gabriel Garcia Medina
    Nearshore Modeling Group
    ggarcia@coas.oregonstate.edu
Saeed Moghimi

Log of edits:
-------------
April 2014 - Created module
    Gabriel Garcia Medina
17 September 2015
    Gabriel Garcia Medina 

External dependencies:
    netCDF4, time, getpass, os, numpy, sys, collections

Internal dependencies:
    waves
"""

from __future__ import division,print_function

__author__ = "Gabriel Garcia Medina"
__email__ = "ggarcia@coas.oregonstate.edu"
__group__="Nearshore Modeling Group"


# Import Modules
import netCDF4
import time
import sys
import getpass
import os
import numpy as np
from collections import defaultdict

# Internal modules
import pynmd.physics.waves as gwaves

#===============================================================================
# Pyroms subroutine to write NetCDF fields
#===============================================================================
def create_nc_var(nc, name, dimensions, units=None, longname=None):
    '''
    Not for standalone use
    '''
    nc.createVariable(name, 'f8', dimensions)
    if units is not None:
        nc.variables[name].units = units
    if longname is not None:
        nc.variables[name].long_name = longname    

# Append NetCDF variable        
def append_nc_var(nc,var,name,tstep):
    '''
    Not for standalone use
    '''
    nc.variables[name][tstep,...] = var


#===============================================================================
# Vorticity
#===============================================================================

def vorticity(x,y,u,v):
    '''
    
    Parameters:
    -----------
    x: 2d array of x locations of velocity points
    y: 2d array of y locations of velocity points
    u: 2d array of flow velocity in the x direction
    v: 2d array of flow velocity in the y direction3
    
    Output:
    -------
    q: 2d array of vertical vorticity (dv/dx - du/dy)
    
    '''
    
    # Compute gradients
    tmpgrad = np.gradient(x)
    dx = tmpgrad[1]
    tmpgrad = np.gradient(y)
    dy = tmpgrad[0]

    tmpgrad = np.gradient(u)
    du = tmpgrad[0]
    tmpgrad = np.gradient(v)
    dv = tmpgrad[1]
    
    # Compute vorticity
    return (dv/dx - du/dy)



# ==================================================================
# Create NetCDF file
# ==================================================================    
def convert_output(workfld,outfile,bathyfile=None,inpfile=None,verbose=False):
    '''
    
    Tools to convert ASCII output from NHWAVE to NetCDF4
    
    Parameters:
    -----------
    workfld      : Path to the folder where output files reside
    outfile      : Output file
    bathyfile    : Full path to input NetCDF bathy file (optional) 
    inpfile      : NHwave input files used to add metadata (optional)
    verbose      : Display progress messages (optional)
    
    Output:
    -------
    NetCDF File with the variables in the folder. Not all are supported so you 
    may need to edit this file.
    
    Notes:
    ------    
    
    TODO:
    -----
    1. Need to test for 2DH simulations.
    2. Add support for exponential vertical layers
    
    '''

    # Get variable information -------------------------------------------------
    archivos = os.listdir(workfld)                          # All files   
    tmpvars = [x.split('_')[0] for x in archivos]           # Variables
    tmpvars = list(set(tmpvars))                            # Unique variables

    # If no variables found exit    
    if not tmpvars:
        print('No files found in ' + workfld)
        print('Quitting ...')
        return None
    
    # Make sure variables are within the supported ones (exclude time here)
    supported_vars_2d_time = ['eta']    
    vars_2d_time = [x for x in tmpvars if x in supported_vars_2d_time]
    supported_vars_2d = ['setup','waveheight','umean','vmean']    
    vars_2d = [x for x in tmpvars if x in supported_vars_2d]
    supported_vars_3d_time = ['u','v','w']
    vars_3d_time = [x for x in tmpvars if x in supported_vars_3d_time]        
    supported_vars_3d = ['euler','lag']
    vars_3d = [x for x in tmpvars if x in supported_vars_3d]        
    
    # Read input file if provided ----------------------------------------------
    if inpfile:
       
        if verbose: 
            print("Reading data from input file:")
            print("  " + inpfile)
        
        # Open file
        tmpinpfile = open(inpfile,'r')
        
        # Output dictionary
        inpinfo = {}
        
        # Extract information (need to add wavemaker support)
        for tmpline in tmpinpfile:
            
            # Skip blank lines
            if len(tmpline.strip()) == 0:
                continue
            
            # Read selected keywords
            if "TITLE" == tmpline.split()[0]:
                inpinfo['title'] = tmpline.split()[2]
            elif "Mglob" == tmpline.split()[0]:
                inpinfo['mglob'] = tmpline.split()[2]
            elif "Nglob" == tmpline.split()[0]:
                inpinfo['nglob'] = tmpline.split()[2]
            elif "Kglob" == tmpline.split()[0]:
                inpinfo['kglob'] = tmpline.split()[2]
            elif "PX" == tmpline.split()[0]:
                inpinfo['px'] = tmpline.split()[2]
            elif "PY" == tmpline.split()[0]:
                inpinfo["py"] = tmpline.split()[2]
            elif "TOTAL_TIME" == tmpline.split()[0]:
                inpinfo['total_time'] = tmpline.split()[2]
            elif "PLOT_START" == tmpline.split()[0]:
                inpinfo['plot_start'] = tmpline.split()[2]
            elif "PLOT_INTV" == tmpline.split()[0]:
                inpinfo["plot_intv"] = tmpline.split()[2]
            elif "DX" == tmpline.split()[0]:
                inpinfo['dx'] = tmpline.split()[2]
                dx = float(tmpline.split()[2])
            elif "DY" == tmpline.split()[0]:
                inpinfo['dy'] = tmpline.split()[2]
                dy = float(tmpline.split()[2])
            elif "IVGRD" == tmpline.split()[0]:
                inpinfo['ivgrd'] = tmpline.split()[2]
            elif "DT_INI" == tmpline.split()[0]:
                inpinfo['dt_ini'] = tmpline.split()[2]
            elif "DT_MIN" == tmpline.split()[0]:
                inpinfo['dt_min'] = tmpline.split()[2]
            elif "DT_MAX" == tmpline.split()[0]:
                inpinfo['dt_max'] = tmpline.split()[2]
            elif "HIGH_ORDER" == tmpline.split()[0]:
                inpinfo['high_order'] = tmpline.split()[2]
            elif "TIME_ORDER" == tmpline.split()[0]:
                inpinfo['time_order'] = tmpline.split()[2]
            elif "CONVECTION" == tmpline.split()[0]:
                inpinfo['convection'] = tmpline.split()[2]
            elif "HLLC" == tmpline.split()[0]:
                inpinfo['hllc'] = tmpline.split()[2]
            elif "Ibot" == tmpline.split()[0]:
                inpinfo['ibot'] = tmpline.split()[2]
                ibot = int(tmpline.split()[2])
            elif "Cd0" == tmpline.split()[0] and ibot == 1:
                inpinfo['cd0'] = tmpline.split()[2]
            elif "Zob" == tmpline.split()[0] and ibot == 2:
                inpinfo['zob'] = tmpline.split()[2]
            elif "Iws" == tmpline.split()[0]:
                inpinfo['Iws'] = tmpline.split()[2]
                iws = int(tmpline.split()[2])
            elif "WindU" == tmpline.split()[0] and iws == 1:
                inpinfo['windu'] = tmpline.split()[2]
            elif "WindV" == tmpline.split()[0] and iws == 1:
                inpinfo['windv'] = tmpline.split()[2]
            elif "slat" == tmpline.split()[0]:
                inpinfo['slat'] = tmpline.split()[2]
            elif "BAROTROPIC" == tmpline.split()[0]:
                inpinfo['barotropic'] = tmpline.split()[2]
            elif "NON_HYDRO" == tmpline.split()[0]:
                inpinfo['non_hydro'] = tmpline.split()[2]
            elif "CFL" == tmpline.split()[0]:
                inpinfo['cfl'] = tmpline.split()[2]
            elif "TRAMP" == tmpline.split()[0]:
                inpinfo['tramp'] = tmpline.split()[2]
            elif "MinDep" == tmpline.split()[0]:
                inpinfo['min_dep'] = tmpline.split()[2]
            elif "ISOLVER" == tmpline.split()[0]:
                inpinfo['isolver'] = tmpline.split()[2]
            elif "PERIODIC_X" == tmpline.split()[0]:
                inpinfo['periodic_x'] = tmpline.split()[2]
            elif "PERIODIC_Y" == tmpline.split()[0]:
                inpinfo['periodic_y'] = tmpline.split()[2]
            elif "BC_X0" == tmpline.split()[0]:
                inpinfo['bc_x0'] = tmpline.split()[2]
            elif "BC_Xn" == tmpline.split()[0]:
                inpinfo['bc_xn'] = tmpline.split()[2]
            elif "BC_Y0" == tmpline.split()[0]:
                inpinfo['bc_y0'] = tmpline.split()[2]
            elif "BC_Yn" == tmpline.split()[0]:
                inpinfo['bc_yn'] = tmpline.split()[2]
            elif "BC_Z0" == tmpline.split()[0]:
                inpinfo['bc_z0'] = tmpline.split()[2]
            elif "BC_Zn" == tmpline.split()[0]:
                inpinfo['bc_zn'] = tmpline.split()[2]
            elif "WAVEMAKER" == tmpline.split()[0]:
                inpinfo['wavemaker'] = tmpline.split()[2]
            elif "SPONGE_ON" == tmpline.split()[0]:
                inpinfo['sponge'] = tmpline.split()[2]
                sponge = tmpline.split()[2]
            elif "Sponge_West_Width" == tmpline.split()[0] and sponge == 'T':
                inpinfo['sponge_west_width'] = tmpline.split()[2]
            elif "Sponge_East_Width" == tmpline.split()[0] and sponge == 'T':
                inpinfo['sponge_east_width'] = tmpline.split()[2]
            elif "Sponge_South_Width" == tmpline.split()[0] and sponge == 'T':
                inpinfo['sponge_south_width'] = tmpline.split()[2]
            elif "Sponge_North_Width" == tmpline.split()[0] and sponge == 'T':
                inpinfo['sponge_north_width'] = tmpline.split()[2]
            elif "Seed"  == tmpline.split()[0]:
                inpinfo['Seed'] = tmpline.split()[2]

            
        # Close file
        tmpinpfile.close()
            
    else:
        
        if verbose:
            print("Input file not provided")
    


    # If bathymetry file is given then the coordinates should be taken from 
    # this file, otherwise unit coordinates will be assumed with the shape of 
    # one of the output files.
    if bathyfile: 
        ncfile = netCDF4.Dataset(bathyfile,'r')
        x_rho = ncfile.variables['x_rho'][:]
        if ncfile.variables.has_key('y_rho'):
            y_rho = ncfile.variables['y_rho'][:]
        h = ncfile.variables['h'][:]
        ncfile.close()
        hdims = h.ndim
        
    else:
        
        if not os.path.isfile(workfld + '/depth'):
            print('No depth file found in ' + workfld)
            return None
        
        h = np.loadtxt(workfld + '/depth')
        
        # Check if it is a 1D or 2D model
        hdims = h.ndim                              # Horizontal dimensions
        if hdims == 1:
            x_rho = np.arange(0,h.shape[0],1)
        elif hdims == 2:
            x_rho, y_rho = np.meshgrid(np.arange(0,h.shape[1],1),
                                       np.arange(0,h.shape[0],1))
        else:
            print('Something is wrong with the depth file')
            print('Quitting...')
            return None
        
        
    # Load time vector
    if not os.path.isfile(workfld + '/time'):
        print("No time file found in " + workfld)
        print("Quitting ...")
        return None
    
    ocean_time = np.loadtxt(workfld + '/time')
        
        
    
    # Create NetCDF file ------------------------------------------------------  
    nc = netCDF4.Dataset(outfile, 'w', format='NETCDF4')
    nc.Description = 'NHWAVE Output'
    nc.Author = getpass.getuser()
    nc.Created = time.ctime()
    nc.Owner = 'Nearshore Modeling Group'
    nc.Software = 'Created with Python ' + sys.version
    nc.NetCDF_Lib = str(netCDF4.getlibversion())
    nc.Source = workfld
    nc.Script = os.path.realpath(__file__)
    
    # Add more global variables to output (if input file is provided)
    if inpinfo:
        for tmpatt in inpinfo.keys():
            nc.__setattr__(tmpatt,inpinfo[tmpatt][:])
    
    # Create dimensions
    if verbose:
        print('Creating dimensions')
        
    if hdims == 2:
        eta_rho, xi_rho = h.shape
        nc.createDimension('eta_rho', eta_rho)
    else:
        xi_rho = h.shape[0]
        eta_rho = 1
    nc.createDimension('xi_rho', xi_rho)            
    nc.createDimension('ocean_time',0)
                
    # Get vertical layers
    if not vars_3d and not vars_3d_time:
        print("No 3D variables found")
        s_rho = False
    else:
        # Load any 3D variables
        if os.path.isfile(workfld + '/' + vars_3d_time[0] + '_00001'):
            tmpvar = np.loadtxt(workfld + '/' + vars_3d_time[0] + '_00001')
        elif os.path.isfile(workfld + '/' + vars_3d[0] + '_umean'):
            tmpvar = np.loadtxt(workfld + '/' + vars_3d[0] + '_umean')
        elif os.path.isfile(workfld + '/' + vars_3d[0] + '_vmean'):
            tmpvar = np.loadtxt(workfld + '/' + vars_3d[0] + '_vmean')            
        else:
            tmpvar = np.loadtxt(workfld + '/' + vars_3d[0])
        
        # Outputs are stacked on the first dimension of the file
        # I need to enhance this and will probably have to use the input file
#         if hdims == 2:
#             s_rho = tmpvar.shape[0]/h.shape[0]
#         else:
#             s_rho = tmpvar.shape[0]
        s_rho = tmpvar.size/h.shape[0]
        
        nc.createDimension('s_rho',s_rho)
        
    
    # Write coordinates, bathymetry and time ----------------------------------
    if verbose:
        print("Saving coordinates and time")
    
    if hdims == 2:
        
        nc.createVariable('x_rho','f8',('eta_rho','xi_rho'))
        nc.variables['x_rho'].units = 'meter'
        nc.variables['x_rho'].longname = 'x-locations of RHO points'
        nc.variables['x_rho'][:] = x_rho
        
        nc.createVariable('y_rho','f8',('eta_rho','xi_rho'))
        nc.variables['y_rho'].units = 'meter'
        nc.variables['y_rho'].longname = 'y-locations of RHO points'
        nc.variables['y_rho'][:] = y_rho

        nc.createVariable('h','f8',('eta_rho','xi_rho'))
        nc.variables['h'].units = 'meter'
        nc.variables['h'].longname = 'bathymetry at RHO points'
        nc.variables['h'][:] = h


    else:
        
        nc.createVariable('x_rho','f8',('xi_rho'))
        nc.variables['x_rho'].units = 'meter'
        nc.variables['x_rho'].longname = 'x-locations of RHO points'
        nc.variables['x_rho'][:] = x_rho
        
        nc.createVariable('h','f8',('xi_rho'))
        nc.variables['h'].units = 'meter'
        nc.variables['h'].longname = 'bathymetry at RHO points'
        nc.variables['h'][:] = h
        
    
    # Create s_rho vector
    if s_rho:
        ds    = 1.0/s_rho
        sigma = np.arange(ds/2.0,1-ds/2.0,ds)
        nc.createVariable('s_rho','f8',('s_rho'))
        nc.variables['s_rho'].longname = 's-coordinate at cell centers'
        nc.variables['s_rho'].positive = 'up'
        nc.variables['s_rho'].notes = 'small s_rho means close to bottom'
        nc.variables['s_rho'][:] = sigma 
    
    # Create time vector
    nc.createVariable('ocean_time','f8','ocean_time')
    nc.variables['ocean_time'].units = 'seconds since 2000-01-01 00:00:00'
    nc.variables['ocean_time'].calendar = 'julian'
    nc.variables['ocean_time'].long_name = 'beach time since initialization'
    nc.variables['ocean_time'].notes = 'units are arbitrary'
    nc.variables['ocean_time'][:] = ocean_time



    # Create variables ---------------------------------------------------------    

    # Variable information
    varinfo = defaultdict(dict)

    varinfo['eta']['units'] = 'meter'
    varinfo['eta']['longname'] = 'water surface elevation'

    varinfo['waveheight']['units'] = 'meter'
    varinfo['waveheight']['longname'] = 'Mean wave height'
    varinfo['setup']['units'] = 'meter'
    varinfo['setup']['longname'] = 'Mean wave induced setup'
    
    varinfo['u']['units'] = 'meter second-1'
    varinfo['u']['longname'] = 'Flow velocity in the xi direction'
    varinfo['v']['units'] = 'meter second-1'
    varinfo['v']['longname'] = 'Flow velocity in the eta direction'
    varinfo['w']['units'] = 'meter second-1'
    varinfo['w']['longname'] = 'Flow velocity in the vertical direction'
    
    varinfo['umean']['units'] = 'meter second-1'
    varinfo['umean']['longname'] = 'Depth-averaged flow velocity in xi direction'
    varinfo['vmean']['units'] = 'meter second-1'
    varinfo['vmean']['longname'] = 'Depth-averaged flow velocity in eta direction'    
    
    varinfo['lag_umean']['units'] = 'meter second-1'
    varinfo['lag_umean']['longname'] = 'Lagrangian mean velocity in xi direction'
    varinfo['lag_vmean']['units'] = 'meter second-1'
    varinfo['lag_vmean']['longname'] = 'Lagrangian mean velocity in eta direction'
    varinfo['lag_wmean']['units'] = 'meter second-1'
    varinfo['lag_wmean']['longname'] = 'Lagrangian mean velocity in vertical direction'
    
    varinfo['euler_umean']['units'] = 'meter second-1'
    varinfo['euler_umean']['longname'] = 'Eulerian mean velocity in xi direction'
    varinfo['euler_vmean']['units'] = 'meter second-1'
    varinfo['euler_vmean']['longname'] = 'Eulerian mean velocity in eta direction'
    varinfo['euler_wmean']['units'] = 'meter second-1'
    varinfo['euler_wmean']['longname'] = 'Eulerian mean velocity in vertical direction'
    


    # Loop over 2D variables that have no time component ----------------------
    if hdims == 1:
        nc_dims = ('xi_rho')
    else:
        nc_dims = ('eta_rho','xi_rho')
          
    for aa in vars_2d:
        
        if verbose:
            print('  Writing ' + aa)
            
        # Create variable
        create_nc_var(nc,aa,nc_dims,varinfo[aa]['units'],
                      varinfo[aa]['longname'])
        nc.variables[aa][:] = np.loadtxt(workfld + '/' + aa) 
        
    
    # Loop over 3D variables that have no time component ----------------------
    if hdims == 1:
        nc_dims = ('s_rho','xi_rho')
    else:
        nc_dims = ('s_rho','eta_rho','xi_rho')    
    
    for aa in vars_3d:
        
        if verbose:
            print('  Writing ' + aa)
        
        if aa == 'euler' or aa == 'lag':
            for bb in ['umean','vmean','wmean']:
                create_nc_var(nc,aa + '_' + bb,nc_dims,
                              varinfo[aa + '_' + bb]['units'],
                              varinfo[aa + '_' + bb]['longname'])                
                if hdims == 1:
                    nc.variables[aa + '_' + bb][:] = \
                    np.loadtxt(workfld + '/' + aa + '_' + bb)
                else:
                    tmpvar = np.loadtxt(workfld + '/' + aa + '_' + bb)
                    tmpvar2 = np.zeros((s_rho,eta_rho,xi_rho))
                    for cc in range(s_rho):                        
                        tmpvar2[cc,:,:] = tmpvar[cc*eta_rho:(cc+1)*eta_rho,:]
                        
                    nc.variables[aa + '_' + bb][:] = tmpvar2
                    del tmpvar,tmpvar2
                    
        else:
            # Need to test this part with a full 3d code
            print("need to fix this")

            
        
        
    # Loop over 2D variables that have a time component -----------------------        
    if hdims == 1:
        nc_dims = ('ocean_time','xi_rho')
    else:
        nc_dims = ('ocean_time','eta_rho','xi_rho')
          
          
    for aa in vars_2d_time:
        
        if verbose:
            print('  Writing ' + aa)
        
        # Create variable
        create_nc_var(nc,aa,nc_dims,varinfo[aa]['units'],
                      varinfo[aa]['longname'])
        
        tmpvar = np.loadtxt(workfld + '/' + aa + '_' + '%05.0f' % 1)        
        nc.variables[aa][:] = np.expand_dims(tmpvar,axis=0)
        
        for bb in range(2,len(ocean_time)+1):
            tmpvar = np.loadtxt(workfld + '/' + aa + '_' + '%05.0f' % bb)
            append_nc_var(nc,tmpvar,aa,bb-1)
             
    

    # Loop over 3D variables that have a time component -----------------------        
    if hdims == 1:
        nc_dims = ('ocean_time','s_rho','xi_rho')
    else:
        nc_dims = ('ocean_time','s_rho','eta_rho','xi_rho')
          
          
    for aa in vars_3d_time:
        
        if verbose:
            print('  Writing ' + aa)
        
        # Create variable
        create_nc_var(nc,aa,nc_dims,varinfo[aa]['units'],
                      varinfo[aa]['longname'])
        
        if hdims == 1:
            
            tmpvar = np.loadtxt(workfld + '/' + aa + '_' + '%05.0f' % 1)
            if s_rho == 1:
                nc.variables[aa][:] = np.expand_dims(np.expand_dims(tmpvar,
                                                                    axis=0),
                                                     axis=0)
            else:
                nc.variables[aa][:] = np.expand_dims(tmpvar,axis=0)
            for bb in range(2,len(ocean_time)+1):
                tmpvar = np.loadtxt(workfld + '/' + aa + '_' + '%05.0f' % bb)
                append_nc_var(nc,tmpvar,aa,bb-1)
        
        else:
            for bb in range(1,len(ocean_time)+1):
                tmpvar = np.loadtxt(workfld + '/' + aa + '_' + '%05.0f' % bb)
                tmpvar2 = np.zeros((s_rho,eta_rho,xi_rho))
                for cc in range(s_rho):
                    tmpvar2[cc,:,:] = tmpvar[cc*eta_rho:(cc+1)*eta_rho,:]
                
                if bb == 1:
                    nc.variables[aa][:] = np.expand_dims(tmpvar2,axis=0)
                else:
                    append_nc_var(nc,tmpvar2,aa,bb-1)
                del tmpvar,tmpvar2
                
                
                
    # Close NetCDF file -------------------------------------------------------
    if verbose:
        print('Created: ' + outfile)
    nc.close()
    
    # End of file



#===============================================================================
# Compute mean setup
#===============================================================================
def setup(runup,ot):
    """
    
    Parameters:
    ----------
    runup        : Water surface elevation time series [m]
    ot           : Time stamp vector [s]
    
    Output:
    -------
    Dictionary containing    
    setup        : Mean water surface elevation [m]
    r2_combined  : 2% runup exceedence value [m]
    r2_cdf       : 2% runup exceedence value computed from runup CDF [m]
    r1_cdf       : 1% runup exceedence value computed from runup CDF [m]    
    ig           : Significant infragravity swash elevation [m]
    in           : Significant incident swash elevation [m]
    swash        : Significant swash elevation [m]                   
    r_max        : Maximum runup [m]
    r_var        : Runup variance [m2]     
                   
    Notes:
    ------
    r2_combined = 1.1*(setup + 0.5*((ig**2 + in**2)**0.5))
    
    See also:
    gnhwave.runup
    
    """
    
    # Compute the setup
    setup = np.mean(runup)
    
    # Compute swash time series 
    swash = runup - setup
    
    # Compute spectrum
    freq = np.fft.fftshift(np.fft.fftfreq(ot.shape[0],ot[1]-ot[0]))
    Nt = freq.shape[0]
    if np.mod(Nt,2) == 1:
        zero_ind = np.int((Nt - 1.0)/2.0)
    else:
        zero_ind = np.int(Nt/2.0)  
    freq_amp = freq[zero_ind:]
    
    # Compute spectrum
    ff = np.fft.fftshift(np.fft.fft(swash))
    #sf = 2.0/Nt*(ff[zero_ind:].real**2 + ff[zero_ind:].imag**2)**0.5
    sf = (ff[zero_ind:].real**2 + ff[zero_ind:].imag**2)/Nt


    # Compute significant infragravity swash
    freq_ig = freq_amp<0.05
    freq_in = freq_amp>=0.05
    swash_ig = 4.0*(np.trapz(sf[freq_ig],freq_amp[freq_ig])**0.5)
    swash_in = 4.0*(np.trapz(sf[freq_in],freq_amp[freq_in])**0.5)

    # Compute R2% real and from formula
    r2_combined = (setup + 0.5*((swash_ig**2 + swash_in**2)**0.5))*1.1
    
    # Compute R2% from the cumulative distribution function
    r2_ind = np.int(np.floor(0.98*runup.shape[0]))
    r2_cdf = np.sort(runup)[r2_ind]

    # Compute R1% from the cumulative distribution function
    r1_ind = np.int(np.floor(0.99*runup.shape[0]))
    r1_cdf = np.sort(runup)[r1_ind]    
        
    # Generate output
    return {'setup':setup, 'ig':swash_ig,'in':swash_in,
            'r2_combined':r2_combined,'r2_cdf':r2_cdf,
            'r1_cdf':r1_cdf,'r_max':runup.max(),'r_var':np.var(runup)}


#===============================================================================
# Compute Runup
#===============================================================================
def runup(eta,h,x,r_depth=0.01):
    """
    
    Parameters:
    ----------
    eta          : Water surface elevation time series [m]
    h            : Bathymetry [m] (positive down)
    x            : x coordinates of h [m]
    r_depth      : Runup depth [m] (defaults to 0.01m)
    
    Output:
    -------
    runup        : Water surface elevation time series relative to SWL given
                   a contour depth [m]
    x_runup      : Across-shore location of runup time series [m]
                       
    Notes:
    ------
    Really meant for 1D simulations.
                   
    """
    
    # Preallocate runup variable
    runup = np.zeros(eta.shape[0])
    x_runup = np.zeros_like(runup)
    
    # Loop over time, which is assumed to be on the first dimension.
    for aa in range(runup.shape[0]):
        
        # Water depth
        wdepth = eta[aa,:] + h
        
        # Find the runup contour (search from left to right) 
        wdepth_ind = np.argmin(wdepth>r_depth)-1
        
        # Store the water surface elevation in matrix
        runup[aa]= eta[aa,wdepth_ind]

        # Store runup position
        x_runup[aa] = x[wdepth_ind]         
    
    # Done
    return runup,x_runup


def nc_runup(nc,r_depth=0.01):
    """
    
    Function to compute runup from netcdf file.
    
    Parameters:
    -----------
    nc           : NetCDF file handle
    r_depth      : Runup depth [m] (defaults to 0.01m)
    
    Output:
    -------
    runup        : Water surface elevation time series relative to SWL given
                   a contour depth [m]
    x_runup      : Across-shore location of runup time series [m]
                       
    Notes:
    ------
    -  Really meant for 1D simulations.
    -  See convert_output for ASCII to NetCDF4 file conversion.
    
    """
    
    # Load variables
    h = nc.variables['h'][:]
    ot = nc.variables['ocean_time'][:]
    x = nc.variables['x_rho'][:]
    
    # Preallocate runup variable
    runup = np.zeros(ot.shape[0])
    x_runup = np.zeros_like(runup)
    
    # Loop over time, which is assumed to be on the first dimension.
    for aa in range(runup.shape[0]):
        
        # Water depth
        eta = nc.variables['eta'][aa,:]
        wdepth = eta + h
        
        # Find the runup contour (search from left to right) 
        wdepth_ind = np.argmin(wdepth>r_depth)-1
        
        # Store the water surface elevation in matrix
        runup[aa]= eta[wdepth_ind]
        
        # Store runup position
        x_runup[aa] = x[wdepth_ind]
        
    
    # Done
    return runup,x_runup
    

#===============================================================================
# Depth averaged currents
#===============================================================================
def depth_average(u,eta,h):
    """
    Compute depth-averaged currents from NHwave output
    
    USAGE:
    ------
    ubar = depth_average(u,eta,h)
    
    Parameters:
    -----------
    u            : flow matrix (3D or 2D)
    eta          : water surface elevation (2D or 1D)
    h            : bottom (2D or 1D)
       
    Output:
    -------
    ubar         : Depth-averaged currents
       
    Notes:
    ------
    Uniform vertical grid supported (IVGRD = 1)
        
    """
    
    # Preallocate variables
    ubar = np.zeros_like(eta) * np.NAN
       
    # Compute vertical coordinate system
    ds    = 1.0/u.shape[0]
    #sigma = np.arange(ds/2.0,1-ds/2.0,ds)
    
    # Loop over the array
    for aa in range(ubar.shape[0]):
        
        # Total water depth
        D = eta[aa] + h[aa]
        
        # Depth average
        ubar[aa] =  np.sum(ds*D*u[:,aa])/D
    
    return ubar
    
    
