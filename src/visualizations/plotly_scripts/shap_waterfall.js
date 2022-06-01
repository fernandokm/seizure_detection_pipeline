// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the waterfall shap plot panel

// The queries used to make it work are the following : 

// QUERY A (Table format, query on Influx DB)
// SELECT * FROM "autogen"."features" WHERE ("patient" =~ /^$patient$/) AND $timeFilter



// Max number of feature to plot
let max_feature_number = 10;

// Base number for the waterfall plot
let mean_important_number = 0.1;

// argsort function found online :
// let argsort = a => a.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]).map(i => i[1])
// my modification to sort by absolute value in a descending order
let argsort_abs_reverse = a => a.map((v, i) => [v, i]).sort((a, b) => Math.abs(b[0]) - Math.abs(a[0])).map(i => i[1]);

// function to convert a timestamp of the form "2006-10-09 09:06:22.000000" to "09:06:22"
function full_timestamp_to_hour(unix_time){
    let date = new Date(unix_time)
    // padStarts adds enough 0 at the beginning make sure the string length is 2 (ex : 7 --> 07)
    return String(date.getHours()).padStart(2,0) + ':' + String(date.getMinutes()).padStart(2,0) + ':' + String(date.getSeconds()).padStart(2, 0)
};


function find_timestamps_of_crisis(timestamp, labels){
    let begin_of_crisis = []
    let end_of_crisis = []
    let in_crisis = (labels[0] == 1)
    if (in_crisis) {
        begin_of_crisis.push(timestamp[0])
    }
    for (let i=0; i<labels.length; i++){
        if (labels[i] == 1 & !in_crisis){
            in_crisis = true
            begin_of_crisis.push(timestamp[i])
        }
        if (labels[i] == 0 & in_crisis){
            in_crisis = false
            end_of_crisis.push(timestamp[i])
        }
        
    };
    return [begin_of_crisis, end_of_crisis];
}


console.log(data);
// If there is no data (not the good time window for our patient for example)
if (data.series.length == 0 ) {
    return {};
}

let all_fields = data.series[0].fields;
let only_shap_value_fields = [];
let timestamp = [];
let labels = [];
let predicted_labels = [];


// loop on all the fields to retrieve only the shap_values fields and the timestamp one
for (let j = 0; j < all_fields.length; j++) {
    if (all_fields[j].name == "Time") {
        timestamp = all_fields[j].values.buffer;
    };
    if (all_fields[j].name == "label") {
        labels = all_fields[j].values.buffer;
    };
    if (all_fields[j].name == "predicted_label") {
        predicted_labels = all_fields[j].values.buffer;
    };
    if (all_fields[j].name.substring(0, 11) == 'shap_values') {
        only_shap_value_fields.push(all_fields[j])
    };
};


// loop on the timestamp to retrieve for each instant the name of the features and the shap_values
let data_y = {};
let data_x = {};
for (let i = 0; i < timestamp.length; i++) {
    if (!(timestamp[i] in data_y)) {
        data_y[timestamp[i]] = []
        data_x[timestamp[i]] = []
    }
    for (let j = 0; j < only_shap_value_fields.length; j++) {
        data_x[timestamp[i]].push(only_shap_value_fields[j].values.buffer[i])
        data_y[timestamp[i]].push(only_shap_value_fields[j].name.substring(12))
    };
};

// data_x_i is a list of shap values for a given timestamp
// data_y_i is a list of feature names for a given timestamp
function construct_shap_waterfall(data_x_i, data_y_i) {
    let inds = argsort_abs_reverse(data_x_i); // Sorting in descending order + for absolute values
    let ind = -1;
    let new_data_x_i = [];
    let new_data_y_i = [];
    for (let i = 0; i < Math.min(inds.length, max_feature_number); i++) {
        ind = inds[i]
        // Plotly plots the first element at the bottom, and we want the biggest elements to be at the top
        new_data_x_i.unshift(data_x_i[ind]);  // unshift allows to push at the beginning of the array
        new_data_y_i.unshift(data_y_i[ind]);
    };
    let last_value = 0;
    for (let i = Math.min(inds.length, max_feature_number); i < Math.max(inds.length, max_feature_number); i++) {
        last_value += data_x_i[inds[i]];
    };

    new_data_x_i.unshift(last_value);
    new_data_y_i.unshift("Other");
    // We want this regroupment to be at the bottom
    return [ new_data_x_i, new_data_y_i ];
};

function find_data_x_i_extrema(data_x_i){
    let data_x_i_min = 1000;
    let data_x_i_max = -1000;
    let current_value = 0;
    for (let i = 0; i < data_x_i.length ; i++) {
        current_value += data_x_i[i]
        if (current_value < data_x_i_min) {
            data_x_i_min = current_value;
        };
        if (current_value > data_x_i_max) {
            data_x_i_max = current_value;
        };
    };
    return [data_x_i_min, data_x_i_max]
};

let frames = [];
let x_range_min = 1000;
let x_range_max = -1000;
// for (let i = 0; i < 100; i++) {
for (let i = 0; i < timestamp.length; i++) {
    let [ new_data_x_i, new_data_y_i ] = construct_shap_waterfall(data_x[timestamp[i]], data_y[timestamp[i]]);
    let [data_x_i_min, data_x_i_max] = find_data_x_i_extrema(new_data_x_i)
    if (data_x_i_max > x_range_max) {
        x_range_max = data_x_i_max
    };
    if (data_x_i_min < x_range_min) {
        x_range_min = data_x_i_min
    }; 
    frames.push({
        name: timestamp[i],
        data: [{
            x: new_data_x_i,
            y: new_data_y_i,
        }],
    });
};

let sliderSteps = [];
// for (let i = 0; i < 100; i++) {
for (let i = 0; i < timestamp.length; i++) {
    sliderSteps.push({
        method: 'animate',
        label: full_timestamp_to_hour(timestamp[i]),
        args: [[timestamp[i]], {
            mode: 'immediate',
            transition: { duration: 0 },
            frame: { duration: 0, redraw: true },
        }]
    });
}

let [begin_of_real_crisis, end_of_real_crisis] = find_timestamps_of_crisis(timestamp, labels);
let [begin_of_predicted_crisis, end_of_predicted_crisis] = find_timestamps_of_crisis(timestamp, predicted_labels);

let real_crisis_buttons_beginning = [];
let predicted_crisis_buttons_beginning = [];


for (let i = 0; i < begin_of_real_crisis.length; i++)  {
    real_crisis_buttons_beginning.push({
        label: full_timestamp_to_hour(begin_of_real_crisis[i]),
        method: 'animate',
        args: [[begin_of_real_crisis[i]], {
            mode: 'immediate',
            transition: { duration: 0 },
            frame: { duration: 0, redraw: true }
        }]
    });
};
for (let i = 0; i < begin_of_predicted_crisis.length; i++) {
    predicted_crisis_buttons_beginning.push({
        label: full_timestamp_to_hour(begin_of_predicted_crisis[i]),
        method: 'animate',
        args: [[begin_of_predicted_crisis[i]], {
            mode: 'immediate',
            transition: { duration: 0 },
            frame: { duration: 0, redraw: true }
        }]
    });
};


let layout = {
    sliders: [{
        steps: sliderSteps
    }],
    updatemenus: [{
        // type: 'buttons', 
        type : 'dropdown',
        showactive: false,
        x : -0.5,
        xanchor: 'center',
        yanchor: 'top',
        buttons: real_crisis_buttons_beginning
      },
      {
        // type: 'buttons',
        type : 'dropdown',
        showactive: false,
        x : -0.3,
        xanchor: 'center',
        yanchor: 'top',
        buttons: predicted_crisis_buttons_beginning
      }
    ],
    annotations : [{
        xref: 'paper',
        yref: 'paper',
        x: -0.5,
        xanchor: 'center',
        y: 1,
        yanchor: 'bottom',
        text: 'Real crises',
        showarrow: false
    }, {
        xref: 'paper',
        yref: 'paper',
        x: -0.3,
        xanchor: 'center',
        y: 1,
        yanchor: 'bottom',
        text: 'Predicted crises',
        showarrow: false
    }],
    // The range is the min and max for all the graphs on the slider +/- 10% of the range
    xaxis: { range: [x_range_min - 0.1 * (x_range_max - x_range_min) + mean_important_number, x_range_max + 0.1 * (x_range_max - x_range_min) + mean_important_number] }
};

let [ new_data_x_i, new_data_y_i ] = construct_shap_waterfall(data_x[timestamp[0]], data_y[timestamp[0]])
let relative = []
for (let i = 0; i < new_data_x_i.length; i++) {
    relative.push("relative")
}

let trace = {
    x: new_data_x_i,
    y: new_data_y_i,
    // measure: relative,
    type: "waterfall",
    // type:"bar",
    orientation: "h",
    base: mean_important_number,
}


return {
    data: [trace],
    layout: layout,
    frames: frames
};