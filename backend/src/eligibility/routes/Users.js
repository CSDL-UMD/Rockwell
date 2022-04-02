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
  const v1User = await client.v1.user({ user_id: userId });
  delete v1User.status; // Cut down on user object size

  // Hometimeline variables
  const userHomeTimelineTweets = [];
  let homeTimelineTweetCount = 0;
  let homeTimelineFavoriteCount = 0;
  let homeTimelineRetweetCount = 0;
  let newsGuardHomeTimelineLikeCount = 0;
  let newsGuardHomeTimelineRetweetCount = 0;
  let homeTimelineNewsGuardLinkCount = 0;
  let error = false;

  // favorites/list variables
  const userLikedTweets = [];
  let likedTweetsListCount = 0;
  let likedTweetsNewsGuardLinkCount = 0;

  // Usertimeline variables
  const userTimelineTweets = [];
  let userTimelineTweetCount = 0;
  let userTimelineNewsGuardLinkCount = 0;
  let userTimelineLikeCount = 0;
  let userTimelineRetweetCount = 0;
  let newsGuardUserTimelineLikeCount = 0;
  let newsGuardUserTimelineRetweetCount = 0;

  try {
    const homeTimeline = await client.v1.homeTimeline({ exclude_replies: true, count: 200 });
    for await (const tweet of homeTimeline) {
      if (tweet.user.id == userId) // Ignore if we are author
        continue;

      userHomeTimelineTweets.push(tweet);
      homeTimelineTweetCount++;
      if (tweet.favorited)
        homeTimelineFavoriteCount++;
      if (tweet.retweeted)
        homeTimelineRetweetCount++;

      for (const url of tweet.entities.urls) {
        for (let i = 0; i < domainList.length; i++)
          try {
            if (url.expanded_url.includes(domainList[i])) {
              if (tweet.favorited)
                newsGuardHomeTimelineLikeCount++;
              if (tweet.retweeted)
                newsGuardHomeTimelineRetweetCount++;

              homeTimelineNewsGuardLinkCount++;
              break;
            }
          } catch {
            console.log("String parsing error.");
          }
      }
      /*if (homeTimelineTweetCount == 18) // For dev so limit isn't hit
        break;*/
    }
    // Get users liked tweets and parse as well.
    /* Commented to save rate limit. Will use later.
    const userLikes = await client.v1.get('favorites/list.json?count=200&user_id=' + userId, { full_text: true }); // Can get 75 pages of this with max_id
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
    */
  } catch (Error) {
    console.log(Error);
    error = true;
  }

  const userTimeline = await client.v1.userTimeline(userId, { include_entities: true, count: 200 });
  for await (const tweet of userTimeline) {
    userTimelineTweets.push(tweet);
    userTimelineTweetCount++;

        if (tweet.favorited)
          userTimelineLikeCount++;
        if (tweet.retweeted)
          userTimelineRetweetCount++;
    
        for (const url of tweet.entities.urls) {
          for (let i = 0; i < domainList.length; i++)
            try {
              if (url.expanded_url.includes(domainList[i])) {
                if (tweet.favorited)
                  newsGuardUserTimelineLikeCount++;
                if (tweet.retweeted)
                  newsGuardUserTimelineRetweetCount++;
    
                userTimelineNewsGuardLinkCount++;
                break;
              }
            } catch {
              console.log("String parsing error.");
            }
        }
  }

  const json_response = {
    error: error,
    homeTimelineTweetCount: homeTimelineTweetCount,
    homeTimelineFavoriteCount: homeTimelineFavoriteCount,
    homeTimelineRetweetCount: homeTimelineRetweetCount,
    homeTimelineNewsGuardLinkCount: homeTimelineNewsGuardLinkCount,
    newsGuardHomeTimelineRetweetCount: newsGuardHomeTimelineRetweetCount,
    newsGuardHomeTimelineLikeCount: newsGuardHomeTimelineLikeCount,
    likedTweetsListCount: likedTweetsListCount,
    likedTweetsNewsGuardLinkCount: likedTweetsNewsGuardLinkCount,
    userTimelineTweetCount: userTimelineTweetCount,
    userTimelineLikeCount: userTimelineLikeCount,
    userTimelineRetweetCount: userTimelineRetweetCount,
    userTimelineNewsGuardLinkCount: userTimelineNewsGuardLinkCount,
    newsGuardUserTimelineLikeCount: newsGuardUserTimelineLikeCount,
    newsGuardUserTimelineRetweetCount: newsGuardUserTimelineRetweetCount,
    userObject: v1User
  }

  const writeObject = {
    "userHomeTimelineTweets": userHomeTimelineTweets,
    "likedTweets": userLikedTweets,
    "userTimelineTweets": userTimelineTweets,
    "MTurkId": mturk_id,
    "MTurkHitId": mturk_hit_id,
    "MTurkAssignmentId": mturk_assignment_id,
    "userObject": v1User,
    "ResponseObject": json_response
  };

  if (!error)
    await writeOut(writeObject, userId); // Synchronous call to see if it fixes write issues.

  response.write(JSON.stringify(json_response));
  response.send();
});


module.exports = router;