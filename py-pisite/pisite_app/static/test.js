var endpoints = {
    "main": "/api/power",
    "minecraft": "/api/main/mc",
    "left": "/api/main/left"
};
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
    if (typeof data != "string") {
        data = JSON.stringify(data);
    }
    if (data != null) {
        request.send(data);
    }
    else {
        request.send();
    }
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
function parseStatusResponse(id, response, statusDiv) {
    statusDiv.textContent = "Parsing...";
    switch (id) {
        case "main":
            var groupButtons = document.querySelectorAll(".group > button");
            var mainPowerButton = document.querySelector("#main > .power");
            if (response.data.is_main_connectable) { // server is up
                statusDiv.textContent = "Main Server is up!";
                // update group buttons
                updateAllGroups();
                // make server power button unclickable
                mainPowerButton.disabled = true;
            }
            else { // server not up
                if (response.data.is_main_pingable) {
                    statusDiv.textContent = "Main Server is booting up, please wait...";
                    mainPowerButton.disabled = true;
                }
                else {
                    statusDiv.textContent = "Unable to reach Main Server, it is probably off."; // make server power button clickable
                    mainPowerButton.disabled = false;
                }
                // make group buttons unclickable until main server is on
                groupButtons.forEach(function (button) {
                    button.disabled = true;
                });
            }
            break;
        case "minecraft":
            var newString = "";
            var minecraftPowerButton = document.querySelector("#minecraft > .power");
            var dynmapButton = document.querySelector("#dynmap");
            if (!response.data.any_true) { // any_true is false
                newString = "Unable to see Minecraft Server, it is probably off.";
                minecraftPowerButton.disabled = false;
                dynmapButton.disabled = true;
            }
            else if (!response.data.mc_status_ping) { // any_true but not mc_status-able
                newString = "Minecraft Server is starting up, please wait...";
                minecraftPowerButton.disabled = true;
                dynmapButton.disabled = true;
                // if (response.data.tmux_window_running) {
                //     newString += "Minecraft tmux window is open<br>";
                // }
                // if (response.data.process_running) {
                //     newString += "Minecraft java process is running<br>";
                // }
            }
            else { //mc_status-able
                newString = "Minecraft Server is up and should be joinable :)<br>";
                minecraftPowerButton.disabled = true;
                dynmapButton.disabled = false;
                if (response.data.info != null && Object.keys(response.data.info).length != 0) {
                    newString += "MOTD: " + response.data.info.motd + "<br>";
                    var players = response.data.info.players;
                    if (players.length == 0) {
                        newString += "No players online.";
                    }
                    else {
                        newString += "Players: ";
                        for (var i = 0; i < players.length; i++) {
                            newString += players[i];
                            if (i < players.length - 1) {
                                newString += ", ";
                            }
                        }
                    }
                }
            }
            statusDiv.innerHTML = newString;
            break;
        case "left":
            statusDiv.textContent = "unimplemented";
        default:
            break;
    }
}
function updateStatus(id) {
    var statusDiv = document.querySelector("#" + id + " .status");
    statusDiv.textContent = "Loading...";
    sendRequest("GET", endpoints[id], function (data) {
        // console.log(data.target.responseText);
        var response = JSON.parse(data.target.responseText);
        parseStatusResponse(id, response, statusDiv);
    });
}
function updateAllGroups() {
    for (var id in endpoints) {
        if (id == "main") {
            continue;
        }
        updateStatus(id);
        var updateButton = document.querySelector("#" + id + " .update");
        updateButton.disabled = false;
    }
}
function turnOn(id) {
    sendRequest("POST", endpoints[id], function (data) {
        var response = JSON.parse(data.target.responseText);
        if (response.success) {
            alert("Successfully booted up " + id + " :)");
            updateStatus(id);
        }
        else {
            alert("Failed to boot up " + id + " :(\nreason: " + response.message);
        }
    }, {
        "operation": "on"
    });
}
function setupGroupDiv(groupDiv) {
    var id = groupDiv.id;
    var statusDiv = document.querySelector("#" + id + " .status");
    var updateButton = document.querySelector("#" + id + " .update");
    var powerButton = document.querySelector("#" + id + " .power");
    updateStatus(id);
    updateButton.onclick = function () {
        updateStatus(id);
    };
    powerButton.onclick = function () {
        turnOn(id);
    };
}
function onLoadPage() {
    if (window.location.pathname == "/controls") {
        // URL is /controls
        // set up main server
        var mainDiv = document.querySelector("#main");
        // treat mainDiv like a groupDiv, it is set up in the same way
        setupGroupDiv(mainDiv);
        // set up all group divs
        var groupDivs = document.querySelectorAll(".group");
        groupDivs.forEach(function (groupDiv) {
            setupGroupDiv(groupDiv);
        });
        // set up dynmap button
        var dynmap = document.querySelector("#dynmap");
        dynmap.onclick = function () {
            window.open('/dynmap?zoom=3', '_blank');
        };
        // update status of main
        updateStatus("main");
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
            sendRequest("POST", "/api/logout", onLoginLogoutResponse);
            return false;
        };
    }
    catch (_a) { }
    return false;
}
// attach function to the load event
window.addEventListener("load", onLoadPage);
