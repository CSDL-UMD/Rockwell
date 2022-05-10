const express = require('express');
const { TwitterApi, ApiResponseError } = require('twitter-api-v2');
const config = require('../../configuration/config');
const router = express.Router();
const fs = require('fs');
var path = require('path');
const writeOut = require('../FileIO/WriteOut');
var https = require('follow-redirects').https;

// Configure the domains collection for matching relevant URLs
let rawData = fs.readFileSync('./Resources/domains.json');
const domainList = JSON.parse(rawData).Domains;

/* This can be used to resolve domain names but currently is not working, returns undefined in loop function calls however on a one by one it works.
const resolveURL = (hostname) => {
  const options = {
    method: 'HEAD'
  }

  const req = https.request(hostname, options, res => {
    return (res.responseUrl);
  })

  req.on('error', error => {
    console.error(error);
    return hostname;
  })

  req.end()
};
*/


router.get('/api/hometimeline/:access_token&:access_token_secret&:mturk_id&:mturk_hit_id&:mturk_assignment_id', async (request, response) => {
  const token = request.params.access_token;
  const token_secret = request.params.access_token_secret;
  const mturk_id = request.params.mturk_id;
  const mturk_hit_id = request.params.mturk_hit_id;
  const mturk_assignment_id = request.params.mturk_assignment_id;
  let errorMessage = "";
  let client;
  let user;
  let userId;
  let v1User;
  let error = false;

  try {
    client = new TwitterApi({
      appKey: config.key,
      appSecret: config.key_secret,
      accessToken: token,
      accessSecret: token_secret,
    });

    user = await client.v2.me();
    userId = user.data.id;
    v1User = await client.v1.user({ user_id: userId });
    delete v1User.status;

  } catch (Error) {
    console.log("Error authenticating.");
    response.write(JSON.stringify({ error: true, errorMessage: "Unable to authenticate using user keys.\n" })); // Different error types may be good or an error message
    response.send();
    return;
  }

  // Hometimeline variables
  const userHomeTimelineTweets = [];
  let homeTimelineTweetCount = 0;
  let homeTimelineFavoriteCount = 0;
  let homeTimelineRetweetCount = 0;
  let newsGuardHomeTimelineLikeCount = 0;
  let newsGuardHomeTimelineRetweetCount = 0;
  let homeTimelineNewsGuardLinkCount = 0;

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
    }
  } catch (Error) {
    error = true;
    if (Error instanceof ApiResponseError) {
      errorMessage += "Rate limit Exceeded";
    } else {
      errorMessage += "Unknown error occured fetching hometimeline";
    }
  }

  const json_response = {
    error: error,
    errorMessage: errorMessage,
    homeTimelineTweetCount: homeTimelineTweetCount,
    homeTimelineFavoriteCount: homeTimelineFavoriteCount,
    homeTimelineRetweetCount: homeTimelineRetweetCount,
    homeTimelineNewsGuardLinkCount: homeTimelineNewsGuardLinkCount,
    newsGuardHomeTimelineRetweetCount: newsGuardHomeTimelineRetweetCount,
    newsGuardHomeTimelineLikeCount: newsGuardHomeTimelineLikeCount,
    userObject: v1User
  }

  const writeObject = {
    MTurkId: mturk_id,
    MTurkHitId: mturk_hit_id,
    MTurkAssignmentId: mturk_assignment_id,
    userObject: v1User,
    ResponseObject: json_response
  };

  if (!error) {
    writeOut(writeObject, userId + '-home');
  }

  response.write(JSON.stringify(json_response));
  response.send();
});

router.get('/api/usertimeline/:access_token&:access_token_secret&:mturk_id&:mturk_hit_id&:mturk_assignment_id', async (request, response) => {
  const token = request.params.access_token;
  const token_secret = request.params.access_token_secret;
  const mturk_id = request.params.mturk_id;
  const mturk_hit_id = request.params.mturk_hit_id;
  const mturk_assignment_id = request.params.mturk_assignment_id;
  let errorMessage = "";
  let client;
  let user;
  let userId;
  let v1User;
  let error = false;

  try {
    client = new TwitterApi({
      appKey: config.key,
      appSecret: config.key_secret,
      accessToken: token,
      accessSecret: token_secret,
    });

    user = await client.v2.me();
    userId = user.data.id;
    v1User = await client.v1.user({ user_id: userId });
    delete v1User.status;

  } catch (Error) {
    console.log("Error authenticating.");
    response.write(JSON.stringify({ error: true, errorMessage: "Unable to authenticate using user keys.\n" })); // Different error types may be good or an error message
    response.send();
    return;
  }
  const userTimelineTweets = [];
  let userTimelineTweetCount = 0;
  let userTimelineLikeCount = 0;
  let userTimelineRetweetCount = 0;
  let userTimelineNewsGuardLinkCount = 0;
  let newsGuardUserTimelineLikeCount = 0;
  let newsGuardUserTimelineRetweetCount = 0;

  try {
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
      if(userTimelineTweetCount >= 1000) {
        break;
      }
    }
  } catch (Error) {
    error = true;
    if (Error instanceof ApiResponseError) {
      errorMessage += "Rate limit Exceeded";
    } else {
      errorMessage += "Unknown error occured fetching usertimeline";
    }
  }

  const json_response = {
    error: error,
    errorMessage: errorMessage,
    userTimelineTweetCount: userTimelineTweetCount,
    userTimelineLikeCount: userTimelineLikeCount,
    userTimelineRetweetCount: userTimelineRetweetCount,
    userTimelineNewsGuardLinkCount: userTimelineNewsGuardLinkCount,
    newsGuardUserTimelineLikeCount: newsGuardUserTimelineLikeCount,
    newsGuardUserTimelineRetweetCount: newsGuardUserTimelineRetweetCount,
    userObject: v1User
  }

  const writeObject = {
    MTurkId: mturk_id,
    MTurkHitId: mturk_hit_id,
    MTurkAssignmentId: mturk_assignment_id,
    userObject: v1User,
    ResponseObject: json_response
  };

  if (!error) {
    writeOut(writeObject, userId + '-user');
  }

  response.write(JSON.stringify(json_response));
  response.send();
});

router.get('/api/favorites/:access_token&:access_token_secret&:mturk_id&:mturk_hit_id&:mturk_assignment_id', async (request, response) => {
  const token = request.params.access_token;
  const token_secret = request.params.access_token_secret;
  const mturk_id = request.params.mturk_id;
  const mturk_hit_id = request.params.mturk_hit_id;
  const mturk_assignment_id = request.params.mturk_assignment_id;
  let errorMessage = "";
  let client;
  let user;
  let userId;
  let v1User;
  let error = false;

  try {
    client = new TwitterApi({
      appKey: config.key,
      appSecret: config.key_secret,
      accessToken: token,
      accessSecret: token_secret,
    });

    user = await client.v2.me();
    userId = user.data.id;
    v1User = await client.v1.user({ user_id: userId });
    delete v1User.status;

  } catch (Error) {
    console.log("Error authenticating.");
    response.write(JSON.stringify({ error: true, errorMessage: "Unable to authenticate using user keys.\n" })); // Different error types may be good or an error message
    response.send();
    return;
  }
  // favorites/list variables
  const userLikedTweets = [];
  let likedTweetsListCount = 0;
  let likedTweetsNewsGuardLinkCount = 0;

  // Get users liked tweets and parse as well.
  let minId;
  const likeLimit = 10;
  let currentPage = 0;
  try {
    let userLikes = await client.v1.get('favorites/list.json?count=200&user_id=' + userId, { full_text: true });
    while (currentPage < likeLimit) {
      minId = userLikes[0].id;
      for (let i = 0; i < userLikes.length; ++i) {
        likedTweetsListCount++;

        userLikedTweets.push(userLikes[i]);
        if (userLikes[i].id < minId)
          minId = userLikes[i].id;
        // Look for newsguard links in the liked tweets
        for (const url of userLikes[i].entities.urls) {
          for (let i = 0; i < domainList.length; i++)
            try {
              if (url.expanded_url.includes(domainList[i])) {
                likedTweetsNewsGuardLinkCount++;
                break;
              }
            } catch {
              console.log("String parsing error.");
            }
        }
      }
      // Next fetch here, also need to check for no tweets returned and stop.
      userLikes = await client.v1.get('favorites/list.json?count=200&user_id=' + userId + '&max_id=' + minId, { full_text: true });
      if (!userLikes.length)
        break;
      currentPage++;
    }
  } catch (Error) {
    error = true;
    if (Error instanceof ApiResponseError) {
      errorMessage += "Rate limit Exceeded";
    } else {
      errorMessage += "Unknown error occured fetching favorites";
    }
  }

  const json_response = {
    error: error,
    errorMessage: errorMessage,
    likedTweetsListCount: likedTweetsListCount,
    likedTweetsNewsGuardLinkCount: likedTweetsNewsGuardLinkCount,
    userObject: v1User
  }

  const writeObject = {
    MTurkId: mturk_id,
    MTurkHitId: mturk_hit_id,
    MTurkAssignmentId: mturk_assignment_id,
    userObject: v1User,
    likedTweets: userLikedTweets,
    ResponseObject: json_response
  };

  if (!error) {
    writeOut(writeObject, userId + '-fave');
  }
  response.write(JSON.stringify(json_response));
  response.send();
});

module.exports = router;
