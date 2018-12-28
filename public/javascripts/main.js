(function () {
    window.onload = function () {
        let REFRESH_INTERVAL = 1000;
        let idOfTimeout = null;
        getStatus();


        function getStatus() {
            let exception = 1;
            fetch("api/status", {credentials: "same-origin"})
                .then((response) => response.status >= 200 && response.status < 300 ? response.text() : Promise.reject(new Error(response.status + ": " + response.statusText)))
                .then(JSON.parse)
                .then((data) => {
                    console.log(data);
                    $('#downloadQueue').children().each((index, element) => {
                        let newValue = data.downloadQueue.find((item) => item.gid == element.id);
                        if (newValue) {
                            let percentage = Math.round(newValue.completedLength / newValue.totalLength * 100);
                            let totalLength = humanFileSize(newValue.totalLength);
                            let completedLength = humanFileSize(newValue.completedLength);
                            let speed = humanFileSize(newValue.speed) + "/s";
                            let eta = humanTimeSeconds((newValue.totalLength - newValue.completedLength) / (newValue.speed ? newValue.speed : Infinity));
                            $(`#${element.id} .progress-bar`).attr('style', `width: ${percentage}%`).text(` ${percentage}%`);
                            $(`#${element.id}`).attr("data-json", JSON.stringify(newValue, null, 2));
                            $(`#${element.id} .float-right`).text(`${completedLength} / ${totalLength} @ ${speed} eta ${eta}`);
                        } else {
                            element.remove();
                        }
                    });

                    data.downloadQueue.filter((x) => $(`#${x.gid}`).length === 0).forEach((task) => {
                        let percentage = Math.round(task.completedLength / task.totalLength * 100);
                        let totalLength = humanFileSize(task.totalLength);
                        let completedLength = humanFileSize(task.completedLength);
                        let speed = humanFileSize(task.speed) + "/s";
                        let eta = humanTimeSeconds((task.totalLength - task.completedLength) / (task.speed ? task.speed : Infinity));

                        let card = $("<div>", { id: task.gid, "class": "card text-white bg-secondary mb-5", "data-json": JSON.stringify(task, null, 2) });
                        let header = $("<div>", {"class": "card-header"}).text(task.name).css('cursor', 'pointer');
                        let status = $("<div>", {"class": "float-right"}).text(`${completedLength} / ${totalLength} @ ${speed} eta ${eta}`);
                        let progress = $("<div>", {"class": "progress"}).append($("<div>", { "class": "progress-bar progress-bar-striped progress-bar-animated", "style": `width: ${percentage}%` }).text(`${percentage}%`));
                        $('#downloadQueue').append(card.append(header.append(status).append(progress)));

                        header.click(() => {
                            let detail = card.children('.card-body');
                            if (detail.length) {
                                detail.remove();
                            } else {
                                let cardBody = $("<div>", { "class": "card-body row", "style": "display: flex; align-items: center; justify-content: center;" });
                                let col3 = $("<div>", {"class": "col-3 card-text"});
                                let col7 = $("<div>", {"class": "col-7 card-text", "style": "white-space: pre-wrap"}).text(card.attr('data-json'));
                                let removeBtn = $("<button>", {"class": "btn btn-danger", "type": "button"})
                                    .text("⚠️Remove⚠️")
                                    .click(() => fetch("api/task", {
                                        credentials: "same-origin",
                                        body: JSON.stringify({"gid": task.gid}),
                                        headers: {"Content-Type": "application/json; charset=UTF-8"},
                                        method: "DELETE"
                                    }).catch((err) => $.notify(err, "error")));
                                card.append(cardBody.append(col3.append(removeBtn)).append(col7));
                            }
                        });
                    });


                    ///////////////////////
                    $('#uploadQueue').children().each((index, element) => {
                        let newValue = data.uploadQueue.find((item) => item.gid == element.id);
                        if (newValue) {
                            let percentage = Math.round(newValue.completedLength / newValue.totalLength * 100);
                            $(`#${element.id} .progress-bar`).attr('style', `width: ${percentage}%`).text(` ${percentage}%`);
                        } else {
                            element.remove();
                        }
                    });

                    data.uploadQueue.filter((x) => $(`#${x.gid}`).length === 0).forEach((task) => {
                        let totalLength = humanFileSize(task.totalLength);
                        let percentage = Math.round(task.completedLength / task.totalLength * 100);

                        let card = $("<div>", { id: task.gid, "class": "card text-white bg-info mb-5", "data-json": JSON.stringify(task, null, 2) });
                        let header = $("<div>", {"class": "card-header"}).text(task.name).css('cursor', 'pointer');
                        let status = $("<div>", {"class": "float-right"}).text(`${totalLength}`);
                        let progress = $("<div>", {"class": "progress"}).append($("<div>", { "class": "progress-bar progress-bar-striped progress-bar-animated", "style": `width: ${percentage}%` }).text(`${percentage}%`));
                        $('#uploadQueue').append(card.append(header.append(status).append(progress)));

                        header.click(() => {
                            let detail = card.children('.card-body');
                            if (detail.length) {
                                detail.remove();
                            } else {
                                let cardBody = $("<div>", { "class": "card-body row", "style": "display: flex; align-items: center; justify-content: center;" });
                                let col3 = $("<div>", {"class": "col-3 card-text"});
                                let col7 = $("<div>", {"class": "col-7 card-text", "style": "white-space: pre-wrap"}).text(card.attr('data-json'));
                                let removeBtn = $("<button>", {"class": "btn btn-danger", "type": "button"})
                                    .text("⚠️Remove⚠️")
                                    .click(() => fetch("api/task", {
                                        credentials: "same-origin",
                                        body: JSON.stringify({"gid": task.gid}),
                                        headers: {"Content-Type": "application/json; charset=UTF-8"},
                                        method: "DELETE"
                                    }).catch((err) => $.notify(err, "error")));
                                card.append(cardBody.append(col3.append(removeBtn)).append(col7));
                            }
                        });
                    });


                    ///////////////////////
                    $('#completedQueue').children().each((index, element) => {
                        let newValue = data.completedQueue.find((item) => item.gid == element.id);
                        if (newValue) {
                            // currently nothing to do
                        } else {
                            element.remove();
                        }
                    });

                    data.completedQueue.filter((x) => $(`#${x.gid}`).length === 0).forEach((task) => {
                        let card = $("<div>", { id: task.gid, "class": "card text-white bg-success mb-5", "data-json": JSON.stringify(task, null, 2) });
                        let header = $("<div>", {"class": "card-header"}).text(task.name).css('cursor', 'pointer');
                        let status = $("<div>", {"class": "float-right"}).text(`completed`);
                        $('#completedQueue').append(card.append(header.append(status)));

                        header.click(() => {
                            let detail = card.children('.card-body');
                            if (detail.length) {
                                detail.remove();
                            } else {
                                let cardBody = $("<div>", { "class": "card-body row", "style": "display: flex; align-items: center; justify-content: center;" });
                                let col3 = $("<div>", {"class": "col-3 card-text"});
                                let col7 = $("<div>", {"class": "col-7 card-text", "style": "white-space: pre-wrap"}).text(card.attr('data-json'));
                                let removeBtn = $("<button>", {"class": "btn btn-danger", "type": "button"})
                                    .text("⚠️Remove⚠️")
                                    .click(() => fetch("api/task", {
                                        credentials: "same-origin",
                                        body: JSON.stringify({"gid": task.gid}),
                                        headers: {"Content-Type": "application/json; charset=UTF-8"},
                                        method: "DELETE"
                                    }).catch((err) => $.notify(err, "error")));
                                card.append(cardBody.append(col3.append(removeBtn)).append(col7));
                            }
                        });
                    });
                })
                .catch((err) => {
                    $.notify(err, "error");
                    exception = 10;
                })
                .finally(() => idOfTimeout = setTimeout(getStatus, REFRESH_INTERVAL * exception));
        }


        $("#interval-val").text(REFRESH_INTERVAL / 1000);

        $("#interval").change(() => {
            clearTimeout(idOfTimeout);
            REFRESH_INTERVAL = $("#interval").val() * 1000;
            $("#interval-val").text(REFRESH_INTERVAL / 1000);
            idOfTimeout = setTimeout(getStatus, REFRESH_INTERVAL);
        });

        $("#btn").click(() => {
            let data = {
                "name": $("#name").val(),
                "link": $("#link").val(),
                "upload": $("#upl").is(':checked'),
                "delete": $("#del").is(':checked')
            };
            if (data.name === "" || data.link === "") {
                $("#btn").notify("name and link field cannot be blank", "warning");
            } else {
                fetch("api/addUri", {
                    credentials: "same-origin",
                    body: JSON.stringify(data),
                    headers: {"Content-Type": "application/json; charset=UTF-8"},
                    method: "POST"
                })
                    .then((response) => {
                        if (response.status === 201) {
                            $("#btn").notify("Successfully added new URI  task", "success");
                        } else if (response.status === 422) {
                            $("#btn").notify(JSON.parse(response.text()).message, "error");
                        } else {
                            return Promise.reject(new Error(response.status + ": " + response.statusText));
                        }
                    })
                    .catch((err) => $("#btn").notify(err, "error"));
            }
        });


        function humanFileSize(bytes) {
            let si = true;
            let thresh = si ? 1000 : 1024;
            if (Math.abs(bytes) < thresh) {
                return bytes + ' B';
            }
            let units = si
                ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
                : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
            let u = -1;
            do {
                bytes /= thresh;
                ++u;
            } while (Math.abs(bytes) >= thresh && u < units.length - 1);
            return bytes.toFixed(1) + ' ' + units[u];
        }

        function humanTimeSeconds(seconds) {
            let date = new Date(null);
            date.setSeconds(Math.round(seconds)); // specify value for SECONDS here
            try {
                return date.toISOString().substr(11, 8);
            } catch (e) {
                return 'Not Applicable';
            }

        }
    }
})();