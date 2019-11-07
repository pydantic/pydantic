function main () {
  const ad_el = document.getElementById('bsa-cpc')
  if (!ad_el) {
    // if no ad element, don't load buysellads
    return
  }
  const script = document.createElement('script')
  script.onload = () => {
    _bsa.init('default', 'CKYDVKJJ', 'placement:helpmanualio', {
      target: '#bsa-cpc',
      align: 'horizontal',
    })
    ad_el.classList.add('loaded')
  }
  script.src = 'https://m.servedby-buysellads.com/monetization.js'
  document.head.appendChild(script)
}

main()
