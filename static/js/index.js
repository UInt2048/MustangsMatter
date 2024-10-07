const authClient = PropelAuth.createClient({
    // The base URL where your authentication pages are hosted. You can find this under the Frontend Integration section for your project.
    authUrl: document.getElementById("auth-script").getAttribute("data-propelauth-base"),
    // If true, periodically refresh the access token in the background. This helps ensure you always have a valid token ready to go. Default true.
    enableBackgroundTokenRefresh: true,
});

console.log("Auth client initialized:", authClient);

async function whoAmI(accessToken) {
    return fetch('/api/whoami', {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
    }).then((res) => res.json())
}

// Hook up buttons to redirect to signup, login, etc
document.getElementById("signup").onclick = authClient.redirectToSignupPage;
document.getElementById("login").onclick = authClient.redirectToLoginPage;
document.getElementById("account").onclick = authClient.redirectToAccountPage;
document.getElementById("logout").onclick = authClient.logout;

function callEndpoint(endpoint) {
    // This function is dangerous!
    // Running it will run JavaScript code from the HTML returned by the endpoint
    // Credit to https://stackoverflow.com/a/47614491
    function setInnerHTML(element, html) {
        element.innerHTML = html;

        const context = {
            addGoal: addGoal,
            completeGoal: completeGoal,
            deleteGoal: deleteGoal,
            editGoal: editGoal,
            submitMessage: submitMessage
        };
        Array.from(element.querySelectorAll("script"))
            .forEach(untrusted => {
                const script = untrusted.innerHTML;
                new Function(`with (this) { return (function() { ${script} })(); }`).call(context);
                const trusted = document.createElement("script");
                untrusted.parentNode.replaceChild(trusted, untrusted);
            });
    }

    fetch(endpoint).
        then(response => response.blob()).
        then(blob => blob.text()).
        then(html => setInnerHTML(document.getElementById("authenticated"), html));
}

function addGoal(form) {
    let name = document.getElementById("name").value;
    let t = Array.from(document.getElementsByName("type")).map(x => x.checked);
    if (!t.some(x => x)) return false;
    let type = t[0] ? "physical" : "mental";
    let d = Array.from(document.getElementsByName("day")).map(x => x.checked + 0);
    if (!d.some(x => x)) return false;
    let notif = document.getElementById("notifs").checked + 0;
    let weeks = document.getElementById("weeks").value;
    callEndpoint("/add?name=" + name + "&type=" + type + "&d0=" + d[0] +
       "&d1=" + d[1] + "&d2=" + d[2] + "&d3=" + d[3] + "&d4=" + d[4] + "&d5=" + d[5] + "&d6=" + d[6] +
       "&notifs=" + notif + "&weeks=" + weeks);
    return false;
}

function completeGoal(goalId) {
    return (function(form) {
        callEndpoint("/complete?goal=" + goalId);
    });
}

function deleteGoal(goalId) {
    return (function(form) {
        callEndpoint("/delete?goal=" + goalId);
    });
}

function editGoal(goalId) {
    return (function(form) {
        let name = document.getElementById("name-" + goalId).value;
        let notif = document.getElementById("notifs-" + goalId).checked + 0;
        callEndpoint("/edit?id=" + goalId + "&name=" + name + "&notifs=" + notif);
        return false;
    });
}

function submitMessage(form) {
    callEndpoint("/message?text=" + document.getElementById("chatmsg").value);
}

// When the logged in status changes, display one of the divs
authClient.addLoggedInChangeObserver((isLoggedIn) => {
    if (isLoggedIn) {
        document.getElementById("display-when-logged-in").style.display = "revert";
        document.getElementById("display-when-logged-out").style.display = "none";

        // Get authentication info and set email to it
        authClient.getAuthenticationInfoOrNull()
            .then(authInfo => {
                if (authInfo?.user !== null) {
                    let user = authInfo.user;
                    document.getElementById("email").innerText = user.email;
                    callEndpoint("/login?id=" + user.userId +
                        "&email=" + user.email +
                        "&name=" + user.firstName)
                } else {
                    fetch("/logout")
                }
            });
    } else {
        document.getElementById("display-when-logged-in").style.display = "none";
        document.getElementById("display-when-logged-out").style.display = "revert";
        fetch("/logout")
    }
});

(async () => {
    const authInfo = await authClient.getAuthenticationInfoOrNull(true);
    if (authInfo) {
        console.log("User is logged in as", authInfo.user.email);
        return await whoAmI(authInfo.accessToken)
    } else {
        console.log("User is not logged in");
    }
})();
