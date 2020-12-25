#! /usr/bin/env node

console.log('Started data loading script !!');


var async = require('async')
var Actor = require('./models/Actor.js');
var Script = require('./models/Script.js');
var Notification = require('./models/Notification.js');
const _ = require('lodash');
const dotenv = require('dotenv');
var mongoose = require('mongoose');
var fs = require('fs')
const CSVToJSON = require("csvtojson");
//input files
/********
TODO:
Use CSV files instead of json files
use a CSV file reader and use that as input
********/
var actors_list
var posts_list
var comment_list
var notification_list
var notification_reply_list

//dotenv.config({ path: '.env' });
dotenv.config({ path: '.env.example' });

var MongoClient = require('mongodb').MongoClient
    , assert = require('assert');


//var connection = mongo.connect('mongodb://127.0.0.1/test');

mongoose.connect(process.env.MONGODB_URI || process.env.MONGOLAB_URI, { useNewUrlParser: true });
var db = mongoose.connection;
mongoose.connection.on('error', (err) => {
    console.error(err);
    console.log('%s MongoDB connection error. Please make sure MongoDB is running.');
    process.exit(1);
});

/*
This is a huge function of chained promises, done to achieve serial completion of asynchronous actions.
There's probably a better way to do this, but this worked.
*/
async function doPopulate() {
  /****
  Dropping collections
  ****/
  let promise = new Promise((resolve, reject) => { //Drop the actors collection
    console.log("Dropping actors...");
    db.collections['actors'].drop(function (err) {
        console.log('actors collection dropped');
        resolve("done");
      });
    }).then(function(result){ //Drop the scripts collection
      return new Promise((resolve, reject) => {
        console.log("Dropping scripts...");
        db.collections['scripts'].drop(function (err) {
            console.log('scripts collection dropped');
            resolve("done");
          });
      });
    }).then(function(result){ //Drop the notifications collection
      return new Promise((resolve, reject) => {
        console.log("Dropping notifications...");
        db.collections['notifications'].drop(function (err) {
            console.log('notifications collection dropped');
            resolve("done");
          });
      });
    /***
    Converting CSV files to JSON
    ***/
    }).then(function(result){ //Convert the actors csv file to json, store in actors_list
      return new Promise((resolve, reject) => {
        console.log("Reading actors list...");
        CSVToJSON().fromFile('./input/actors_twitter_demo.csv').then(function(json_array){
          actors_list = json_array;
          console.log("Finished getting the actors_list");
          resolve("done");
        });
      });
    }).then(function(result){ //Convert the posts csv file to json, store in posts_list
      return new Promise((resolve, reject) => {
        console.log("Reading posts list...");
        CSVToJSON().fromFile('./input/posts_twitter_demo.csv').then(function(json_array){
          posts_list = json_array;
          console.log("Finished getting the posts list");
          resolve("done");
        });
      });
    }).then(function(result){ //Convert the comments csv file to json, store in comment_list
      return new Promise((resolve, reject) => {
        console.log("Reading comment list...");
        CSVToJSON().fromFile('./input/replies.csv').then(function(json_array){
          comment_list = json_array;
          console.log("Finished getting the comment list");
          resolve("done");
        });
      });
    }).then(function(result){ //Convert the comments csv file to json, store in comment_list\
      return new Promise((resolve, reject) => {
        console.log("Reading notification list...");
        CSVToJSON().fromFile('./input/notifications.csv').then(function(json_array){
          notification_list = json_array;
          console.log("Finished getting the notification list");
          resolve("done");
        });
      });
    }).then(function(result){ //Convert the notification reply csv file to json, store in comment_list\
      return new Promise((resolve, reject) => {
        console.log("Reading notification reply list...");
        CSVToJSON().fromFile('./input/actor_replies.csv').then(function(json_array){
          notification_reply_list = json_array;
          console.log("Finished getting the notification reply list");
          resolve("done");
        });
      });
    /*************************
    Create all the Actors in the simulation
    Must be done before creating any other instances
    *************************/
  }).then(function(result){
        console.log("starting to populate actors...");
        return new Promise((resolve, reject) => {
          async.each(actors_list, function (actor_raw, callback) {
              actordetail = {};
              actordetail.profile = {};

              actordetail.profile.name = actor_raw.name
              actordetail.profile.location = actor_raw.location;
              actordetail.profile.picture = actor_raw.picture;
              actordetail.profile.bio = actor_raw.bio;
              actordetail.profile.age = actor_raw.age;
              actordetail.class = actor_raw.class;
              actordetail.username = actor_raw.username;

              var actor = new Actor(actordetail);

              actor.save(function (err) {
                  if (err) {
                      console.log("Something went wrong!!!");
                      return -1;
                  }
                  console.log('New Actor: ' + actor.username);
                  callback();
              });
          },
          function (err) {
              //return response
              console.log("All DONE WITH ACTORS!!!")
              resolve("done");
              return 'Loaded Actors'
          }
        );
      });
    /*************************
    Create each post and upload it to the DB
    Actors must be in DB first to add them correctly to the post
    *************************/
    }).then(function(result){
          console.log("starting to populate posts...");
          return new Promise((resolve, reject) => {
            async.each(posts_list, function (new_post, callback) {
                Actor.findOne({ username: new_post.actor }, (err, act) => {
                    if (err) { console.log("createPostInstances error"); console.log(err); return; }
                    if (act) {
                        var postdetail = new Object();

                        postdetail.likes =  new_post.likes;
                        postdetail.urls =  new_post.urls;
                        postdetail.expanded_urls =  new_post.expanded_urls;
                        postdetail.experiment_group = new_post.experiment_group
                        postdetail.post_id = new_post.id;
                        postdetail.tweet_id = new_post.tweet_id;
                        postdetail.body = new_post.body;
                        postdetail.class = new_post.class;
                        postdetail.picture = new_post.picture;
                        postdetail.picture_heading = new_post.pictures_title
                        postdetail.picture_description = new_post.pictures_description
                        postdetail.lowread = getReads(6, 20);
                        postdetail.highread = getReads(145, 203);
                        postdetail.actor = act;
                        postdetail.time = timeStringToNum(new_post.time);
                        //postdetail.image = new_post.image; // THIS IS MY NEW CODE TO GET THE IMAGES
                       // postdetail.embeded = new_post.embeded_image; // ALSO NEW
                        var script = new Script(postdetail);
                        script.save(function (err) {
                            if (err) {
                                console.log("Something went wrong in Saving POST!!!");
                                callback(err);
                            }
                            console.log('Saved New Post: ' + script.id);
                            callback();
                        });
                    }
                    else {
                        //Else no ACTOR Found
                        console.log("No Actor Found!!!");
                        callback();
                    }
                });
              },
              function (err) {
                  if (err) {
                      console.log("END IS WRONG!!!");
                      callback(err);
                  }
                  //return response
                  console.log("All DONE WITH POSTS!!!")
                  resolve("done");
                  return 'Loaded Posts'
              }
            );
        });
  });
//Done!
}

//capitalize a string
String.prototype.capitalize = function () {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

//usuful when adding comments to ensure they are always in the correct order
//(based on the time of the comments)
function insert_order(element, array) {
    array.push(element);
    array.sort(function (a, b) {
        return a.time - b.time;
    });
    return array;
}

//Transforms a time like -12:32 (minus 12 minutes and 32 seconds)
//into a time in milliseconds
function timeStringToNum(v) {
    var timeParts = v.split(":");
    if (timeParts[0] == "-0")
        return -1 * parseInt(((timeParts[0] * (60000 * 60)) + (timeParts[1] * 60000)), 10);
    else if (timeParts[0].startsWith('-'))
        return parseInt(((timeParts[0] * (60000 * 60)) + (-1 * (timeParts[1] * 60000))), 10);
    else
        return parseInt(((timeParts[0] * (60000 * 60)) + (timeParts[1] * 60000)), 10);
};

//create a radom number (for likes) with a weighted distrubution
//this is for posts
function getLikes() {
    var notRandomNumbers = [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 6];
    var idx = Math.floor(Math.random() * notRandomNumbers.length);
    return notRandomNumbers[idx];
}

function randomIntFromInterval(min, max) {
    return Math.floor(Math.random() * (max - min + 1) + min);
}

//create a radom number (for likes) with a weighted distrubution
//this is for comments
function getLikesComment() {
    var notRandomNumbers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 3, 4];
    var idx = Math.floor(Math.random() * notRandomNumbers.length);
    return notRandomNumbers[idx];
}

//Create a random number between two values (like when a post needs a number of times it has been read)
function getReads(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min)) + min; //The maximum is exclusive and the minimum is inclusive
}

//Call the function with the long chain of promises
doPopulate();
