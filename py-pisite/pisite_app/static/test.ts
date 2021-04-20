
function formToStringifiedJSON(form: HTMLFormElement): string {
    const formData = new FormData(form);
    let data = {};   
    formData.forEach((value, key) => data[key] = value);
    let stringified = JSON.stringify(data);
    return stringified;
}

function sendRequest(method: "GET" | "POST", url: string, onload, data: string) {
    let request = new XMLHttpRequest();
    request.open(method, url);
    request.onload = onload;
    request.setRequestHeader("Content-Type", "application/json");
    request.overrideMimeType("application/json");
    request.send(data);
    
    console.log("sent request: " + method + " " + url + " " + data);
}

function onControlsResponse() {
    const status: HTMLElement = document.getElementById("status");
    const result: HTMLElement = document.getElementById("result");

    // response is the actual JSON object 
    // responseText is the stringified version (a string)
    console.log("response is: " + this.responseText);
    const response = JSON.parse(this.responseText);

    status.textContent = "done :)";
    result.textContent = this.responseText;
    
    console.log("done with onControlsResponse");

    return false;
}

function onLoginLogoutResponse() {
    console.log("response is: " + this.responseText);
    const response = JSON.parse(this.responseText);

    if (response.success) {
        // navigate to homepage
        window.location.href = window.location.origin;
    }
    return false;
}

function onLoadPage() {
    if (window.location.pathname == "/controls") {
        // URL is /controls
        const inputForm: HTMLFormElement = document.querySelector("#userInput");

        inputForm.onsubmit = () => {
            const status: HTMLElement = document.getElementById("status");
            const result: HTMLElement = document.getElementById("result");

            status.textContent = "loading...";
            result.textContent = "";

            sendRequest("POST", "/api/test", onControlsResponse, formToStringifiedJSON(inputForm));

            return false;
        }
    } else if (window.location.pathname == "/login") {
        // URL is /login
        const loginForm: HTMLFormElement = document.querySelector("#loginForm");
        loginForm.onsubmit = () => {
            sendRequest("POST", "/api/login", onLoginLogoutResponse, formToStringifiedJSON(loginForm));
            return false;
        }
    }
    // for all URLs
    try { // this only runs if the logout button exists
        const logoutElement: HTMLAnchorElement = document.querySelector("#logout");
        logoutElement.onclick = () => {
            console.log("logging out");
            sendRequest("POST", "/api/logout", onLoginLogoutResponse, null);
            return false;
        }
    } catch {}

    return false;
}

// attach function to the load event
window.addEventListener("load", onLoadPage);