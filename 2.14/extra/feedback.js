var feedback = document.forms.feedback
feedback.hidden = false

feedback.addEventListener("submit", function(ev) {
  ev.preventDefault()

  var data = ev.submitter.getAttribute("data-md-value")
  feedback.firstElementChild.disabled = true

  var note = feedback.querySelector(
    `.md-feedback__note [data-md-value='${data}']`
  )
  if (note)
    note.hidden = false

  if (data == 1) {
    window.flarelytics_event('thumbsUp');
  } else if (data == 0) {
    window.flarelytics_event('thumbsDown');
  }
})
