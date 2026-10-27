
const emergencyForm = document.getElementById("emergencyForm");
const formResult = document.getElementById("formResult");

emergencyForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const submitButton = emergencyForm.querySelector(
        'button[type="submit"]'
    );

    const payload = {
        name: document.getElementById("patientName").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        type: document.getElementById("emergencyType").value,
        symptoms: document.getElementById("symptoms").value.trim(),
        location: document.getElementById("location").value.trim()
    };

    if (!emergencyForm.reportValidity()) {
        return;
    }

    formResult.textContent = "Saving your demo request...";
    formResult.style.color = "#334155";
    submitButton.disabled = true;

    try {
        const response = await fetch("/api/emergencies", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const responseText = await response.text();

let result;

try {
    result = JSON.parse(responseText);
} catch {
    console.error("Invalid server response:", responseText);
    throw new Error(
        "The server returned an invalid response. Check the Flask terminal."
    );
}

        if (!response.ok) {
            throw new Error(
                result.error || "Could not save the request."
            );
        }

        formResult.replaceChildren();

        const heading = document.createElement("h3");
        heading.textContent = "Demo Request Saved Successfully!";

        const idLine = document.createElement("p");
        idLine.textContent = "Request ID: " + result.request_id;

        const typeLine = document.createElement("p");
        typeLine.textContent =
            "Emergency Type: " + result.emergency_type;

        const statusLine = document.createElement("p");
        statusLine.textContent = "Status: " + result.status;

        const note = document.createElement("p");
        note.textContent =
            "Saved to the local SQLite database. No ambulance has been contacted.";

        formResult.append(
            heading, idLine, typeLine, statusLine, note
        );

        formResult.style.color = "#166534";

        // Keep personal details out of the browser console.
    } catch (error) {
        formResult.textContent =
            error.message || "Unable to connect to the server.";
        formResult.style.color = "#b91c1c";
    } finally {
        submitButton.disabled = false;
    }
});