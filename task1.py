import sqlite3
import sys
from sqlite3 import Error
from matplotlib import pyplot as plt
import cv2
import numpy as np
import pytesseract
from pytesseract import Output

plt.rcParams['figure.figsize'] = [20, 15]
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return conn
 
 
def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def insertEntries(conn, table, entries):
    c = conn.cursor()
    for entry in entries:
        try:
            myDict = entry
            keys = []
            values = []
            for k in myDict:
                keys.append(k)
                values.append(myDict[k])
            columns = ', '.join(myDict.keys())
            placeholders = ', '.join('?' * len(myDict))
            sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, columns, placeholders)
            #qry = "INSERT INTO %s (%s) Values (%s)" % (table, qmarks, qmarks)
            print(sql)
            c.execute(sql, list(myDict.values()))
            #c.execute(insertFromDict(table,entry))
        except Error as e:
            print(e)

def createDb():
    database = "data.db"
 
    tables = [ """ CREATE TABLE IF NOT EXISTS bar_coords (
                                        id text PRIMARY KEY,
                                        x_start integer NOT NULL,
                                        y_start integer NOT NULL,
                                        x_end integer NOT NULL,
                                        y_end integer NOT NULL
                                    ); """,\
             """CREATE TABLE IF NOT EXISTS bar_texts (
                                        id text PRIMARY KEY,
                                        value text NOT NULL,
                                        x_start integer NOT NULL,
                                        y_start integer NOT NULL,
                                        x_end integer NOT NULL,
                                        y_end integer NOT NULL
                                    );""",\
             """CREATE TABLE IF NOT EXISTS xaxis_texts (
                                        id text PRIMARY KEY,
                                        value text NOT NULL,
                                        x_start integer NOT NULL,
                                        y_start integer NOT NULL,
                                        x_end integer NOT NULL,
                                        y_end integer NOT NULL
                                    );""",\
             """CREATE TABLE IF NOT EXISTS yaxis_texts (
                                        id text PRIMARY KEY,
                                        value text NOT NULL, 
                                        x_start integer NOT NULL,
                                        y_start integer NOT NULL,
                                        x_end integer NOT NULL,
                                        y_end integer NOT NULL
                                    );""",\
             """CREATE TABLE IF NOT EXISTS relations (
                                        bar_coord_id text PRIMARY KEY,
                                        bar_text_id text,
                                        y_axis_labels text
                                    );""",\
             ]
 
    # create a database connection
    conn = create_connection(database)
 
    # create tables
    if conn is not None:
        for schema in tables:
            create_table(conn, schema)
 
    else:
        print("Error! cannot create the database connection.")
    return conn



def get_data(im):
    return pytesseract.image_to_data(im, output_type=Output.DICT)

def get_comp(data,i):
    comp = {
                     'value':data['text'][i],
                     'x_start':data['left'][i],
                     'x_end': data['left'][i]+data['width'][i],
                     'y_start':data['top'][i],
                     'y_end':data['top'][i]+data['height'][i],
            }
    return comp

def get_texts(img):
    data = get_data(img)
    texts=[]
    n = len(data['text'])
    for i in range(n):
        if len(data['text'][i].strip())==0:
            continue
        comp = get_comp(data,i)
        texts.append(comp)
        #putting a check to parse in only numbers and texts
        if data['text'][i].isalpha() or data['text'][i].isnumeric():
            pass
            #cv2.rectangle(img,(comp['x_start'],comp['y_start']),(comp['x_end'],comp['y_end']),(0,255,0),2)
    return texts

def get_split_components(img):
    x_start,y_start = 0,0
    y_end, x_end = img.shape[:2]
    texts = get_texts(img)
    
    #find the topmost text and the start of the y-axis
    topmost_ylimit = y_end + 1
    leftmost_xlimit = x_end + 1
    x_axis_ttls_ylimit = 0
    y_axis_ttls_xlimit = 0

    #find the topmost text first
    for text in texts:
        topmost_ylimit = min(topmost_ylimit, text['y_end'])
        leftmost_xlimit = min(leftmost_xlimit,text['x_end'])

    #find the x_axis_ttls_ylimit
    for text in texts:
        if topmost_ylimit < text['y_start'] and text['value'].isnumeric():
            x_axis_ttls_ylimit = max(x_axis_ttls_ylimit, text['y_start'])
    
    #find the y_axis_ttls_xlimit
    for text in texts:
        if topmost_ylimit < text['y_start'] and text['x_start'] > leftmost_xlimit and\
        text['value'].isalpha() and text['y_end'] < x_axis_ttls_ylimit:
            y_axis_ttls_xlimit = max(y_axis_ttls_xlimit, text['x_end'])
    

    print(x_axis_ttls_ylimit,y_axis_ttls_xlimit)
    #cv2.rectangle(img,(y_axis_ttls_xlimit,y_start),(x_end,x_axis_ttls_ylimit),(0,255,0),2)
    #plt.imshow(img)
    #print(y_axis_ttls_xlimit)
    x_ttls = []
    y_ttls = []
    i=0
    for text in texts:
        if text['x_start'] >= y_axis_ttls_xlimit and text['value'].isnumeric():
            text['id']=str(i)
            x_ttls.append(text)
            i+=1
    i=0
    for text in texts:
        if text['x_end'] <= y_axis_ttls_xlimit and text['y_end'] <= x_axis_ttls_ylimit:
            text['id']=str(i)
            y_ttls.append(text)
            i+=1
    
    bargraph_coords = {
                     'x_start':y_axis_ttls_xlimit,
                     'x_end': x_end,
                     'y_start':topmost_ylimit,
                     'y_end':x_axis_ttls_ylimit,
    }
    print(bargraph_coords)
    return x_ttls, y_ttls, bargraph_coords

def get_bar_texts(img,bb,idprefix):
    im=img.copy()
    bargraph=im[bb['y_start']:bb['y_end'],bb['x_start']:bb['x_end']]
    im = cv2.bitwise_not(bargraph)
    data = pytesseract.image_to_data(im, output_type=Output.DICT,config='--psm 6')
    texts = []
    n = len(data['text'])
    for i in range(n):
        if not data['text'][i].isnumeric():
            continue
        comp = get_comp(data,i)
        #offset
        comp['x_start'] += bb['x_start']
        comp['y_start'] += bb['y_start']
        comp['x_end'] += bb['x_start']
        comp['y_end'] += bb['y_start']
        comp['id'] = idprefix + str(i)
        texts.append(comp)
    return texts

def not_white(color):
    white_threshold=250
    return color[0]<white_threshold and color[1]<white_threshold and color[2]<white_threshold

def get_bcid(btid):
    return btid+"_bc"

def get_bar_coords(bar_texts,im):
    img = im.copy()
    bar_coords=[]
    idg=1
    for i,text in enumerate(bar_texts):
        tx,ty = text['x_start'],text['y_start']
        bx,by = text['x_end'],text['y_end']
        bound = {
                     'id':get_bcid(text['id']),
                     'x_start':tx,
                     'x_end': bx,
                     'y_start':ty,
                     'y_end':by,
        }
        #cv2.rectangle(img,(tx,ty),(bx,by),(0,255,0),2)
        print("origin",img[ty,tx],img[by,bx])
        while not_white(img[ty,tx]):
            tx-=1
        tx+=1
        bound['x_start']=tx
        tx,ty = text['x_start'],text['y_start']
        while not_white(img[ty,tx]):
            ty-=1
        ty+=1
        bound['y_start']=ty
        bx,by = text['x_end'],text['y_end']
        while not_white(img[by,bx]):
            bx+=1
        bx-=1
        bound['x_end']=bx
        bx,by = text['x_end'],text['y_end']
        while not_white(img[by,bx]):
            by+=1
        by-=1
        bound['y_end']=by
        #cv2.rectangle(im,(bound['x_start'],bound['y_start']),(bound['x_end'],bound['y_end']),(0,255,0),2)

        bar_coords.append(bound)
    plt.imshow(im)
    return bar_coords
if __name__=='__main__':
    img = cv2.imread(sys.argv[1])
    xaxis_texts, yaxis_texts, bb = get_split_components(img)

    bar_texts = get_bar_texts(img,bb,"bt") #key pattern bt<int>
    bar_coords = get_bar_coords(bar_texts,img) #key patter bc<int>
    relations = []
    for bt in bar_texts:
        rel={
            'bar_coord_id':get_bcid(bt['id']),
            'bar_text_id':bt['id'],
        }
        matches = []
        for yt in yaxis_texts:
            if yt['y_start']>=bt['y_start'] and yt['y_end']<=bt['y_end']:
                matches.append(yt['id'])
        rel['y_axis_labels'] = str(matches)
        relations.append(rel)

    conn = createDb()
    insertEntries(conn,'xaxis_texts',xaxis_texts)
    insertEntries(conn,'yaxis_texts',yaxis_texts)
    insertEntries(conn,'bar_texts',bar_texts)
    insertEntries(conn,'bar_coords',bar_coords)
    insertEntries(conn,'relations',relations)
    conn.commit()
