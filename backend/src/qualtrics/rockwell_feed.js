Qualtrics.SurveyEngine.addOnload(function()
{
	/*Place your JavaScript here to run when the page loads*/
	document.getElementById("screenameinput2").value = "${e://Field/screename}";
	document.getElementById("screenameinput2").disabled = true;
	var that = this;
    this.questionclick = function(event,element) {
		var choice = that.getSelectedChoices()[0];
		if (choice == 1){

		}
		else if (choice == 2){
			
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