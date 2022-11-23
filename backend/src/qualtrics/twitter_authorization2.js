Qualtrics.SurveyEngine.addOnload(function()
{
	/*Place your JavaScript here to run when the page loads*/
	document.getElementById("screenameinput").value = "${e://Field/screename}";
	document.getElementById("screenameinput").disabled = true;
	this.hideNextButton();
	this.hidePreviousButton();
	var that = this;
    this.questionclick = function(event,element) {
		var choice = that.getSelectedChoices()[0];
		if (choice == 1){
			jQuery("#NextButton").show();
			this.hidePreviousButton();
			document.getElementById("incorrect").hidden = true;
		}
		else if (choice == 2){
			this.hideNextButton();
			this.showPreviousButton();
			document.getElementById("incorrect").hidden = false;
		}
	}
});
Qualtrics.SurveyEngine.addOnReady(function()
{
	/*Place your JavaScript here to run when the page is fully displayed*/
});
Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});