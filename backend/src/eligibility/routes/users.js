const express = require('express');
const { TwitterApi } = require('twitter-api-v2');
const config = require('../../configuration/config');

const router = express.Router();

router.get('/eligibility/:access_token&:access_token_secret', async (request, response) => {
  const token = request.params.access_token;
  const token_secret = request.params.access_token_secret;

  const client = new TwitterApi({
    appKey: config.key,
    appSecret: config.key_secret,
    accessToken: token,
    accessSecret: token_secret,
  });
   const user = await client.v2.me();
   const userId = user.data.id;

   /*const tweetParameters = {
    'media.fields': 'url'
   }*/
  const tweetsOfUser = await client.v2.userTimeline(userId); // ,tweetParameters);

  while (!tweetsOfUser.done) {
    for (const tweet of tweetsOfUser) {
      console.log(tweet);
    }
    tweetsOfUser.fetchNext;
  }
  
  const json_response = {
    token: token,
    token_secret: token_secret
  }

  response.write(JSON.stringify(json_response));
  response.send();
});


module.exports = router;