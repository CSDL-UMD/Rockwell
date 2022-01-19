#Function to get the card info from a website for a tweet.
#Requires full tweet links in order to work as anticipated.
import html # This may not be needed and can be removed if you take out line 18. Im not sure it actually does anything.
import requests as rq
import time
#import asgiref # pip install asgiref
from bs4 import BeautifulSoup
import asyncio

# no longer fetches the actual image this should increase the speed of execution by alot. !!
#@async_to_sync
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
        searchMe = fetchWebpage(link) # changed this call to async to make the fetching of webpages asyncronus.
        if(searchMe == None):
            time.sleep(0.1) # This can be adjusted and async may be desirable.
            failCounter = failCounter + 1
        else:
            break

    out = {}
    if(searchMe is not None): # Check if our request passed.
        soup = ""
        try: # Create our BeautifulSoup parser "soup"
            soup = BeautifulSoup(searchMe,"html.parser")
        except:
            print("Very unexpected error. Log this")
            return out
        try:
            meta_tag_image = soup.find("meta", {"property": "twitter:image"}) # Could be None even in this tag scope, if below.
            meta_tag_title = soup.find("meta", {"property": "twitter:title"})
            meta_tag_description = soup.find("meta", {"property": "twitter:description"})

            imageLink = meta_tag_image.get('content')
            if imageLink is None:
                meta_tag_image = soup.find("meta", {"property": "twitter:image:src"}) # some also do "twitter:image:src", this covers it.
                imageLink = meta_tag_image.get('content')

            articleTitleFiltered = meta_tag_title.get('content')

            articleDescriptionFiltered = meta_tag_description.get('content')

            #Creating the return dictonary if all actions worked.
            out = {
                "image": imageLink,
                "title": articleTitleFiltered,
                "description": articleDescriptionFiltered
            }

            return out # Returning a dictonary with all neccessary information
            
        except:
            pass # Did not discover, not an error just no twitter tag.
            
        try: #try twitter tag under <meta name> if <meta property> didn't work
            meta_tag_image = soup.find("meta", {"name": "twitter:image"}) # Could be None even in this tag scope, if below.
            meta_tag_title = soup.find("meta", {"name": "twitter:title"})
            meta_tag_description = soup.find("meta", {"name": "twitter:description"})

            imageLink = meta_tag_image.get('content')
            if imageLink is None:
                meta_tag_image = soup.find("meta", {"name": "twitter:image:src"})
                imageLink = meta_tag_image.get('content')

            articleTitleFiltered = meta_tag_title.get('content')

            articleDescriptionFiltered = meta_tag_description.get('content')

            #Creating the return dictonary if all actions worked.
            out = {
                "image": imageLink,
                "title": articleTitleFiltered,
                "description": articleDescriptionFiltered
            }

            return out # Returning a dictonary with all neccessary information
            
        except:
            pass # Did not discover, not an error just no twitter tag under meta name.
        
        try: # Try the default og: tags if twitter: does not work.
            meta_tag_image = soup.find("meta", {"property": "og:image"})
            meta_tag_title = soup.find("meta", {"property": "og:title"})
            meta_tag_description = soup.find("meta", {"property": "og:description"})

            imageLink = meta_tag_image.get('content')
            articleTitleFiltered = meta_tag_title.get('content')

            articleDescriptionFiltered = meta_tag_description.get('content')
            #Creating the return dictonary if all actions worked.
            out = {
                "image": imageLink,
                "title": articleTitleFiltered,
                "description": articleDescriptionFiltered
            }
            return out
        except:
            pass
        

    else: # REQUEST FAILED.
        return out
