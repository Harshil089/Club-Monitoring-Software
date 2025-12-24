document.addEventListener("DOMContentLoaded", function () {
    console.log("Admin Theme Toggle Script Loaded");

    const savedTheme = localStorage.getItem("admin-theme");
    const body = document.body;

    if (savedTheme === "dark") {
        body.classList.add("dark-mode");
    }

    // Attempt to find the right navbar
    // Jazzmin uses .navbar-nav.ml-auto for the right-side menu (user, etc)
    let navbarNav = document.querySelector(".navbar-nav.ml-auto");

    if (!navbarNav) {
        // Fallback: try finding any navbar-nav and take the last one
        const navs = document.querySelectorAll(".navbar-nav");
        if (navs.length > 0) {
            navbarNav = navs[navs.length - 1];
        }
    }

    if (navbarNav) {
        console.log("Navbar found, injecting toggle.");

        const li = document.createElement("li");
        li.className = "nav-item";

        const a = document.createElement("a");
        a.className = "nav-link";
        a.href = "#";
        a.title = "Toggle Light/Dark Mode";
        a.style.cursor = "pointer";

        // Icon logic
        const updateIcon = () => {
             if (body.classList.contains("dark-mode")) {
                 a.innerHTML = '<i class="fas fa-sun"></i>';
             } else {
                 a.innerHTML = '<i class="fas fa-moon"></i>';
             }
        };
        updateIcon();

        a.addEventListener("click", function (e) {
            e.preventDefault();
            console.log("Toggle clicked");

            body.classList.toggle("dark-mode");

            if (body.classList.contains("dark-mode")) {
                localStorage.setItem("admin-theme", "dark");
            } else {
                localStorage.setItem("admin-theme", "light");
            }
            updateIcon();
        });

        li.appendChild(a);
        navbarNav.prepend(li); // Prepend to put it before the user menu
    } else {
        console.error("Navbar not found for theme toggle injection.");
    }
});
