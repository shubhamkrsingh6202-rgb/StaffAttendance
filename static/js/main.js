document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.querySelector("#password");
    const toggleButton = document.querySelector(".password-toggle");

    if (!passwordInput || !toggleButton) {
        return;
    }

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
});
