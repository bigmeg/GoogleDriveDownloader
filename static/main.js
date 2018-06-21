(function () {
    window.onload = function () {
        let alertContainer = document.getElementById("alert-info");
        let REFRESH_INTERVAL = 1000;
        let idOfTimeout = null;
        getStatus();

        function getStatus() {
            fetch("status", {credentials: "same-origin"})
                .then(checkStatus)
                .then(JSON.parse)
                .then(renderContent)
                .then(function () {
                    idOfTimeout = setTimeout(getStatus, REFRESH_INTERVAL);
                })
                .catch(alert);
        }

        function renderContent(data) {
            let download = data.download;
            let upload = data.upload;
            $("status").innerHTML = "";

            function filler(task, cssClass, type) {
                let div = document.createElement("div");
                div.classList.add("list-group-item", "list-group-item-action", cssClass);
                div.innerText = task.status + " " + task.filename + " : " + task.completedLength + " / " + task.totalLength
                    + " @ " + task.speed + " [" + Math.round(task.progress * 1000) / 10 + "%, " + task.eta + "]";
                let x = document.createElement("button");
                $("status").appendChild(div).appendChild(x);
                x.innerText = "✖";
                x.style.float = "right";
                x.onclick = function () {
                    if (confirm("Remove task \"" + task.filename + "\" ?")) {
                        fetch("remove", {
                            credentials: "same-origin",
                            method: "POST",
                            headers: {"Content-Type": "application/json; charset=UTF-8"},
                            body: JSON.stringify({"name": task.filename, "type": type})})
                            .then(checkStatus)
                            .then(JSON.parse)
                            .then(function (response) {if (response.result !== "success") {alert(response.result);}})
                            .catch(alert);
                    }
                }
            }

            download.forEach(function (task) {filler(task, "list-group-item-info", "download")});
            upload.forEach(function (task) {filler(task, "list-group-item-success", "upload")});
        }

        $("interval-val").innerText = REFRESH_INTERVAL / 1000;

        $("interval").onchange = function () {
            clearTimeout(idOfTimeout);
            REFRESH_INTERVAL = ($("interval-val").innerText = $("interval").value) * 1000;
            idOfTimeout = setTimeout(getStatus, REFRESH_INTERVAL);
        }

        $("btn").addEventListener("click", debounce(function () {
            let data = {
                "name": document.getElementById("name").value,
                "link": document.getElementById("link").value,
                "upload": document.getElementById("upl").checked,
                "delete": document.getElementById("del").checked
            };
            if (data.name === "" || data.link === "") {
                alert("name and link field cannot be blank");
            } else {
                fetch("newtask", {
                    credentials: "same-origin",
                    body: JSON.stringify(data),
                    headers: {"Content-Type": "application/json; charset=UTF-8"},
                    method: "POST"
                })
                    .then(checkStatus)
                    .then(JSON.parse)
                    .then(function (response) {
                        if (response.result === "invalid link") alert("invalid link");
                        else if (response.result === "missing parameter") alert("missing parameter");
                        else {
                            alertContainer.insertAdjacentHTML("beforeend", "<div id=\"alert-msg\">Add new task succeed</div>");
                            alertContainer.style.display = 'inherit';
                            setTimeout(function () {
                                alertContainer.style.display = "none";
                                var msg = document.getElementById("alert-msg");
                                msg.parentNode.removeChild(msg);
                            }, 1300);
                        }
                    })
                    .catch(alert);
            }
        }, 1500, true));

        function debounce(func, wait, immediate) {
            let timeout;
            return function () {
                let context = this, args = arguments;
                let later = function () {
                    timeout = null;
                    if (!immediate) func.apply(context, args);
                };
                let callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(context, args);
            };
        };

        function checkStatus(response) {
            if (response.status >= 200 && response.status < 300) {
                return response.text();
            } else {
                return Promise.reject(new Error(response.status + ": " + response.statusText));
            }
        }

        function $(id) {
            return document.getElementById(id);
        }

    }
})();