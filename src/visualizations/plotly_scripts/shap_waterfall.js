// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the waterfall shap plot panel

// The queries used to make it work are the following : 

// QUERY A : 

// SELECT
//   *
// FROM shap_data




console.log(data)
var all_fields = data.series[0].fields

var only_shap_value_fields = []
var timestamp = []

for (var j = 0; j < all_fields.length; j++) {
    if (all_fields[j].name == "timestamp") {
        timestamp = all_fields[j].values.buffer;
    }
    if (all_fields[j].name.substring(0, 11) == 'shap_values') {
        only_shap_value_fields.push(all_fields[j])
    }
}

var data_y = {};
var data_x = {}
for (var i = 0; i < timestamp.length; i++) {
    if (!(timestamp[i] in data_y)) {
        data_y[timestamp[i]] = []
        data_x[timestamp[i]] = []
    }
    for (var j = 0; j < only_shap_value_fields.length; j++) {
        data_x[timestamp[i]].push(only_shap_value_fields[j].values.buffer[i])
        data_y[timestamp[i]].push(only_shap_value_fields[j].name)
    };
};

var frames = [];
for (var i = 0; i < timestamp.length; i++) {
    frames.push({
        name: timestamp[i],
        data: [{
            x: data_x[timestamp[i]],
            y: data_y[timestamp[i]],
        }],
    })
};

var sliderSteps = [];
for (var i = 0; i < timestamp.length; i++) {
    sliderSteps.push({
        method: 'animate',
        label: timestamp[i],
        args: [[timestamp[i]], {
            mode: 'immediate',
            transition: { duration: 0 },
            frame: { duration: 0, redraw: true },
        }]
    });
}

var layout = {
    sliders: [{
        steps: sliderSteps
    }]
};

console.log(frames)

var relative = []
for (var i = 0; i < data_x[timestamp[0]].length; i++) {
    relative.push("relative")
}


var trace = {
    x: data_x[timestamp[0]],
    y: data_y[timestamp[0]],
    // measure: relative,
    type: "waterfall",
    // type:"bar",
    orientation: "h"
}

return {
    data: [trace],
    layout: layout,
    frames: frames
};
