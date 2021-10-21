
const getImageHeightRatio = (width) => {
    if (width > 800)
      return 0.65;
    if (width > 500)
      return 0.60;
    else
      return 0.60;
  }

const getTweetSizes = () => {
    const newSizes = [];
    let res = document.getElementsByClassName('completeTweet');
    Object.keys(res).forEach(tweet => {
        newSizes.push(res[tweet].clientHeight);
    });
    return newSizes;
};

const handleTotalResize = () => {
    let res = document.getElementsByClassName('TweetImage');
    Object.keys(res).forEach(image => {
        res[image].height = res[image].width * getImageHeightRatio(res[image].width);
    });
    return getTweetSizes();
};

export default handleTotalResize;