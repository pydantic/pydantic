const companies = [
  {name: 'Adobe', key: 'adobe'},
  {name: 'Amazon', key: 'amazon'},
  {name: 'Apple', key: 'apple'},
  {name: 'ASML', key: 'asml'},
  {name: 'AstraZeneca', key: 'astrazeneca'},
  {name: 'Cisco Systems', key: 'cisco'},
  {name: 'Comcast', key: 'comcast'},
  {name: 'Datadog', key: 'datadog'},
  {name: 'Facebook', key: 'facebook'},
  {name: 'Google', key: 'google'},
  {name: 'HSBC', key: 'hsbc'},
  {name: 'IBM', key: 'ibm'},
  {name: 'Intel', key: 'intel'},
  {name: 'Intuit', key: 'intuit'},
  {name: 'IPCC', key: 'ipcc'},
  {name: 'JPMorgan', key: 'jpmorgan'},
  {name: 'Jupyter', key: 'jupyter'},
  {name: 'Microsoft', key: 'microsoft'},
  {name: 'Molssi', key: 'molssi'},
  {name: 'NASA', key: 'nasa'},
  {name: 'Netflix', key: 'netflix'},
  {name: 'NSA', key: 'nsa'},
  {name: 'NVIDIA', key: 'nvidia'},
  {name: 'Oracle', key: 'oracle'},
  {name: 'Palantir', key: 'palantir'},
  {name: 'Qualcomm', key: 'qualcomm'},
  {name: 'Red Hat', key: 'redhat'},
  {name: 'Revolut', key: 'revolut'},
  {name: 'Robusta', key: 'robusta'},
  {name: 'Salesforce', key: 'salesforce'},
  {name: 'Starbucks', key: 'starbucks'},
  {name: 'Texas Instruments', key: 'ti'},
  {name: 'Twilio', key: 'twilio'},
  {name: 'Twitter', key: 'twitter'},
  {name: 'UK Home Office', key: 'ukhomeoffice'},
]

const grid = document.getElementById('company-grid');
if (grid) {
  for (const company of companies) {
    const div = document.createElement('div');
    div.classList.add('tile');
    const {key, name} = company;
    div.innerHTML = `
      <a href="why/#org-${key}" title="${name}">
        <img src="logos/${key}_logo.png" alt="${name}" />
      </a>
    `;
    grid.appendChild(div);
  }
}

async function set_download_count(el) {
  const r = await fetch('https://errors.pydantic.dev/download-count.txt');
  if (r.status === 200) {
    el.innerText = await r.text();
  }
}

const download_count = document.getElementById('download-count');
if (download_count) {
  set_download_count(download_count)
}
