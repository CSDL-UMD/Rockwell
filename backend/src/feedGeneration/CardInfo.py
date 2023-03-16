#Function to get the card info from a website for a tweet.
#Requires full tweet links in order to work as anticipated.
import html # This may not be needed and can be removed if you take out line 18. Im not sure it actually does anything.
import requests as rq
import time
#import asgiref # pip install asgiref
from bs4 import BeautifulSoup
import asyncio
from configparser import ConfigParser
#from src.databaseAccess.database_config import config

def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

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
    params = config('../configuration/config.ini','twitterapp')
    titleMax = int(params['title_max'])
    descriptionMax = int(params['description_max'])

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

            if meta_tag_image is None:
                meta_tag_image = soup.find("meta", {"property": "twitter:image:src"}) # some also do "twitter:image:src", this covers it.
            
            imageLink = meta_tag_image.get('content')

            articleTitleFiltered = meta_tag_title.get('content')
            titleSoup = BeautifulSoup(articleTitleFiltered)
            articleTitleFiltered = titleSoup.get_text()

            if (len(articleTitleFiltered) > titleMax):
                articleTitleFiltered = articleTitleFiltered[0:titleMax]
                articleTitleFiltered = articleTitleFiltered + "..."

            articleDescriptionFiltered = meta_tag_description.get('content')
            descriptionSoup = BeautifulSoup(articleDescriptionFiltered)
            articleDescriptionFiltered = descriptionSoup.get_text()

            if (len(articleDescriptionFiltered) > descriptionMax):
                articleDescriptionFiltered = articleDescriptionFiltered[0:descriptionMax]
                articleDescriptionFiltered = articleDescriptionFiltered + "..."

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

            if meta_tag_image is None:
                meta_tag_image = soup.find("meta", {"property": "twitter:image:src"}) # some also do "twitter:image:src", this covers it.
            
            imageLink = meta_tag_image.get('content')

            articleTitleFiltered = meta_tag_title.get('content')
            titleSoup = BeautifulSoup(articleTitleFiltered,features="html.parser")
            articleTitleFiltered = titleSoup.get_text()

            if (len(articleTitleFiltered) > titleMax):
                articleTitleFiltered = articleTitleFiltered[0:titleMax]
                articleTitleFiltered = articleTitleFiltered + "..."

            articleDescriptionFiltered = meta_tag_description.get('content')
            descriptionSoup = BeautifulSoup(articleDescriptionFiltered)
            articleDescriptionFiltered = descriptionSoup.get_text()

            if (len(articleDescriptionFiltered) > descriptionMax):
                articleDescriptionFiltered = articleDescriptionFiltered[0:descriptionMax]
                articleDescriptionFiltered = articleDescriptionFiltered + "..."



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
            titleSoup = BeautifulSoup(articleTitleFiltered,features="html.parser")
            articleTitleFiltered = titleSoup.get_text()

            if (len(articleTitleFiltered) > titleMax):
                articleTitleFiltered = articleTitleFiltered[0:titleMax]
                articleTitleFiltered = articleTitleFiltered + "..."

            articleDescriptionFiltered = meta_tag_description.get('content')
            descriptionSoup = BeautifulSoup(articleDescriptionFiltered,features="html.parser")
            articleDescriptionFiltered = descriptionSoup.get_text()

            if (len(articleDescriptionFiltered) > descriptionMax):
                articleDescriptionFiltered = articleDescriptionFiltered[0:descriptionMax]
                articleDescriptionFiltered = articleDescriptionFiltered + "..."


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
