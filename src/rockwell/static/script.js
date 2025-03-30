const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.3
};

const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            console.log(entry)
            console.log(`Element ${entry.target.id} is partially visible in the viewport!`);
        } else {
            console.log(`Element ${entry.target.id} is not leaving in the viewport!`);
        }
    });
}, observerOptions);
document.querySelectorAll('.tweet').forEach(tweet => observer.observe(tweet));

function linkifyText(element) {
console.log("lord")
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    console.log(element.innerHTML.match(urlRegex));
    element.innerHTML = element.innerHTML.replace(urlRegex, '<a href="$1" target="_blank" class="text-blue-600 hover:text-blue-800 underline">$1</a>');
}

document.querySelectorAll('.tweetbody').forEach(linkifyText);
