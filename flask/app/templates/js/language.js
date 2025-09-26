const body = document.body;
const languageSwitch = document.getElementById('language-switch');
const spans = languageSwitch.getElementsByTagName('span');

const savedLang = localStorage.getItem('language') || 'en';
setLanguage(savedLang);

languageSwitch.addEventListener('click', () => {
  const currentLang = body.classList.contains('th') ? 'th' : 'en';
  const newLang = currentLang === 'th' ? 'en' : 'th';
  setLanguage(newLang);
});

function setLanguage(lang) {
  if (lang === 'th') {
    body.classList.remove('en');
    body.classList.add('th');
  } else {
    body.classList.remove('th');
    body.classList.add('en');
  }

  localStorage.setItem('language', lang);
  changeLanguage(lang);
}

function changeLanguage(lang) {
  console.log('Language changed to:', lang);
  if (lang === 'en') {
    document.querySelector('.welcome-message').textContent = 'Welcome!';
    document.querySelector('.search-input').placeholder = 'Search';
    document.querySelector('.action1').textContent = 'Stock';
    document.querySelector('.action2').textContent = 'QR Scan';
    document.querySelector('.action3').textContent = 'Manage Admin';
  } else {
    document.querySelector('.welcome-message').textContent = 'ยินดีต้อนรับ!';
    document.querySelector('.search-input').placeholder = 'ค้นหา';
    document.querySelector('.action1').textContent = 'สต็อก';
    document.querySelector('.action2').textContent = 'QR แสกน';
    document.querySelector('.action3').textContent = 'จัดการแอดมิน';
  }
}
