document.addEventListener("DOMContentLoaded", () => {
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
    const startTime = timer ? new Date(timer.dataset.startTime) : null;

    function updateClock() {
        if (clock) {
            clock.textContent = new Date().toLocaleTimeString();
        }

        if (timer && startTime) {
            if (Number.isNaN(startTime.getTime())) {
                timer.textContent = "Unavailable";
                return;
            }
            const elapsed = Math.max(0, Math.floor((Date.now() - startTime.getTime()) / 1000));
            const hours = String(Math.floor(elapsed / 3600)).padStart(2, "0");
            const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
            const seconds = String(elapsed % 60).padStart(2, "0");
            timer.textContent = `${hours}:${minutes}:${seconds}`;
        }
    }

    updateClock();
    window.setInterval(updateClock, 1000);
});
