// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the LIME bar chart with a slider

// The queries used to make it work are the following : 

// QUERY A (InfluxDB, Format as Table)
// SELECT * FROM "autogen"."features" WHERE ("patient" =~ /^$patient$/) AND $timeFilter


// Max number of feature to plot
var max_feature_number = 6

// argsort function found online and modified so that it sorts in descending order and by absolute values
let descending_abs_argsort = a => a.map((v, i) => [v, i]).sort((a, b) => Math.abs(b[0]) - Math.abs(a[0])).map(i => i[1])


// function to convert a unix timestamp to "HH:MM:SS"
function full_timestamp_to_hour(unix_time){
    if (typeof unix_time == 'string') {
        unix_time = parseInt(unix_time)
    }
    let date = new Date(unix_time)
    // padStarts adds enough 0 at the beginning make sure the string length is 2 (ex : 7 --> 07)
    return String(date.getHours()).padStart(2,0) + ':' + String(date.getMinutes()).padStart(2,0) + ':' + String(date.getSeconds()).padStart(2, 0)
};



console.log(data)
let all_fields = data.series[0].fields
let timestamp = []
let lime_values = []
let lime_names = []

for (let j = 0; j < all_fields.length; j++) {
    if (all_fields[j].name == "Time") {
        timestamp = all_fields[j].values.buffer;
    };
    if (all_fields[j].name.substring(0, 11) == 'lime_values') {
        lime_values.push(all_fields[j].values.buffer);
        lime_names.push(all_fields[j].name.substring(12))
    };
};

function extract_ith_lime_values(lime_values, lime_names, i){
    let x = [];
    let y = [];
    let color = []
    for (let j = 0; j< lime_values.length; j++){
        if (lime_values[j][i] != null) {
            x.push(lime_values[j][i]);
            y.push(lime_names[j]);
            if (lime_values[j][i] > 0) {
                color.push("#23c43e");
            } else {
                color.push("#eb4034");
            };
        };
    };

    // Now that  we retrieved all our data we want to sort it so we can keep only the most important features
    let inds = descending_abs_argsort(x)
    let sorted_x = []
    let sorted_y = []
    let sorted_color = []
    for (let k=0; k<Math.min(x.length,max_feature_number); k++){
        sorted_x.unshift(x[inds[k]])
        sorted_y.unshift(y[inds[k]])
        sorted_color.unshift(color[inds[k]])
    }
    return [sorted_x, sorted_y, sorted_color]
};

let x_range_min = 1000
let x_range_max = -1000
let data_y = {};
let data_x = {}
let data_color = {};
for (let i = 0; i < timestamp.length; i++) {
    let [x, y, color] = extract_ith_lime_values(lime_values, lime_names, i)
    if (x.length > 0 ){
        data_y[timestamp[i]] = y;
        data_x[timestamp[i]] = x;
        data_color[timestamp[i]] = color;
        if (Math.max(...x) > x_range_max){
            x_range_max = Math.max(...x)
        };
        if (Math.min(...x) < x_range_min){
            x_range_min = Math.min(...x)
        }
    };
};



let frames = [];
let unique_timestamps = Object.keys(data_y);
for (let i = 0; i < unique_timestamps.length; i++) {
    frames.push({
        name: unique_timestamps[i],
        data: [{
            x: data_x[unique_timestamps[i]],
            y: data_y[unique_timestamps[i]],
            marker: { color: data_color[unique_timestamps[i]] }
        }],
    })
};



let sliderSteps = [];
for (let i = 0; i < unique_timestamps.length; i++) {
    sliderSteps.push({
        method: 'animate',
        label: full_timestamp_to_hour(unique_timestamps[i]),
        args: [[unique_timestamps[i]], {
            mode: 'immediate',
            transition: { duration: 300 },
            frame: { duration: 300, redraw: false },
        }]
    });
}

let layout = {
    sliders: [{
        steps: sliderSteps
    }],
    xaxis: { range: [x_range_min - 0.1 * (x_range_max - x_range_min), x_range_max + 0.1 * (x_range_max - x_range_min)] }
};



let trace = {
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
