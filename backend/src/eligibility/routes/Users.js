const express = require('express');
const { TwitterApi } = require('twitter-api-v2');
const config = require('../../configuration/config');
const router = express.Router();
const fs = require('fs');
const writeOut = require('../FileIO/WriteOut');

// Configure the domains collection for matching relevant URLs
let rawData = fs.readFileSync('./Resources/domains.json');
const domainList = JSON.parse(rawData).Domains;

router.get('/eligibility/:access_token&:access_token_secret&:mturk_id&:mturk_hit_id&:mturk_assignment_id', async (request, response) => {
  const userTweets = [];
  const userLikedTweets = [];
  const token = request.params.access_token;
  const token_secret = request.params.access_token_secret;
  const mturk_id = request.params.mturk_id;
  const mturk_hit_id = request.params.mturk_hit_id;
  const mturk_assignment_id = request.params.mturk_assignment_id;

  const client = new TwitterApi({
    appKey: config.key,
    appSecret: config.key_secret,
    accessToken: token,
    accessSecret: token_secret,
  });

  const user = await client.v2.me();
  const userId = user.data.id;

  let tweetCount = 0;
  let favoriteCount = 0;
  let retweetCount = 0;
  let likedTweetsListCount = 0;
  let homeTimelineNewsGuardLinkCount = 0;
  let likedTweetsNewsGuardLinkCount = 0;
  let error = false;

  try {
    const homeTimeline = await client.v1.homeTimeline({ exclude_replies: true });
    for await (const tweet of homeTimeline) {
      userTweets.push(tweet); // Store the tweet.
      tweetCount++;
      if (tweet.favorited)
        favoriteCount++;
      if (tweet.retweeted)
        retweetCount++;

      for (const url of tweet.entities.urls) {
        for (let i = 0; i < domainList.length; i++)
          try {
            if (url.expanded_url.includes(domainList[i])) {
              homeTimelineNewsGuardLinkCount++;
              break; // If it matches one stop looking, increase speed.
            }
          } catch {
            console.log("String parsing error.");
          }
      }
      /* if (tweetCount == 18) // For dev so limit isn't hit
        break; */
    }
    // Get users liked tweets and parse as well.
    const userLikes = await client.v1.get('favorites/list.json?count=200&user_id=' + userId, { full_text: true });
    for (let i = 0; i < userLikes.length; ++i) {
      likedTweetsListCount++;
      userLikedTweets.push(userLikes[i]);
      // Look for newsguard links in the liked tweets
      for (const url of userLikes[i].entities.urls) {
        for (let i = 0; i < domainList.length; i++)
          try {
            if (url.expanded_url.includes(domainList[i])) {
              likedTweetsNewsGuardLinkCount++;
              break; // If it matches one stop looking, increase speed.
            }
          } catch {
            console.log("String parsing error.");
          }
      }
    }

  } catch (Error) {
    console.log(Error);
    error = true;
  }
  const writeObject = {
    "userTweets": userTweets,
    "likedTweets": userLikedTweets,
    "MTurkId": mturk_id,
    "MTurkHitId": mturk_hit_id,
    "MTurkAssignmentId": mturk_assignment_id
  };

  if (!error)
    writeOut(writeObject, userId); // Asynchronously call the function to avoid slowdown.

  const json_response = {
    tweetCount: tweetCount,
    error: error,
    homeTimelineFavoriteCount: favoriteCount,
    homeTimelineRetweetCount: retweetCount,
    homeTimelineNewsGuardLinkCount: homeTimelineNewsGuardLinkCount,
    likedTweetsListCount: likedTweetsListCount,
    likedTweetsNewsGuardLinkCount: likedTweetsNewsGuardLinkCount
  }

  response.write(JSON.stringify(json_response));
  response.send();
});


module.exports = router;