# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 14:26:47 2019

Enter coords on the sky in console.
It then displays an image of that part of the sky that is 1 deg diameter and 1500 pixels square
It plots boxes for the main ccd and guide ccd that are the same apparent size as the 
cameras on the Tortugas mountain observatory.
The image is interactive, left mouse clicking a spot on the image will place the
center of the main CCD over the curser position, and right mouse click will place
the guide camera center. Both actions will move the other box respectivly.

@author: Alexander
"""

from IPython import get_ipython
#get_ipython().magic('reset -sf') 

import argparse
import wget
import os
import sys
import matplotlib.pyplot as plt
from astropy.visualization import astropy_mpl_style
plt.style.use(astropy_mpl_style)
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import Angle
from astropy import units
from photutils import CircularAperture
from photutils import RectangularAperture
from astropy.coordinates import SkyCoord
import pdb

# FOV of science camera in arcmin
SciX = 36.8
SciY = 24.8
PlateScale = 0.46
# FOV of guide camera in arcmin
GuideX = 6.14
GuideY = 4.85
# Offset to guider position
#GuideOffRA = -2.
#GuideOffDEC = -16.
GuideOffRA = 5.
GuideOffDEC = -34.


def coord_input():
    '''Asks user to input coordinates in hr min sec/deg arcmin arcsec format
    and converts those into degree decimals that the download link can use'''
    
    rastr = input('RA (hr:min:sec): ')
    decstr = input("DEC (deg:min:sec): ")
    return rastr, decstr

def image_download(RA, DEC, fov = '1.5', Size = '750'):
    """Generate URL and download image of sky centered around the coordinates specified
    """
    # uses user input to edit web address
    #address contains all information about image, including location, resolution, FoV, etc
    url = ('https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey=digitized+sky+survey&position='+
           RA+','+DEC+'&size='+fov+'&pixels='+Size+'&Return=FITS')

    #Download image
    print('downloading image....',url)
    wget.download(url, 'test.fits')
    print('reading image....')
    hdu = fits.open('test.fits')[0]
    os.remove('test.fits')
    return hdu
    
def image_setup(hdu):
    """Displays input image and overlays coordinate grid pulled from WCS data
    """
    wcs = WCS(hdu.header)
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(1,1,1,projection = wcs)
    ax.imshow(hdu.data, cmap = 'gray')
    
    return wcs, fig, ax

def place_overlay(x_pixel, y_pixel, mousebutton, wcs, ax, FOV = 1.5, Size = '750'):
    """Places either the main CCD, or the guide CCD apeture overlay 
    centered on the pixel coordinates depending on the boolean case "guide"
    specified in the input arguments. The overlay for the guide camera is placed
    with respect to the CCD center. Function also replots image to reset apertures
    (Easiest way I could find to do it for now)
    """
    fov = FOV*60
    size = int(Size)
    scale = fov/size
    #Set plate scale of image 60 is number of arcmin across 
    
    position_Target = (size/2, size/2)
    aperture_Target = CircularAperture(position_Target, r=(PlateScale/scale))
    aperture_Target.plot(color = 'blue', lw=1.5, alpha=0.5)
    
    if x_pixel == None or y_pixel == None:
        position_CCD = (size/2, size/2)
        position_Guide = (size/2-GuideOffRA/scale, ((size/2)+(GuideOffDEC/scale)))
    else:
        if mousebutton:
            position_Guide = (x_pixel, y_pixel)
            position_CCD = ((x_pixel)+GuideOffRA/scale, (y_pixel-(GuideOffDEC/scale)))
        else:
            position_Guide = (x_pixel-GuideOffRA/scale, y_pixel+(GuideOffDEC/scale))    
            position_CCD = ((x_pixel), (y_pixel))
        
    aperture_GuideStar = CircularAperture(position_Guide, r=(PlateScale/scale))
    aperture_Guide = RectangularAperture(position_Guide, (GuideX/scale),(GuideY/scale))
    aperture_GuideStar.plot(color = 'blue', lw=1.5, alpha=0.5)
    aperture_Guide.plot(color = 'red', lw=1.5, alpha=0.5)
    
    
    aperture_CCD = RectangularAperture(position_CCD,(SciX/scale),(SciY/scale))
    aperture_CCD.plot(color = 'green', lw=1.5, alpha=0.5)
    
    ax.figure.canvas.draw()
    
    coords = SkyCoord.from_pixel(position_CCD[0], position_CCD[1], wcs)
    RA_str = coords.ra.to_string(units.hour)
    DEC_str = coords.dec.to_string(units.degree)

    #print coords of main CCD center
    print(RA_str, DEC_str)
    
def onclick(event, ax, wcs):
    """Detects button press and reruns the overlay function to replot apertures
    on the location of the click. checks if it was the left or right mouse button
    Left mouse tells "place_overlay" to use mouse coords for Main CCD, and right mouse
    click uses the mouse coords for the guide CCD
    """
    x = event.xdata
    y = event.ydata
    if event.button == 3:       #Checks if click was left or right mouse button
        right = True
    else:
        right = False
    
    for p in reversed(ax.patches) : p.remove()
    
    place_overlay(x,y,right, wcs, ax)
    
def main(rastr=None,decstr=None):
    """Main function to run all the parts
    """

    # get image from skyview
    if rastr is None or decstr is None : 
        rastr,decstr = coord_input()
    ra=str(Angle(rastr+' h').deg)
    dec=str(Angle(decstr+' d').deg)
    print(ra,dec)
    hdu = image_download(ra, dec)
   
    # display 
    wcs, fig, ax = image_setup(hdu)
   
    # display views 
    place_overlay(None, None, mousebutton = False, wcs = wcs, ax = ax)
   
    # start event loop for repointing 
    fig.canvas.mpl_connect('button_press_event', lambda event: onclick(event, ax = ax, wcs = wcs))
    
    plt.show()
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        description='Get adjusted coordinates to find guide star')

    parser.add_argument("--ra", type=str, help='RA (J2000)')
    parser.add_argument("--dec", type=str, help='DEC (J2000)')
    args=parser.parse_args()

    main(rastr=args.ra,decstr=args.dec)
    
