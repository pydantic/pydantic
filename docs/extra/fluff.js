// set the download count in the "why pydantic" page
(async function() {
  const downloadCount = document.getElementById('download-count');
  if (downloadCount) {
    const r = await fetch('https://errors.pydantic.dev/download-count.txt');
    if (r.status === 200) {
      downloadCount.innerText = await r.text();
    }
  }
})();

// update the announcement banner to change the app type
(function() {
  const el = document.getElementById('logfire-app-type');
  const appTypes = [
    ['/integrations/pydantic/', 'Pydantic validations.'],
    ['/integrations/fastapi/', 'FastAPI app.'],
    ['/integrations/openai/', 'OpenAI integration.'],
    ['/integrations/asyncpg/', 'Postgres queries.'],
    ['/integrations/redis/', 'Task Queue.'],
    ['/integrations/system-metrics/', 'System Metrics.'],
    ['/integrations/httpx/', 'API Calls.'],
    ['/integrations/logging/', 'Std lib logging.'],
    ['/integrations/django/', 'Django app.'],
    ['/integrations/anthropic/', 'Anthropic API calls.'],
    ['/integrations/fastapi/', 'Flask app.'],
    ['/integrations/mysql/', 'MySQL queries.'],
    ['/integrations/sqlalchemy/', 'SqlAlchemy queries.'],
    ['/integrations/structlog/', 'Structlog logs.'],
    ['/integrations/stripe/', 'Stripe API calls.'],
  ];
  const docsUrl = 'https://logfire.pydantic.dev/docs';
  let counter = 0;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const replaceText = async () => {
    const text = el.textContent;
    for (let i = text.length; i >= 0; i--) {
      el.textContent = text.slice(0, i);
      await sleep(20);
    }
    await sleep(50);
    counter++;
    // change the link halfway through the animation
    const [link, newText] = appTypes[counter % appTypes.length];
    el.href = docsUrl + link;
    await sleep(50);
    for (let i = 0; i <= newText.length; i++) {
      el.textContent = newText.slice(0, i);
      await sleep(30);
    }
  };
  setInterval(replaceText, 3000);
})();
