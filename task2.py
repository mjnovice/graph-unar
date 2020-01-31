from matplotlib import pyplot as plt
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import sys

def iswhite(color):
    return color>=250

def find_grid_bounds(img):
    y_end, x_end = img.shape[:2]
    y_end-=1
    x_end-=1
    x_start, y_start = 0,0
    curx = x_start
    cury = y_start
    bound = {}
    while curx<x_end:
        found=False
        cury=y_start
        while cury<y_end and iswhite(img[cury,curx]):
            cury+=1
        if not cury>=y_end/2:
            found=True
            break
        if found:
            break
        curx+=1
    bound['x_start']=curx
    bound['y_start']=cury
    
    cury=y_end
    curx=x_end
    while curx>=0:
        found=False
        cury=y_end
        while cury>=0 and iswhite(img[cury,curx]):
            cury-=1
        if cury>(2*y_end)/3:
            found=True
            break
        if found:
            break
        curx-=1
    bound['x_end']=curx
    bound['y_end']=cury
    cv2.rectangle(img,(bound['x_start'],bound['y_start']),(bound['x_end'],bound['y_end']),(0,255,0),2)
    plt.imshow(img)
    return bound


def get_mids(bounds):
    midx = int((bounds['x_end']-bounds['x_start'])/2)+30
    midy = int((bounds['y_end']-bounds['y_start'])/2)+60
    return midx,midy

def overlay_grid(img,bounds,typ):
    gap=2
    white=(255,255,255)
    thickness=1
    cross_hair = 10
    err=10
    midx,midy=get_mids(bounds)
        
    if typ=='hor':
        for x in range(bounds['x_start'],bounds['x_end']+1,gap):
            if abs(x-midx)<=cross_hair:
                continue
            cv2.line(img, (x, bounds['y_start']-err), (x, midy-cross_hair), 255, thickness)
            cv2.line(img, (x, midy+cross_hair), (x, bounds['y_end']+err), 255, thickness)

    if typ=='ver':
        for y in range(bounds['y_start'],bounds['y_end']+1,gap):
            if abs(y-midy)<=cross_hair:
                continue
            cv2.line(img, (bounds['x_start']-err,y), (midx-cross_hair,y), 255, thickness)
            cv2.line(img, (midx+cross_hair,y), (bounds['x_end']+err,y), 255, thickness)
def delete_axis_labels(img,bounds):
    size=40
    midx, midy = get_mids(bounds)
    x_coords = (bounds['x_end']+10,midy-50)
    y_coords = (midx-50,bounds['y_start']-50)
    cv2.rectangle(img, x_coords,(x_coords[0]+size,x_coords[1]+size), 255,-1)
    cv2.rectangle(img, y_coords,(y_coords[0]+size,y_coords[1]+size), 255,-1)
    return x_coords, y_coords,size
    
def add_axis_labels(img,bounds):
    x_coords,y_coords,size = delete_axis_labels(img,bounds)
    x = cv2.cvtColor(cv2.imread('x.png'), cv2.COLOR_BGR2GRAY)
    x = cv2.resize(x, (size-2,size), interpolation = cv2.INTER_AREA) 
    y = cv2.cvtColor(cv2.imread('y.png'), cv2.COLOR_BGR2GRAY)
    y = cv2.resize(y, (size,size), interpolation = cv2.INTER_AREA) 

    img[x_coords[1]+size:x_coords[1]+2*size, x_coords[0]:x_coords[0]+size] = x
    img[y_coords[1]:y_coords[1]+size, y_coords[0]+size:y_coords[0]+2*size] = y

def fix_gaps(curve):
    contours,_ = cv2.findContours(curve,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    orig = cv2.imread('linegraph.png')
    cv2.drawContours(curve, contours, -1, (0, 255, 0), 12)
    contours, _ = cv2.findContours(curve,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(curve, contours, -1, (0, 255, 0), 3)
    kernel = np.ones((3,3),np.uint8)
    return cv2.dilate(curve,kernel,iterations = 4)

def isolate_grid(img=cv2.imread('linegraph.png')):
    kernel_y = np.ones((200,1), np.uint8)
    kernel_x = np.ones((1,200), np.uint8)
    yaxis = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel_y)
    xaxis = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel_x)
    return xaxis, yaxis

if __name__=='__main__':
    plt.rcParams['figure.figsize'] = [15, 10]
    img = cv2.imread(sys.argv[1])
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, img = cv2.threshold(img, 230, 255, cv2.THRESH_BINARY)
    kernel = np.zeros((15,15),np.uint8)
    #img = cv2.erode(img,kernel,iterations = 25)
    plt.rcParams['figure.figsize'] = [10, 5]

    bounds = find_grid_bounds(img)

    #find axes
    xaxis, yaxis = isolate_grid(img)
    plt.imshow(xaxis,cmap=plt.cm.gray)

    #find figure
    curve = cv2.add(img, (255-xaxis))
    curve = cv2.add(curve, (255-yaxis))
    ret, imt = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)

    plt.imshow(imt,cmap=plt.cm.gray)
    ret, curve = cv2.threshold(curve, 100, 255, cv2.THRESH_BINARY)

    #line = thresh_img
    curve = cv2.medianBlur(curve, 5)
    delete_axis_labels(curve,bounds)
    curve = fix_gaps(curve)

    #make axes dotted
    overlay_grid(yaxis,bounds,"ver")
    overlay_grid(xaxis,bounds,"hor")
    axes = np.minimum(xaxis,yaxis)
    _,axes = cv2.threshold(axes, 180, 255, cv2.THRESH_BINARY)
    #final
    curve_edges = cv2.Canny(curve,600,600,apertureSize = 7)
    kernel = np.ones((2,2), np.uint8)
    curve_edges = cv2.dilate(curve_edges,kernel,iterations = 1)
    #plt.imshow(curve_edges, cmap=plt.cm.gray)

    final = np.minimum(axes,curve)
    final = np.maximum(final,curve_edges)
    #add labels
    add_axis_labels(final,bounds)
    cv2.imshow('output',final)
    key = cv2.waitKey(0)
