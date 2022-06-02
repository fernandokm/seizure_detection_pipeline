// This file is NOT used in Grafana, it is simply a copy paste of the Javascript script used in the correlation plot panel

// The queries used to make it work are the following : 

// QUERY A : 
// SELECT /^$feature_1$/, /^$feature_2$/ FROM "autogen"."features" WHERE ("patient" =~ /^$patient$/) AND $timeFilter

console.log(data)

// in case there is no data
if (data.series.length == 0 ) {
    return {layout: {xaxis: {
        type : "linear"
    }}}
}
// if one feature has no data points
if (data.series[0].fields.length < 3) {
    return {layout: {xaxis: {
        type : "linear"
    }}}
}

let trace = {
    x: data.series[0].fields[1].values.buffer,
    y: data.series[0].fields[2].values.buffer,
    marker: {
        color: "rgba(77, 189, 204, 1)",
        size: 3,
    },
    mode: "markers",
    type: "scatter"
};

let layout = {
    margin: {
        b: 30
    },
    xaxis: {
        title: {
            text: data.series[0].fields[1].name,
        },
        type : "linear",
    },
    yaxis: {
        title: {
            text: data.series[0].fields[2].name,
        }
    },
  }

  
return {data:[trace], layout:layout};