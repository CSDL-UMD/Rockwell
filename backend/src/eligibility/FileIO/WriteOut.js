const fs = require('fs');
var path = require('path');

const writeOut = async (writeObject, twitterId) => {
    let jsonPath = path.join(__dirname, '..', 'User_Data', twitterId + '.json');
    fs.writeFile(jsonPath,JSON.stringify(writeObject, null, 4), function (err,data) {
        if (err) {
          return console.log(err);
        }
        console.log(data);
      });
};

module.exports = writeOut;