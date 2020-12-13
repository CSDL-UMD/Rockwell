
class TweetObject():
    def __init__(self,urls,expanded_urls,experiment_group,post_id,tweet_id,body,_class,picture,picture_heading,picture_description,actor,time):
        self.urls = urls
        self.expanded_urls = expanded_urls
        self.experiment_group = experiment_group
        self.post_id = post_id
        self.tweet_id = str(tweet_id)
        self.body = body
        self._class = _class
        self.picture = picture
        self.picture_heading = picture_heading
        self.picture_description = picture_description
        self.actor = actor
        self.time = time