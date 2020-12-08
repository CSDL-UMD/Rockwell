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