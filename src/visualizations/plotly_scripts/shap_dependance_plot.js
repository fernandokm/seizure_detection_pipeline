// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the shap dependance plot

// The queries used to make it work are the following : 

// QUERY A : 

// SELECT
//   interval_start_time,
//   shap_values_interval_start_time,
//   cvi
// FROM shap_data



console.log(data)
var x = data.series[0].fields[0].values.buffer;
var y = data.series[0].fields[1].values.buffer;
var z = data.series[0].fields[2].values.buffer;


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

    return colors
};

var trace = {
    x: x,
    y: y,
    marker: {
        color: colors,
        colorscale: [[0, "#007bff"], [0.1, "#0069f8"], [0.2, "#5153e9"], [0.3, "#7e35d6"], [0.4, "#9d00be"], [0.5, "#bc00ab"], [0.6, "#db009a"], [0.7, "#f30086"], [0.8, "#ff0071"], [1, "#ff0059"]],
        showscale: true,
        cmin: z_min,
        cmax: z_max,
    }
};

console.log(z_max, z_min)
console.log(trace)
return { data: [trace] };