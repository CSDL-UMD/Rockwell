#Function to get the card info from a website for a tweet.
#Requires full tweet links in order to work as anticipated.
import html # This may not be needed and can be removed if you take out line 18. Im not sure it actually does anything.
import requests as rq

# no longer fetches the actual image this should increase the speed of execution by alot. !!
def getCardData(link) -> dict: 
    content = rq.get(link)
    searchMe = content.text
    try:      
        # Block to find the image
        tagLocation = searchMe.find('\"og:image\"')
        openQuote = searchMe.find("\"",tagLocation + 10) # Plus 10 so we dont count our own mark.
        closeQuote = searchMe.find("\"",openQuote + 1)
        imageLink = searchMe[int(openQuote) + 1:int(closeQuote)]
        #imageRaw = rq.get(imageLink) # This is the image.
        #End block

        #Block to find the Title
        html.unescape(searchMe)
        tagLocation = searchMe.find("\"og:title\"")
        openQuote = searchMe.find("\"",tagLocation + 15) # Plus 15 to avoid overlap.
        closeQuote = searchMe.find("\"",openQuote + 1)
        articleTitle = searchMe[openQuote + 1: closeQuote]
        articleTitleFiltered = articleTitle.replace("&#x27;","\'") # Dirty but effectively converts the "code" to a '
        #End block

        #Block to find description
        tagLocation = searchMe.find("\"og:description\"")
        openQuote = searchMe.find("\"",tagLocation + 16) # Plus 16 to avoid overlap.
        closeQuote = searchMe.find("\"",openQuote + 1)
        articleDescription = searchMe[openQuote + 1: closeQuote]
        articleDescriptionFiltered = articleDescription.replace("&#x27;","\'") # Dirty but effectively converts the "code" to a '
        #End block

        #Creating the return dictonary if all actions worked.
        out = {
            "image": imageLink,
            "title": articleTitleFiltered,
            "description": articleDescriptionFiltered
        }

        return out # Returning a dictonary with all neccessary information
        
    except:
        # Attempt to load with alternate more generic tags if the first failed.
        try:
            # Block to find the image
            tagLocation = searchMe.find('\"twitter:image\"')
            openQuote = searchMe.find("\"",tagLocation + 15) # Plus 15 so we dont count our own mark.
            closeQuote = searchMe.find("\"",openQuote + 1)
            imageLink = searchMe[int(openQuote) + 1:int(closeQuote)]
            #imageRaw = rq.get(imageLink) # This is the image.
            #End block

            #Block to find the Title
            html.unescape(searchMe)
            tagLocation = searchMe.find("\"twitter:title\"")
            openQuote = searchMe.find("\"",tagLocation + 18) # Plus 18 to avoid overlap.
            closeQuote = searchMe.find("\"",openQuote + 1)
            articleTitle = searchMe[openQuote + 1: closeQuote]
            articleTitleFiltered = articleTitle.replace("&#x27;","\'") # Dirty but effectively converts the "code" to a '
            #End block

            #Block to find description
            tagLocation = searchMe.find("\"twitter:description\"")
            openQuote = searchMe.find("\"",tagLocation + 22) # Plus 22 to avoid overlap.
            closeQuote = searchMe.find("\"",openQuote + 1)
            articleDescription = searchMe[openQuote + 1: closeQuote]
            articleDescriptionFiltered = articleDescription.replace("&#x27;","\'") # Dirty but effectively converts the "code" to a '
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

#################### EXAMPLE OF HOW TO READ THE DATA
#read = open("test.csv",'r')
#for line in read:
#   data = getCardData(line)
#    print(data["imageLink"])
#    print(data["title"])
#   print(data["description"])