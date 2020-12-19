function retweet_clicked(tweet_id) {
  //var spawn = require("child_process").spawn;
  //const { spawn } = require('child_process');
  //var process = spawn('python',["./Retweet.py", 
  //                          tweet_id] );
  //require(["child_process"], function (cp) {
  //	console.log('Before Spawn definition');
  //  var spawn = cp.spawn;
  //  console.log('After Spawn definition');
  //  var process = spawn('python3',["./Retweet.py",tweet_id] );
  //  console.log('After Spawn');
    // ... use spawn()
  //});
  $.ajax({
            url: "http://localhost:5050/retweet/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({"tweet_id": String(tweet_id)})        
        }).done(function(data) {
            console.log(data);
        });    
}

function like_clicked(tweet_id) {

  //var spawn = require("child_process").spawn;
  //const { spawn } = require('child_process');
  //var process = spawn('python',["./Retweet.py", 
  //                          tweet_id] );
  //require(["child_process"], function (cp) {
  //	console.log('Before Spawn definition');
  //  var spawn = cp.spawn;
  //  console.log('After Spawn definition');
  //  var process = spawn('python3',["./Retweet.py",tweet_id] );
  //  console.log('After Spawn');
    // ... use spawn()
  //});
  $.ajax({
            url: "http://localhost:5050/like/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({"tweet_id": String(tweet_id)})        
        }).done(function(data) {
            console.log(data);
        });    
}

// Function to monitor tweets seen based on the screen position. Whole function works in pixels
function viewCountScrollBased(sizeList,curPos,furthestSeen,topPadding) {
  // sizeLIst is the array of all the "tweet" container sizes
  // curPos is the current position of the users screen given by the event listener, position of the top of the screen in pixels everytime they scroll
  // furthestSeen is the last tweet we have made it too and only count new reads if it is past this point. [index]
  //topPadding is the fixed size of the top bar and the first box that isnt a tweet.
  // Event listner on scroll, then call the screen postition function and pass me the current postition
  // Access the database and update how many tweets have been seen. We also need to figure out how to activate the main loop to load more tweets.
  

}