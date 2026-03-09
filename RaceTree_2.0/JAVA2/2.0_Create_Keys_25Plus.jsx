// 2.0_Create_Keys_25Plus.jsx (Rebuild Step-by-Step)

// Include the shared function library
#include "2.0_Functions.jsx"

//---------------------------- Setup ------------------------------>

// Define fallback callback if needed
function callback() {
    $.writeln("callback called");
}

// Read lap count from file
var lapNumber = 0;
var filePath = "F:/RaceTree_2.0/lapNumFile.txt";
var file = new File(filePath);
if (file.exists) {
    file.open("r");
    lapNumber = parseInt(file.readln());
    file.close();
} else {
    alert("Lap number file not found.");
}

var nLaps = lapNumber;
var compName = "Name Badge";

//---------------------- Create Lap Counter Layers ------------------------------->

for (var i = 1; i <= nLaps; i++) {
    $.writeln("i:" + i );
    create_lap_counter_layers(compName, i, callback);
}

$.writeln("✅ Created all lap counter layers");

//---------------------- Load Lap JSON and Animate ------------------------------->
///*
for (var i = 1; i <= nLaps; i++) {
    var lapNum = i;
    var jsonData = loadFile(lapNum, callback);
    if (jsonData) {
        $.writeln("📂 Loaded JSON for Lap " + lapNum);
        loadJSON(jsonData, callback); 
    } else {
        $.writeln("⚠️ JSON data was null for Lap " + lapNum);
    }
}//*/



