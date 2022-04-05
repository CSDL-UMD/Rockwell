const fs = require('fs');
var path = require('path');
const zlib = require('zlib');

const writeOut = async (writeObject, twitterId) => {
  let jsonPath = path.join(__dirname, '..', 'User_Data', twitterId + '.json');
  fs.writeFileSync(jsonPath, JSON.stringify(writeObject, null, 4), function (err, data) {
    if (err) {
      return console.log(err);
    }
    /*
    const fileContents = fs.createReadStream(jsonPath);
    const zip = zlib.createGzip();
    let jsonPathZip = path.join(__dirname, '..', 'User_Data', twitterId + '.json.gz');
    const writeStream = fs.createWriteStream(jsonPathZip);

    fileContents.pipe(zip).pipe(writeStream).on('finish', (err) => {
      if (err)
        return console.log(err);
        
      // Close file streams
      fileContents.destroy();
      writeStream.destroy();

      // Attempt to delete file
    }).on('close', function (err) { // further test this
      fs.unlink(jsonPath, (err) => {
        if (err) return console.log(err);
      });
  });;
  */
  });

};

module.exports = writeOut;