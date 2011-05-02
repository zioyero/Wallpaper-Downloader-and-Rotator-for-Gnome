#!/usr/bin/env python

"""
background_fetch.py

Download images from /r/EarthPorn (or from other reddits) and 
create a rotating background XML for Gnome.

See the README file for more details.
"""

import urllib2
import os
import random
import Image

from BeautifulSoup import BeautifulSoup
from urlparse import urlparse
from lxml import etree as ET

# expand the list with REDDIT IDs if you want
REDDITS = { 0 : 'EarthPorn',  1 : 'CityPorn', 2 : 'SpacePorn', 
            3 : 'AnimalPorn', 4 : 'BotanicalPorn', 5: 'AlternativeArt' }

##############################################################################
## change these variables
##############################################################################
# where to save the images:
PHOTO_DIR = '/home/adrian/Pictures/backgrounds/'
# 15 minutes:
DURATION = '600'#'895.0'
# transition time between two images:
TRANSITION = '2.5'
# EarthPorn, by default:
REDDIT = 5
# image size should have at least that many pixels:
SIZE_THRESHOLD = (900, 600)
# percentage, accept image if smaller than threshold by this percentage:
SIZE_TOLERANCE = 5.0
# ratio must be in this interval:
RATIO_INTERVAL = (1.0, 2.0)
##############################################################################

# don't change these
XML_FILENAME = "%s.xml" % REDDITS[REDDIT]    # EarthPorn.xml, by default
REDDIT_URL = "http://www.reddit.com/r/%s/" % REDDITS[REDDIT]

def get_image_list(url):
    """Fetch the HTML of reddit category and extract the URLs
       of JPG images."""
    images = []
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    for tag in soup.findAll('a', href=True):
        if tag['href'].lower().endswith('jpg'):
            if tag['href'] not in images:
                images.append(tag['href'])  # no duplicates and keep the order
     
    return images
# get_image_list

def get_flickr_list(url):
    flickr = []
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    for tag in soup.findAll('a', href=True):
        if tag['href'].lower().endswith('photostream/'):
            if tag['href'] not in flickr:
                flickr.append(tag['href'])

    return flickr

def file_name(url):
    """Return the file name from an URL.
       Ex.: http://example/pic.jpg => pic.jpg."""
    return os.path.split(urlparse(url)[2])[1]

def is_ok_for_wallpaper(image):
    """Decide whether an image is appropriate as a wallpaper.
       An image is good if (1) it's resolution is large enough,
       (2) rotation is landscape, and (3) ratio is OK."""
    minimum_pixels = SIZE_THRESHOLD[0] * SIZE_THRESHOLD[1] * \
                     ((100.0 - SIZE_TOLERANCE)/100.0)
    img = Image.open(PHOTO_DIR + file_name(image))
    width, height = img.size
    
    large = (width * height) >= minimum_pixels
    landscape = width > height
    ratio = float(width) / float(height)
    ratio_ok = (RATIO_INTERVAL[0] <= ratio <= RATIO_INTERVAL[1])
   
    ok = large and landscape and ratio_ok
    
    return ( large and landscape and ratio_ok )
# is_ok_for_wallpaper

def remove_unsuitable_images(all_images, filtered):
    """Remove images that are not so good for a wallpaper."""
    to_remove = list( set(all_images).difference(set(filtered)) )
    for bad in to_remove:
        os.remove( PHOTO_DIR + file_name(bad) )
        
    print "# removed images: %s" % len(to_remove)
# remove_unsuitable_images

def download_images(images):
    """Use wget to download images into specified directory."""
    count = 0
    for image in images:
        filename = os.path.basename(image)
        if os.path.exists(PHOTO_DIR + filename) is False:
            # download if the file doesn't exist yet
            os.system('wget -O ' + PHOTO_DIR + filename + ' ' + image)
            count += 1
            
    print "# new image(s): %d" % count
# download_images

def download_flickr_images(flickr):
    count = 0
    flickrImages = []
    for url in flickr:
        flickrImages+=get_image_list(url)
   
    return flickrImages

def write_xml_output(images):
    """Produce an XML output. This XML must be set as background
       under Gnome."""
    root = ET.Element('background')
    starttime = ET.SubElement(root, 'starttime')
    hour = ET.SubElement(starttime, 'hour')
    hour.text = '00'
    minute = ET.SubElement(starttime, 'minute')
    minute.text = '00'
    second = ET.SubElement(starttime, 'second')
    second.text = '01'
    size = len(images)  # save size
    images.append(images[0])    # add first element after the last
    for i in range(0, size):
        static = ET.SubElement(root, 'static')
        dur = ET.SubElement(static, 'duration')
        dur.text = DURATION
        file_tag = ET.SubElement(static, 'file')
        file_tag.text = PHOTO_DIR + images[i]
        #
        trans = ET.SubElement(root, 'transition')
        dur = ET.SubElement(trans, 'duration')
        dur.text = TRANSITION
        from_tag = ET.SubElement(trans, 'from')
        from_tag.text = PHOTO_DIR + images[i]
        to_tag = ET.SubElement(trans, 'to')
        to_tag.text = PHOTO_DIR + images[i+1]
    
    tree = ET.ElementTree(root)
    tree.write(PHOTO_DIR + XML_FILENAME, pretty_print=True, 
               xml_declaration=True)
# write_xml_output
    
def main():
    """Control block."""
    # get the URL of all images
    images = get_image_list(REDDIT_URL)
    
    # get the URL of all flickr images
    flickr = get_flickr_list(REDDIT_URL)

    flickrImg = download_flickr_images(flickr)
    
    for img in flickrImg:
        images.append(img)

    # download images
    download_images(images)

    # filter good images and remove the bad ones from the file system
    filtered = [x for x in images if is_ok_for_wallpaper(x)]
    remove_unsuitable_images(images, filtered)

    # work with these good images from now on
    images = filtered
    
    # create an XML file
    if len(images) > 0:
        # get all images in speficied directory
        jpegs = [x for x in os.listdir(PHOTO_DIR) if x.lower().endswith('jpg')]
        random.shuffle(jpegs) # randomize image order
        write_xml_output(jpegs)
# main

if __name__ == "__main__":
    main()
