document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const themeToggle = document.querySelector("#theme-toggle");
    const themeIcon = document.querySelector("[data-theme-icon]");

    // Restore the saved color scheme on every page.
    function setTheme(theme) {
        root.dataset.theme = theme;
        if (themeToggle) {
            const isDark = theme === "dark";
            themeToggle.setAttribute("aria-pressed", String(isDark));
            themeToggle.setAttribute(
                "aria-label",
                isDark ? "Switch to light mode" : "Switch to dark mode"
            );
        }
        if (themeIcon) {
            themeIcon.classList.toggle("bi-moon-stars-fill", theme !== "dark");
            themeIcon.classList.toggle("bi-sun-fill", theme === "dark");
        }
    }

    setTheme(localStorage.getItem("staffAttendanceTheme") === "dark" ? "dark" : "light");

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
            localStorage.setItem("staffAttendanceTheme", nextTheme);
            setTheme(nextTheme);
        });
    }

    const passwordInput = document.querySelector("#password");
    const toggleButton = document.querySelector(".password-toggle");

    if (passwordInput && toggleButton) {
        toggleButton.addEventListener("click", () => {
            const showPassword = passwordInput.type === "password";
            passwordInput.type = showPassword ? "text" : "password";
            toggleButton.setAttribute("aria-pressed", String(showPassword));
            toggleButton.setAttribute(
                "aria-label",
                showPassword ? "Hide password" : "Show password"
            );
            toggleButton.innerHTML = showPassword
                ? '<i class="bi bi-eye-slash" aria-hidden="true"></i>'
                : '<i class="bi bi-eye" aria-hidden="true"></i>';
        });
    }

    const clock = document.querySelector("[data-live-clock]");
    const timer = document.querySelector("[data-start-time]");
    const startTimeText = timer ? timer.dataset.startTime : null;
    const staffSearch = document.querySelector("#staff-search");

    if (staffSearch) {
        staffSearch.addEventListener("input", () => {
            const query = staffSearch.value.trim().toLowerCase();
            document.querySelectorAll(".staff-row").forEach((row) => {
                const text = row.dataset.staffSearch || "";
                row.hidden = !text.includes(query);
            });
        });
    }

    document.querySelectorAll("[data-toast-message]").forEach((toastElement) => {
        bootstrap.Toast.getOrCreateInstance(toastElement).show();
    });

    document.querySelectorAll("[data-bs-title]").forEach((tooltipElement) => {
        bootstrap.Tooltip.getOrCreateInstance(tooltipElement);
    });

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (event.defaultPrevented) return;
            if (form.dataset.submitting === "true") {
                event.preventDefault();
                return;
            }

            const submitButton = event.submitter;
            if (!submitButton || submitButton.disabled) return;

            // Disable repeat submissions while the request is being sent.
            form.dataset.submitting = "true";
            submitButton.disabled = true;
            submitButton.setAttribute("aria-busy", "true");

            const spinner = document.createElement("span");
            spinner.className = "spinner-border spinner-border-sm me-2";
            spinner.setAttribute("aria-hidden", "true");

            const label = document.createElement("span");
            label.textContent = submitButton.dataset.loadingLabel || "Please wait...";
            submitButton.replaceChildren(spinner, label);
        });
    });

    function kolkataTimeParts() {
        const parts = new Intl.DateTimeFormat("en-GB", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hourCycle: "h23",
        }).formatToParts(new Date());
        const values = {};
        parts.forEach((part) => {
            if (part.type !== "literal") values[part.type] = Number(part.value);
        });
        return values;
    }

    function secondsInDay(parts) {
        return (parts.hour * 3600) + (parts.minute * 60) + parts.second;
    }

    function updateClock() {
        if (clock) {
            clock.textContent = new Intl.DateTimeFormat("en-IN", {
                timeZone: "Asia/Kolkata",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            }).format(new Date());
        }

        if (timer && startTimeText) {
            const startParts = startTimeText.split(":").map(Number);
            if (startParts.length !== 3 || startParts.some(Number.isNaN)) return;
            const startSeconds = (startParts[0] * 3600) + (startParts[1] * 60) + startParts[2];
            const elapsed = Math.max(0, secondsInDay(kolkataTimeParts()) - startSeconds);
            const hours = String(Math.floor(elapsed / 3600)).padStart(2, "0");
            const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
            const seconds = String(elapsed % 60).padStart(2, "0");
            timer.textContent = `${hours}:${minutes}:${seconds}`;
        }
    }

    updateClock();
    window.setInterval(updateClock, 1000);
});
