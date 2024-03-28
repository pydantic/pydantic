var feedback = document.forms.feedback
feedback.hidden = false

feedback.addEventListener("submit", function(ev) {
  ev.preventDefault()

  var page = document.location.pathname
  var data = ev.submitter.getAttribute("data-md-value")

  feedback.firstElementChild.disabled = true

  var note = feedback.querySelector(
    ".md-feedback__note [data-md-value='" + data + "']"
  )
  if (note)
    note.hidden = false

  var feedbackData = {
    e: 'feedback',
    feedback: data,
    page: page,
    t: (Date.now() - now).toString(),
    sc: window.pageYOffset,
    mx,
    my,
  };

  // send func available bc of flarelytics client script imported in main.html
  send(feedbackData);
})
