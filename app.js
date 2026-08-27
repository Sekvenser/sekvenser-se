const TABS = ["om", "webbshop", "kontakt", "lankar"];
const DEFAULT_TAB = "om";

function loadPublitWebshop() {
  if (document.querySelector('script[src="https://webshop.publit.com/publit-webshop-1.0.js"]')) return;
  const script = document.createElement("script");
  script.async = true;
  script.setAttribute("loading", "lazy");
  script.src = "https://webshop.publit.com/publit-webshop-1.0.js";
  script.text = '\n{\n  "id": "5659",\n  "sortBy": "priority:desc"\n}\n';
  document.getElementById("publit-webshop-root").appendChild(script);
}

function route() {
  const tab = TABS.includes(location.hash.slice(2)) ? location.hash.slice(2) : DEFAULT_TAB;
  TABS.forEach((t) => {
    document.getElementById(`panel-${t}`).classList.toggle("active", t === tab);
    document.querySelector(`.toolbar a[data-tab="${t}"]`).classList.toggle("active", t === tab);
  });
  if (tab === "webbshop") loadPublitWebshop();
}

window.addEventListener("hashchange", route);
route();
