const langSwitch = document.getElementById("language-switch");
const langs = langSwitch.querySelectorAll(".lang");

langSwitch.addEventListener("click", () => {
  langs.forEach(span => span.classList.toggle("active"));
  
  const currentLang = document.querySelector("#language-switch .active").innerText;
  console.log("Current language:", currentLang)
  
});