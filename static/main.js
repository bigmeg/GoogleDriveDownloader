var alertContainer = document.getElementById("alert-info");
var btn = document.getElementById("btn");

var socket = io.connect('http://' + document.domain + ':' + location.port + '/api');
socket.on('newdata', function (msg) {
    renderContent(msg);
});



function renderContent(data) {
    var download = data.download;
    var upload = data.upload;
    var error = data.error;

    var htmlString = '';
    var producer = function (rs) {
        return rs.status + " " + rs.filename + " : " + rs.completed_size + " / " + rs.file_size + " @ " + rs.speed +
            " [" + Math.round(rs.progress * 1000) / 10 + "%, " + rs.eta + "]</a>";
    }

    for (var i = 0; i < download.length; i++) {
        var rs = download[i];
        htmlString += "<a class=\"list-group-item list-group-item-action list-group-item-info\">" + producer(rs);
    }

    for (var i = 0; i < upload.length; i++) {
        var rs = upload[i];
        htmlString += "<a class=\"list-group-item list-group-item-action list-group-item-success\">" + producer(rs);
    }

    for (var i = 0; i < error.length; i++) {
        var rs = error[i];
        htmlString += "<a class=\"list-group-item list-group-item-action list-group-item-danger\">" +
            rs.filename + " " + rs.status + " : <br>";
        for (var ii = 0; ii < rs.errors.length; ii++) {
            htmlString += "\t" + rs.errors[ii] + "<br>";
        }
        htmlString += "</a>";
    }
    document.getElementById("status").innerHTML = htmlString;
}


function debounce(func, wait, immediate) {
    var timeout;
    return function () {
        var context = this, args = arguments;
        var later = function () {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
};

btn.addEventListener("click", debounce(function () {
    var data = {
        "name": document.getElementById("name").value,
        "link": document.getElementById("link").value,
        "upload": document.getElementById("upl").checked,
        "delete": document.getElementById("del").checked
    }
    if (data.name == "" || data.link == "") {
        alert("name and link field cannot be blank");
    } else {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api", true);
        xhr.setRequestHeader("Content-Type", "application/json; charset=UTF-8");
        xhr.send(JSON.stringify(data));
        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4 && xhr.status == 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.result == "invalid link") alert("invalid link");
                else if (response.result == "missing parameter") alert("missing parameter");
                else {
                    alertContainer.insertAdjacentHTML("beforeend", "<div id=\"alert-msg\">Add new task succeed</div>");
                    alertContainer.style.display = 'inherit';
                    setTimeout(function () {
                        alertContainer.style.display = "none";
                        var msg = document.getElementById("alert-msg");
                        msg.parentNode.removeChild(msg);
                    }, 1300);
                }
            }
        }
    }
}, 1500, true));