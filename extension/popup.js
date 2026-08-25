const status =
    document.getElementById("status");


fetch(
    "http://127.0.0.1:8000/"
)

    .then(response => {

        if (!response.ok) {
            throw new Error();
        }

        return response.json();
    })

    .then(data => {

        status.textContent =
            "🟢 AI Server Online";

        status.classList.add(
            "online"
        );

    })

    .catch(() => {

        status.textContent =
            "🔴 AI Server Offline";

        status.classList.add(
            "offline"
        );

    });