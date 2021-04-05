#Function to get the card info from a website for a tweet.
#Requires full tweet links in order to work as anticipated.
import html # This may not be needed and can be removed if you take out line 18. Im not sure it actually does anything.
import requests as rq
import time
from bs4 import BeautifulSoup

# no longer fetches the actual image this should increase the speed of execution by alot. !!
def fetchWebpage(link):
    try:
        content = rq.get(link)
        searchMe = content.text
        return searchMe
    except:
        return None
    
def getCardData(link) -> dict: 
    failCounter = 0
    searchMe = None
    while(failCounter < 3):
        searchMe = fetchWebpage(link)
        if(searchMe == None):
            time.sleep(3) # This can be adjusted and async may be desirable.
            failCounter = failCounter + 1
        else:
            break


    if(searchMe is not None): # Check if our request passed.

        try:
            soup = BeautifulSoup(searchMe,"html.parser")
            meta_tag_image = soup.find("meta", {"property": "og:image"})
            meta_tag_title = soup.find("meta", {"property": "og:title"})
            meta_tag_description = soup.find("meta", {"property": "og:description"})
            # Block to find the image
            #tagLocation = searchMe.find('\"og:image\"')
            #openQuote = searchMe.find("\"",tagLocation + 10) # Plus 10 so we dont count our own mark.
            #closeQuote = searchMe.find("\"",openQuote + 1)
            #imageLink = BeautifulSoupsearchMe[int(openQuote) + 1:int(closeQuote)]
            imageLink = meta_tag_image.get('content')
            #imageRaw = rq.get(imageLink) # This is the image.
            #End block

            #Block to find the Title
            #html.unescape(searchMe)
            #tagLocation = searchMe.find("\"og:title\"")
            #openQuote = searchMe.find("\"",tagLocation + 15) # Plus 15 to avoid overlap.
            #closeQuote = searchMe.find("\"",openQuote + 1)
            #articleTitle = searchMe[openQuote + 1: closeQuote]
            #articleTitleFiltered = articleTitle.replace("&#x27;","\'") # Dirty but effectively converts the "code" to a '
            articleTitleFiltered = meta_tag_title.get('content')
            #articleTitleFiltered = articleTitle.replace("&#x27;","\'")
            #End block

            #Block to find description
            #tagLocation = searchMe.find("\"og:description\"")
            #openQuote = searchMe.find("\"",tagLocation + 16) # Plus 16 to avoid overlap.
            #closeQuote = searchMe.find("\"",openQuote + 1)
            #articleDescription = searchMe[openQuote + 1: closeQuote]
            #articleDescriptionFiltered = articleDescription.replace("&#x27;","\'") # Dirty but effectively converts the "code" to a '
            articleDescriptionFiltered = meta_tag_description.get('content')
            #articleDescriptionFiltered = articleDescription.replace("&#x27;","\'")
            #End block

            #Creating the return dictonary if all actions worked.
            out = {
                "image": imageLink,
                "title": articleTitleFiltered,
                "description": articleDescriptionFiltered
            }

            return out # Returning a dictonary with all neccessary information
            
        except:
            return {}
        #test = open("test.jpg","wb") This is the code to write out the image if desired.
        #test.write(imageRaw.content)
    else: # REQUEST FAILED.
        return {}
#################### EXAMPLE OF HOW TO READ THE DATA
#read = open("test.csv",'r')
#for line in read:
#   data = getCardData(line)
#    print(data["imageLink"])
#    print(data["title"])
#   print(data["description"])