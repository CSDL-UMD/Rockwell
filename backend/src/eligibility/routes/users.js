const express = require('express');
const { TwitterApi } = require('twitter-api-v2');
const config = require('../../configuration/config');
const router = express.Router();
const fs = require('fs');

// Configure the domains collection for matching relevant URLs
let rawData = fs.readFileSync('./Resources/domains.json');
const domainList = JSON.parse(rawData).Domains;

router.get('/eligibility/:access_token&:access_token_secret', async (request, response) => {
  const token = request.params.access_token;
  const token_secret = request.params.access_token_secret;

  const client = new TwitterApi({
    appKey: config.key,
    appSecret: config.key_secret,
    accessToken: token,
    accessSecret: token_secret,
  });

  let tweetCount = 0;
  let favoriteCount = 0;
  let retweetCount = 0;
  let newsGuardLinkCount = 0;
  let error = false;
  try {
    const homeTimeline = await client.v1.homeTimeline({ exclude_replies: true });
    for await (const tweet of homeTimeline) {
      tweetCount++;
      if (tweet.favorited)
        favoriteCount++;
      if (tweet.retweeted)
        retweetCount++;

      for (const url of tweet.entities.urls) {
        for (let i = 0; i < domainList.length; i++)
          if (url.expanded_url.contains(domainList[i]))
            newsGuardLinkCount++;
      }
      if (tweetCount == 18) // For dev so limit isn't hit
        break;
    }
  } catch {
    error = true;
  }

  const json_response = {
    tweetCount: tweetCount,
    error: error,
    favoriteCount: favoriteCount,
    retweetCount: retweetCount,
    newsGuardCount: newsGuardLinkCount
  }

  response.write(JSON.stringify(json_response));
  response.send();
});


module.exports = router;