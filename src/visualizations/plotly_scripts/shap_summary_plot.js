// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the summary shap plot panel

// The queries used to make it work are the following : 

// QUERY A : 

// SELECT
//   *
// FROM shap_data



// Max number of feature to plot
var max_feature_number = 2

// argsort function found online :
var argsort = a => a.map((v, i) => [v, i]).sort().map(i => i[1])

// Standard Normal variate using Box-Muller transform (also found online obviously)
function randn_bm() {
    var u = 0, v = 0;
    while (u === 0) u = Math.random(); //Converting [0,1) to (0,1)
    while (v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Shuffle function based on the Fisher-Yates (aka Knuth) Shuffle (once again found online)
function shuffle(array) {
    let currentIndex = array.length, randomIndex;

    // While there remain elements to shuffle.
    while (currentIndex != 0) {

        // Pick a remaining element.
        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex--;

        // And swap it with the current element.
        [array[currentIndex], array[randomIndex]] = [
            array[randomIndex], array[currentIndex]];
    }

    return array;
}

// Function to get the shap colors
function get_shap_colors(z) {
    var colors = [];
    var sorted_z = [...z].sort((a, b) => a - b)
    first_decile = Math.floor(sorted_z.length * 0.05) - 1;
    last_decile = Math.floor(sorted_z.length * 0.95) - 1;;

    var z_max = sorted_z[last_decile];
    var z_min = sorted_z[first_decile];

    var available_colors = ["#007bff", "#0069f8", "#5153e9", "#7e35d6", "#9d00be", "#bc00ab", "#db009a", "#f30086", "#ff0071", "#ff0059"];

    for (var i = 0; i < z.length; i++) {
        if (z_min > z[i]) {
            colors.push(available_colors[0]);
        };
        for (var j = 0; j < available_colors.length; j++) {
            if (j * (z_max - z_min) / available_colors.length + z_min <= z[i] && (j + 1) * (z_max - z_min) / available_colors.length + z_min > z[i]) {
                colors.push(available_colors[j]);
                break;
            };
        };
        if (z_max <= z[i]) {
            colors.push(available_colors[available_colors.length - 1]);
        };
    };


    return { colors, z_min, z_max };
};


function get_trace_for_one_feature(not_shuffled_shaps, not_shuffled_values, pos, colorbar) {
    // Shuffle the shaps and values
    var inds = [];
    for (var i = 0; i < not_shuffled_shaps.length; i++) {
        inds.push(i);
    }
    inds = shuffle(inds);
    (shaps = []).length = inds.length; shaps.fill(0);
    (values = []).length = inds.length; values.fill(0);

    for (var i = 0; i < inds.length; i++) {
        shaps[i] = not_shuffled_shaps[inds[i]];
        values[i] = not_shuffled_values[inds[i]];
    }


    var n_bins = 100;

    var quant = [];
    var quant_plus_random = [];
    var max_shap = Math.max(...shaps);
    var min_shap = Math.min(...shaps);

    for (var i = 0; i < shaps.length; i++) {
        quant.push(Math.round(n_bins * (shaps[i] - min_shap) / (max_shap - min_shap)));
        quant_plus_random.push(quant[i] + randn_bm() * 10 ** (-6));
    }

    var inds = argsort(quant_plus_random);
    var layer = 0;
    var last_bin = -1;
    var ind = -1;
    (ys = []).length = shaps.length; ys.fill(0);

    for (var i = 0; i < inds.length; i++) {
        ind = inds[i];
        if (!(quant[ind] == last_bin)) {
            layer = 0;
        };
        ys[ind] = Math.ceil(layer / 2) * ((layer % 2) * 2 - 1);
        layer += 1;
        last_bin = quant[ind];
    };

    let { colors, z_min, z_max } = get_shap_colors(values);

    // reverse the x axis and resize the y axis
    var negative_shaps = [];
    var resized_ys = [];
    var row_height = 0.4;
    for (i = 0; i < shaps.length; i++) {
        negative_shaps.push(-1 * shaps[i]);
        resized_ys.push(ys[i] * (0.9 * row_height / (Math.max(...ys) + 1)) + pos);
    };

    var trace = {
        x: negative_shaps,
        y: resized_ys,
        type: "scatter",
        mode: "markers",
    };
    var marker = {}

    if (colorbar) {
        marker = {
            color: colors,
            colorscale: [[0, "#007bff"], [0.1, "#0069f8"], [0.2, "#5153e9"], [0.3, "#7e35d6"], [0.4, "#9d00be"], [0.5, "#bc00ab"], [0.6, "#db009a"], [0.7, "#f30086"], [0.8, "#ff0071"], [1, "#ff0059"]],
            showscale: true,
            colorbar: {
                tickmode: 'array',
                ticktext: ["Low", "High"],
                tickvals: [0, 1],
                // showticklabels: false,
                thicknessmode: "pixel",
                thickness: 10,
                title: {
                    text: 'Feature value',
                    side: 'right'
                },
            },
            cmin: 0,
            cmax: 1
        };
    } else {
        marker = {
            color: colors,
        }
    }
    trace["marker"] = marker

    return trace

};

function calculate_variance(shaps) {
    var result = 0
    for (i = 0; i < shaps.length; i++) {
        result += Math.abs(shaps[i])
    }
    return result
}

console.log(data);
var all_fields = data.series[0].fields;
var feature_name = "";
var list_feature_names = [];
var data_dict = {};
for (var j = 0; j < all_fields.length; j++) {
    if (all_fields[j].name.substring(0, 11) == 'shap_values') {
        feature_name = all_fields[j].name.substring(12);
        data_dict[feature_name] = {};
        list_feature_names.push(feature_name);
    };
};

for (var j = 0; j < all_fields.length; j++) {
    if (all_fields[j].name.substring(0, 11) == 'shap_values') {
        feature_name = all_fields[j].name.substring(12)
        data_dict[feature_name]["shaps"] = all_fields[j].values.buffer
        data_dict[feature_name]["variance"] = calculate_variance(all_fields[j].values.buffer)
    } else if (data_dict.hasOwnProperty(all_fields[j].name)) {
        feature_name = all_fields[j].name
        data_dict[feature_name]["values"] = all_fields[j].values.buffer
    }
}


// Sorting the features by decreasing order of variance
var sorted_feature_names = list_feature_names.sort(function (first, second) {
    return data_dict[second].variance - data_dict[first].variance;
});

// Getting x position of features name annotation
var min_x_shaps_value = 0
var max_x_shaps_value = 0
for (i = 0; i < Math.min(max_feature_number, sorted_feature_names.length); i++) {
    if (max_x_shaps_value < Math.max(...data_dict[sorted_feature_names[i]]["shaps"])) {

        max_x_shaps_value = Math.max(...data_dict[sorted_feature_names[i]]["shaps"])
    }
    if (min_x_shaps_value > Math.min(...data_dict[sorted_feature_names[i]]["shaps"])) {
        min_x_shaps_value = Math.min(...data_dict[sorted_feature_names[i]]["shaps"])
    }
}
// Shap values are actually inverted when plotting so we take the 
// negative of the max minus a small percentage of the range
var x_annotation_pos = -1 * max_x_shaps_value - 0.1 * (max_x_shaps_value - min_x_shaps_value)

var traces = []
var annotations = []
for (i = 0; i < Math.min(max_feature_number, sorted_feature_names.length); i++) {
    traces.push(get_trace_for_one_feature(data_dict[sorted_feature_names[i]]["shaps"], data_dict[sorted_feature_names[i]]["values"], i + 1, (i == 0)))
    annotations.push(
        {
            x: x_annotation_pos,
            xanchor: 'right',
            y: i + 1,
            yanchor: 'center',
            text: sorted_feature_names[i],
            showarrow: false
        }
    )
}




var layout = {
    font: {
        color: "darkgrey"
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: {
        autorange: true,
        showgrid: false,
        showline: true,
        type: "linear"
    },
    yaxis: {
        autorange: true,
        showgrid: false,
        showline: false,
        visible: false,
        type: "linear"
    },
    showlegend: false,
    annotations: annotations
}

return { data: traces, layout: layout };