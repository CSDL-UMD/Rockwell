var furthestSeen = 0;
var worker_id = 0;
var refreshh = 0;
var attn = 0;
var page = 0;
var pre_attn = 0;
var access_token = "";
var access_token_secret = "";
var slideIndex = 1;
var retweet_map = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
var like_map = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
var seen_map = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
var attn_map = [0,0,0,0];
var answers_map = [0,0,0,0];
var attn_map_actual = [0,0,0,0,0];
var click_map = [];

function set_session_id(wid,r,a,p,pre,acc,acc_secret) {
  worker_id = wid;
  refreshh = r;
  attn = a;
  page = p;
  pre_attn = pre;
  access_token = acc;
  access_token_secret = acc_secret;
  localStorage.setItem("retweet_map_"+String(refreshh), retweet_map);
  localStorage.setItem("like_map_"+String(refreshh), like_map);
  localStorage.setItem("seen_map_"+String(refreshh), seen_map);
  localStorage.setItem("click_map_"+String(refreshh), seen_map);
  console.log(attn);
  console.log(page);
}

function loadfeed() {
  attn = 0;
  page = 0;
  pre_attn = 0;
  urll = 'http://127.0.0.1:3000?access_token=' + String(access_token) + '&access_token_secret=' + String(access_token_secret) + '&worker_id=' + String(worker_id) + '&attn=' + String(attn) + '&page=' + String(page); + '&pre_attn_check=' + String(pre_attn);
  location.replace(urll);
}

function retweet_clicked(btn,arguments) {
  //var spawn = require("child_process").spawn;
  //const { spawn } = require('child_process');
  //var process = spawn('python',["./Retweet.py", 
  //                          tweet_id] );
  //require(["child_process"], function (cp) {
  //  console.log('Before Spawn definition');
  //  var spawn = cp.spawn;
  //  console.log('After Spawn definition');
  //  var process = spawn('python3',["./Retweet.py",tweet_id] );
  //  console.log('After Spawn');
    // ... use spawn()
  //});
  if(btn.innerHTML != 'Retweeted'){
    btn.innerHTML='Retweeted';
    btn.style.color = 'red';
    var tweet_id = arguments.split(',')[0].trim();
    var rank = arguments.split(',')[1].trim();
    document.getElementById('retweet_counter_'+tweet_id).innerHTML = parseInt(document.getElementById('retweet_counter_'+tweet_id).innerHTML) + 1
    retweet_map[rank-1] = 1; 
    localStorage.setItem("retweet_map_"+String(refreshh), retweet_map);
    $.ajax({
            url: "http://127.0.0.1:5050/retweet",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({"arguments": String(arguments)})        
          }).done(function(data) {
            console.log(data);
          });
  }    
}

function like_clicked(btn,arguments) {

  //var spawn = require("child_process").spawn;
  //const { spawn } = require('child_process');
  //var process = spawn('python',["./Retweet.py", 
  //                          tweet_id] );
  //require(["child_process"], function (cp) {
  //  console.log('Before Spawn definition');
  //  var spawn = cp.spawn;
  //  console.log('After Spawn definition');
  //  var process = spawn('python3',["./Retweet.py",tweet_id] );
  //  console.log('After Spawn');
    // ... use spawn()
  //});
  if(btn.innerHTML != 'Liked'){
    btn.innerHTML='Liked';
    btn.style.color = 'red';
    var tweet_id = arguments.split(',')[0].trim();
    var rank = arguments.split(',')[1].trim();
    document.getElementById('like_counter_'+tweet_id).innerHTML = parseInt(document.getElementById('like_counter_'+tweet_id).innerHTML) + 1
    like_map[rank-1] = 1;
    localStorage.setItem("like_map_"+String(refreshh), like_map);
    $.ajax({
            url: "http://127.0.0.1:5050/like",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({"arguments": String(arguments)})        
          }).done(function(data) {
            console.log(data);
          });
  }    
}

function link_clicked(link_arguments) {

  //var spawn = require("child_process").spawn;
  //const { spawn } = require('child_process');
  //var process = spawn('python',["./Retweet.py", 
  //                          tweet_id] );
  //require(["child_process"], function (cp) {
  //  console.log('Before Spawn definition');
  //  var spawn = cp.spawn;
  //  console.log('After Spawn definition');
  //  var process = spawn('python3',["./Retweet.py",tweet_id] );
  //  console.log('After Spawn');
    // ... use spawn()
  //});
  console.log("In Link Clicked");
  var tweet_id = link_arguments.split(',')[0].trim();
  var url = link_arguments.split(',')[1].trim();
  var is_card = link_arguments.split(',')[2].trim();
  var date = new Date();
  date = date.toLocaleString('en-US', { timeZone: 'America/New_York' });
  date = date.replace(","," ");
  click_map_url_in = tweet_id+";"+url+";"+is_card+";"+String(date);
  click_map.push(click_map_url_in);
  localStorage.setItem("click_map_"+String(refreshh), click_map);
  // $.ajax({
  //           url: "http://127.0.0.1:5050/link",
  //           type: "POST",
  //           contentType: "application/json",
  //           data: JSON.stringify({"arguments": String(arguments)})        
  //       }).done(function(data) {
  //           console.log(data);
  //       });    
}

function attn_clicked(n) {
  console.log(n);
  attn_map[n] = 1;
  var tot = attn_map.reduce((a, b) => a + b, 0)
  if(tot == 3){
      document.getElementById('nextarrow').style.color = "green";
      document.getElementById('nextarrow').style.cursor = "pointer";
      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
  }
}

function yesclicked(n) {
  yesbtn = document.getElementById('yesbtn_'+n);
  nobtn = document.getElementById('nobtn_'+n);
  if(nobtn.style.background == 'yellow')
    nobtn.style.background = 'white'
  yesbtn.style.background = 'yellow'
  if(pre_attn == 1){
    attn_map[n-1] = 1;
    answers_map[n-1] = 1;
    var tot = attn_map.reduce((a, b) => a + b, 0)
    if(tot == 4){
      document.getElementById('nextarrow').style.color = "green";
      document.getElementById('nextarrow').style.cursor = "pointer";
      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
    }
  }
  else{
    attn_map_actual[n-1] = 1;
    var tot = attn_map.reduce((a, b) => a + b, 0)
    if(tot == 5){
      document.getElementById('nextarrow').style.color = "green";
      document.getElementById('nextarrow').style.cursor = "pointer";
      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
    } 
  }  
}

function noclicked(n) {
  yesbtn = document.getElementById('yesbtn_'+n);
  nobtn = document.getElementById('nobtn_'+n);
  if(yesbtn.style.background == 'yellow')
    yesbtn.style.background = 'white'
  nobtn.style.background = 'yellow'
  if(pre_attn == 1){
    attn_map[n-1] = 1;
    answers_map[n-1] = 0;
    var tot = attn_map.reduce((a, b) => a + b, 0)
    if(tot == 4){
      document.getElementById('nextarrow').style.color = "green";
      document.getElementById('nextarrow').style.cursor = "pointer";
      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
    }
  }
  else{
    attn_map_actual[n-1] = 1;
    var tot = attn_map.reduce((a, b) => a + b, 0)
    if(tot == 5){
      document.getElementById('nextarrow').style.color = "green";
      document.getElementById('nextarrow').style.cursor = "pointer";
      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
    } 
  } 
}

// Function to monitor tweets seen based on the screen position. Whole function works in pixels
function viewCountScrollBased(sizeList,curPos,topPadding) {
  // sizeLIst is the array of all the "tweet" container sizes
  // curPos is the current position of the users screen given by the event listener, position of the top of the screen in pixels everytime they scroll
  // furthestSeen is the last tweet we have made it too and only count new reads if it is past this point. [index]
  // topPadding is the fixed size of the top bar and the first box that isnt a tweet.
  // Event listner on scroll, then call the screen postition function and pass me the current postition
  // Access the database and update how many tweets have been seen. We also need to figure out how to activate the main loop to load more tweets.

  // Main loop Ideally there will be no break, only return statements that end the function.
  //console.log("CALLED SCROLL FUNCTION");
  //for(var i=0;i<sizeList.length;i++){
  //  console.log(i + " :::: "+sizeList[i]);
  //}
  //console.log("sizeList : "+sizeList);
  //console.log("curPos : "+curPos);
  //console.log("topPadding : "+topPadding);
  var countScrollBased = 0;
   while(1){
     if(curPos < topPadding){
       countScrollBased = 0; // Set furthestSeen as zero if the screen top hasnt made it beyond the padding.
       break;
     }
     adjustedCurrPos = curPos - topPadding; // This adjusts the current position to the tweet level.
     // Check if we have passed current before adding on to the next loop
     var sumOfSeenTweets = 0;
     for(let i = 0; i < furthestSeen; i++)
       sumOfSeenTweets += sizeList[i];
     if (adjustedCurrPos <= sumOfSeenTweets){ // If we are at or before the sum of tweets before furthest seen keep the same furthest seen.
       countScrollBased = furthestSeen;
       break;
     }
     //Loop to check how many tweets we have gone through, starting from furthest seen, assuming we have already checked all previous possibilities i.e. scrolled back up and now going down again
     //sumOfSeenTweets += sizeList[furthestSeen]; // updated to current max now, if in this range we push up seen by one, subtract and remainder is greater than zero. furthest seen should be right. i was wrong, probably caused the break.
     //if(adjustedCurrPos - sumOfSeenTweets < 0){
     //  countScrollBased = furthestSeen + 1; // We are now in the middle of the tweet that was furthest seen prior to this
     //  break;
    // }
     //else{
      var found = 0;
      for(let i = furthestSeen; i < sizeList.length; i++) { // we now need to see how far our furthestSeen needs to be, adjusted +1, removed +1 since loop above was removed.
        sumOfSeenTweets += sizeList[i];
        if (adjustedCurrPos - sumOfSeenTweets < 0){
          countScrollBased = i + 1; // We have found our new furthest seen, we choose the one after the current to be the arbitrary next tweet.
          found = 1; // If found never becomes one we went to all of the tweets and all have been seen.
          break;
        }
      }
       //}
       // At this point we are past the given 20 tweets and can be unsure of what we have seen. I will put the position as 21 Which would mean all have been seen, maybe 20 will be the right thing to set.
       // however we need a better solution.
      if (found == 0){
        countScrollBased = sizeList.length + 1;
        break;
      }else{
        break;
      }
   }
  
  furthestSeen = countScrollBased;
  seen_map[furthestSeen] = 1;
  localStorage.setItem("seen_map_"+String(refreshh), seen_map); 
  console.log("COUNT SCROLL BASED : "+countScrollBased);

  if(furthestSeen >= sizeList.length-1){
    if(attn == 0){
      document.getElementById('nextarrow').style.color = "green";
      document.getElementById('nextarrow').style.cursor = "pointer";
      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
    }
  }
  //if(furthestSeen == sizeList.length){
  //  if(attn == 0){
  //    setTimeout(function(){
  //      document.getElementById('nextarrow').style.color = "green";
  //      document.getElementById('nextarrow').style.cursor = "pointer";
  //      document.getElementById('nextarrow').onclick = function() { next_arrow(); };
        //showSlides(slideIndex);
  //    },30000);
  //  }
  //}
  //if(furthestSeen == sizeList.length)
// Also must consider whether or not we must update the data base. I propose another function here below
// That is called prior to valid return statements where read status must be updated. This function may need an array with the 
// appropriate data like tweet id to find the right row in the data tables.
}

function next_arrow() {
  if (pre_attn == 1){
    if(attn == 0){
      attn = 1;
      urll = 'http://127.0.0.1:3000?access_token=' + String(access_token) + '&access_token_secret=' + String(access_token_secret) + '&worker_id=' + String(worker_id) + '&attn=' + String(attn) + '&page=' + String(page) + '&pre_attn_check=' + String(pre_attn);
      location.replace(urll);
    }
    else{
      $.ajax({
        url: "http://127.0.0.1:5050/check_attn",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({"worker_id": String(worker_id),
                "page": String(page),
                "attn_map": answers_map})        
      }).done(function(data) {
        console.log(data.check);
        console.log(data.result_map);
        result = data.check;
        result_map = data.result_map;
        tot_correct = result_map.reduce((a, b) => a + b, 0);
        if(result == "Correct"){
          console.log("CORRECT!!!");
          document.getElementById('myModal1').style.display = "block";
        }
        else if(result == "Incorrect"){
          console.log("INCORRECT!!!");
          if (page == 2){
            document.getElementById('myModal2').style.display = "block";
          }
          else{
            page = parseInt(page) + 1;
            urll = 'http://127.0.0.1:3000?access_token=' + String(access_token) + '&access_token_secret=' + String(access_token_secret) + '&worker_id=' + String(worker_id) + '&attn=' + String(attn) + '&page=' + String(page) + '&pre_attn_check=' + String(pre_attn);
            document.getElementById('pincorrect').innerHTML = "That was incorrect! You got " + String(tot_correct) + " answers wrong. You need at least 3 answers right out of 4.";
            document.getElementById('tryagainbtn').onclick = function() { location.replace(urll); };
            document.getElementById('myModal3').style.display = "block";
          }
        }
      });
    }
  }
  else{
    if (attn == 0){
      attn = 1;
    }
    else{
      attn = 0;
      page = parseInt(page) + 1;
    }
    urll = 'http://127.0.0.1:3000?access_token=' + String(access_token) + '&access_token_secret=' + String(access_token_secret) + '&worker_id=' + String(worker_id) + '&attn=' + String(attn) + '&page=' + String(page); + '&pre_attn_check=' + String(pre_attn);
    location.replace(urll);
  }
}

function plusSlides(n) {
  showSlides(slideIndex += n);
}

function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides(n) {
  var i;
  var slides = document.getElementsByClassName("mySlides");
  var dots = document.getElementsByClassName("dot");
  var modal = document.getElementById("myModal");
  if (n > slides.length) {
    modal.style.display = "none";
  }
  else{
    for (i = 0; i < slides.length; i++) {
      slides[i].style.display = "none";  
    }
    for (i = 0; i < dots.length; i++) {
      dots[i].className = dots[i].className.replace(" active", "");
    }
    slides[slideIndex-1].style.display = "block";  
    dots[slideIndex-1].className += " active";
  }
}

function logout_send_data(){
  console.log(localStorage.getItem("seen_map_"+String(refreshh)));
  console.log(localStorage.getItem("click_map_"+String(refreshh)));
  retweet_map_all = [];
  like_map_all = [];
  seen_map_all = [];
  click_map_all = [];
  for(i = 0;i<=refreshh;i++){
    retweet_map_all.push(localStorage.getItem("retweet_map_"+String(i)));
    like_map_all.push(localStorage.getItem("like_map_"+String(i)));
    seen_map_all.push(localStorage.getItem("seen_map_"+String(i)));
    click_map_all.push(localStorage.getItem("click_map_"+String(i)))
  }  
  $.ajax({
            url: "http://127.0.0.1:5052/engagements_save",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({"worker_id": String(worker_id),
              "retweet_map": retweet_map_all,
              "like_map": like_map_all,
              "seen_map": seen_map_all,
              "click_map": click_map_all
            })        
        }).done(function(data) {
            console.log(data);
            for(i = 0;i<=refreshh;i++){
              localStorage.removeItem("retweet_map_"+String(i));
              localStorage.removeItem("like_map_"+String(i));
              localStorage.removeItem("seen_map_"+String(i));
              localStorage.removeItem("click_map_"+String(i));
            }
        });
}