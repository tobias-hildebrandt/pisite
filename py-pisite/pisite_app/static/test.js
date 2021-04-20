function formToStringifiedJSON(form) {
    var formData = new FormData(form);
    var data = {};
    formData.forEach(function (value, key) { return data[key] = value; });
    var stringified = JSON.stringify(data);
    return stringified;
}
function sendRequest(method, url, onload, data) {
    var request = new XMLHttpRequest();
    request.open(method, url);
    request.onload = onload;
    request.setRequestHeader("Content-Type", "application/json");
    request.overrideMimeType("application/json");
    request.send(data);
    console.log("sent request: " + method + " " + url + " " + data);
}
function onControlsResponse() {
    var status = document.getElementById("status");
    var result = document.getElementById("result");
    // response is the actual JSON object 
    // responseText is the stringified version (a string)
    console.log("response is: " + this.responseText);
    var response = JSON.parse(this.responseText);
    status.textContent = "done :)";
    result.textContent = this.responseText;
    console.log("done with onControlsResponse");
    return false;
}
function onLoginLogoutResponse() {
    console.log("response is: " + this.responseText);
    var response = JSON.parse(this.responseText);
    if (response.success) {
        // navigate to homepage
        window.location.href = window.location.origin;
    }
    return false;
}
function onLoadPage() {
    if (window.location.pathname == "/controls") {
        // URL is /controls
        var inputForm_1 = document.querySelector("#userInput");
        inputForm_1.onsubmit = function () {
            var status = document.getElementById("status");
            var result = document.getElementById("result");
            status.textContent = "loading...";
            result.textContent = "";
            sendRequest("POST", "/api/test", onControlsResponse, formToStringifiedJSON(inputForm_1));
            return false;
        };
    }
    else if (window.location.pathname == "/login") {
        // URL is /login
        var loginForm_1 = document.querySelector("#loginForm");
        loginForm_1.onsubmit = function () {
            sendRequest("POST", "/api/login", onLoginLogoutResponse, formToStringifiedJSON(loginForm_1));
            return false;
        };
    }
    // for all URLs
    try { // this only runs if the logout button exists
        var logoutElement = document.querySelector("#logout");
        logoutElement.onclick = function () {
            console.log("logging out");
            sendRequest("POST", "/api/logout", onLoginLogoutResponse, null);
            return false;
        };
    }
    catch (_a) { }
    return false;
}
window.addEventListener("load", onLoadPage);
/*
function formToJSONString(form: HTMLFormElement) : string {
    let formData = new FormData(form);

    let data: object = {};
    formData.forEach((value, key) => data[key] = value);

    let stringified: string = JSON.stringify(data);

    return stringified;
}

function sendJSONRequest(method: string, url: string, loadEventListener, data: string) {
    let request = new XMLHttpRequest();
    request.open(method, url);
    request.addEventListener("load", loadEventListener);
    request.setRequestHeader("Content-Type", "application/json");
    request.overrideMimeType("application/json");
    request.send(data);
}

function onLoginResponse() {
    // const response: object = JSON.parse(this.responseText);

    console.log("login response: " + this.responseText)

    return false;
}

function onControlResponse() {
    const status: HTMLElement = document.getElementById("status");
    status.textContent = "done :)";

    let result: HTMLElement = document.getElementById("result");

    // response is the actual JSON object
    // responseText is the stringified version (a string)
    console.log("response is: " + this.responseText);

    const response = JSON.parse(this.responseText);

    result.textContent = this.responseText;

    console.log("done with onResponse");

    return false;
}

function onLoadPage() {
    console.log("pathname:" + window.location.pathname)
    
    if (window.location.pathname == "/login") {
        // Login page
        console.log("on login page");
        const loginForm: HTMLFormElement = document.querySelector("#loginForm");
        loginForm.onsubmit = () => {
            let data = formToJSONString(loginForm);
            console.log("data: " + data);
            // sendJSONRequest("POST", "/api/login", onLoginResponse, data);
            let request = new XMLHttpRequest();
            request.open("POST", "/api/login/");
            request.addEventListener("load", onLoginResponse);
            request.setRequestHeader("Content-Type", "application/json");
            request.overrideMimeType("application/json");
            request.send(data);
            
            console.log("sent login request");
        }
    }
    else if (window.location.pathname == "/controls") {
        // Controls page
        console.log("on controls page");
        const inputForm: HTMLFormElement = document.querySelector("#userInput");
        inputForm.onsubmit = () => {
            const status: HTMLElement = document.getElementById("status");
            status.textContent = "loading...";

            let result: HTMLElement = document.getElementById("result");

            result.textContent = "";

            let data = formToJSONString(inputForm);
            sendJSONRequest("POST", "/api/test", onControlResponse, data);

            console.log("done with sending request");
        }
    }

    return false;
}

window.addEventListener("load", onLoadPage);
*/ 
