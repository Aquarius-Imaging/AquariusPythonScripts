
########################################################################################################################
# 
# Purpose: This script contains a class for downloading documents from Aquarius DMS in a standard and repeatable way.
# It uses the GridViewExport.csv file, which is a standard download from Aquarius DMS Web query results. It then 
# creates a cross reference file between images and the document indexes.
#
########################################################################################################################


import utils.AquariusImaging as AquariusImaging
import os
import tifftools
from datetime import datetime
import pandas as pd
import re

class CrossRefDataWriter:
    def __init__(self,inputfile,uniqueIdentifier):
        
        #establish the output file path
        self.outputPath = os.path.dirname(inputfile)
        self.imageXRefFilePath = os.path.splitext(inputfile)[0] + 'ImageXRef.csv' # outputPath + '/ImageXref.csv'

        #create unique folder
        self.outputPath += '\\' + uniqueIdentifier + '\\'

        os.mkdir(self.outputPath)
    
        #create image cross reference data file.
        self.imageXRefFile = open(self.imageXRefFilePath,'wb')
    
        #write the column headers
        self.imageXRefFile.write(bytes('doc_id' + '\t' + 'Page' + '\t' + 'FileName' + '\n','UTF-8'))
   
    def Write(self,docID,pageCounter,fileName):
        self.imageXRefFile.write(bytes(docID + '\t' + str(pageCounter) + '\t' + fileName + '\n','UTF-8'))
                
    def Close(self):
        self.imageXRefFile.close()


def DownloadImagesFromQueryResults(inputFile,username,password,server,multiPage,uniqueIdentifier, type='image'):
    
    webApi=AquariusImaging.AquariusWebAPIWrapper(server)

    if (username != ""):
        webApi.authenticate(username,password)

    while webApi.Authenticated  == False:
                username=input("username: ")
                password=input("password: ")
                webApi.authenticate(username,password)


    #read the text file
    queryResultsData = open(inputFile, 'r', encoding='UTF-8')

    #establish a cross reference file
    XrefDataWriter=CrossRefDataWriter(inputFile,uniqueIdentifier)

    #begin document loop
    for resultLine in queryResultsData:
    
        docID = resultLine.split('\t')[0]

        print(f'{datetime.now()} {docID}')

        if (docID != 'doc_id'):
            
            #get the document page count
            docresponse = webApi.GetDocument(docID)
        
              #check for good response. 
            if (docresponse.status_code==200):
                doc = docresponse.json()
                
   
                #reset the variables
                pageCounter= 1
                tiff_files_li=[]

                #begin page loop
                while (pageCounter <= doc["pageCount"] ):

                    #retrieve the page
                    #write the image to disk
                    response=webApi.GetPage(docID,pageCounter,type)
                    
                    #check for good response. Failed response indicates we've run out of pages.
                    if (response.status_code==200):

                        fileName = response.headers['Content-Disposition']
                        fileName = os.path.join( XrefDataWriter.outputPath ,  docID + str(pageCounter) + re.sub('.*filename=(.+)(?: |$)','\\1',fileName))
                        fileName = fileName.replace('"','')
                        
                        #write the image to disk
                        imageFile = open(fileName, 'wb+')
                        imageFile.write(response.content)
                        imageFile.close ()
                        
                        tiff_files_li.append(fileName)
                    #increment the page counter
                    pageCounter += 1   

                    

                
                if(len(tiff_files_li) == 1):

                    XrefDataWriter.Write(docID,pageCounter,tiff_files_li[0])   

                elif(len(tiff_files_li) > 1 and multiPage):

                    #create a multi page tiff
                    newTif=None

                    for tiffFile in tiff_files_li:
                        if (newTif == None):
                            newTif=tifftools.read_tiff(tiffFile)
                        else:
                            tiftoadd = tifftools.read_tiff(tiffFile)
                            newTif['ifds'].extend(tiftoadd['ifds'])
                    
                    multiTiff = tiff_files_li[0].lower().replace(".tif","-multi.tif")
                    
                    tifftools.write_tiff(newTif,multiTiff)


                    #tifftools.tiff_concat(tiff_files_li,multiTiff, overwrite=True)
                    XrefDataWriter.Write(docID,1,multiTiff)
                    
                    #remove the single page images
                    for imagefile in tiff_files_li:
                        os.remove(imagefile)
                
                else:
                    pageCounter = 1
                    for singlepageimage in tiff_files_li:
                        XrefDataWriter.Write(docID,pageCounter,singlepageimage)
                        #increment the page counter
                        pageCounter += 1   
            else:
                # error downloading document
                print(f'{datetime.now()} Error downloading document {docID}. Error code: {docresponse.status_code}')

        #   end page loop
    #end document loop

    XrefDataWriter.Close()
    print(f'{datetime.now()} Process complete!')

def GetMergedData(inputFile):
        
    #read csv for document indexes
    indexes_df = pd.read_csv(inputFile,sep='\t', lineterminator='\n', header=0)

    #read csv for pages
    images_df = pd.read_csv(os.path.splitext(inputFile)[0] + 'ImageXRef.csv', sep='\t', lineterminator='\n', header=0)

    #merge the data
    merged_data = pd.merge(indexes_df,images_df,left_on='doc_id',right_on='doc_id',sort=True)
        
    return merged_data
