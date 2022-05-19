// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the LIME bar chart with a slider

// The queries used to make it work are the following : 

// QUERY A : 

// SELECT
//   lime_coefficient,
//   feature_name,
//   timestamp
// FROM lime_barchart_less_random
// WHERE
//   patient_id = 1234 AND
//   session_id = 5678

// QUERY B : 

// SELECT
//   feature_name
// FROM lime_barchart
// WHERE
//   patient_id = 1234 AND
//   session_id = 5678


console.log(data)
var x = data.series[0].fields[0].values.buffer;
var y = data.series[0].fields[1].values.buffer;
var timestamp = data.series[0].fields[2].values.buffer;
var colors = [];


var data_y = {};
var data_x = {}
var data_color = {};
for (var i = 0; i < x.length; i++) {
    if (!(timestamp[i] in data_y)) {
        data_y[timestamp[i]] = []
        data_x[timestamp[i]] = []
        data_color[timestamp[i]] = []
    }
    data_y[timestamp[i]].push(y[i])
    data_x[timestamp[i]].push(x[i])

    if (x[i] > 0) {
        data_color[timestamp[i]].push("#23c43e");
    } else {
        data_color[timestamp[i]].push("#eb4034");
    };
};

var frames = [];
var unique_timestamps = Object.keys(data_y);
for (var i = 0; i < unique_timestamps.length; i++) {
    frames.push({
        name: unique_timestamps[i],
        data: [{
            x: data_x[unique_timestamps[i]],
            y: data_y[unique_timestamps[i]],
            marker: { color: data_color[unique_timestamps[i]] }
        }],
    })
};

var sliderSteps = [];
for (var i = 0; i < unique_timestamps.length; i++) {
    sliderSteps.push({
        method: 'animate',
        label: unique_timestamps[i],
        args: [[unique_timestamps[i]], {
            mode: 'immediate',
            transition: { duration: 300 },
            frame: { duration: 300, redraw: false },
        }]
    });
}

var layout = {
    sliders: [{
        steps: sliderSteps
    }]
};



var trace = {
    x: data_x[unique_timestamps[0]],
    y: data_y[unique_timestamps[0]],
    type: "bar",
    orientation: "h",
    marker: {
        color: data_color[unique_timestamps[0]]
    }
};

return {
    data: [trace],
    layout: layout,
    frames: frames
};
