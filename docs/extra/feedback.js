var feedback = document.forms.feedback
feedback.hidden = false

feedback.addEventListener("submit", function(ev) {
  ev.preventDefault()

  var data = ev.submitter.getAttribute("data-md-value")

  feedback.firstElementChild.disabled = true

  var note = feedback.querySelector(
    ".md-feedback__note [data-md-value='" + data + "']"
  )
  if (note)
    note.hidden = false

  const url = new URL(window.location.href)
  const feedbackData = {
    o: url.host,
    p: url.pathname,
    a: url.hash,
    q: url.search,
    f: data,
    event_type: 'feedback',
    dt: Date.now().toString(),
  }

  // send func should be available bc of flarelytics client script imported in main.html
  send(feedbackData);
})
