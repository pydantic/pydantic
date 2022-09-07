function main () {
  const ad_el = document.getElementById('bsa-cpc')
  if (!ad_el || innerWidth < 800) {
    // if no ad element or element hidden, don't load buysellads
    return
  }
  const script = document.createElement('script')
  script.onload = () => {
    if (_bsa.isMobile()) {
      // bsa doesn't show ads on mobile, hide th box
      ad_el.remove()
      return
    }
    _bsa.init('default', 'CK7ITKJU', 'placement:pydantic-docshelpmanualio', {
      target: '#bsa-cpc',
      align: 'horizontal',
    })
    ad_el.classList.add('loaded')
  }
  script.src = 'https://m.servedby-buysellads.com/monetization.js'
  document.head.appendChild(script)
}

// ads disabled for now
// main()
