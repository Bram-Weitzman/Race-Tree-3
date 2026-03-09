// Inclusions

#include AE_KeyFrame_Functions2.jsx

// Define the file path
var filePath = "F:/RaceTree_2.0/lapNumFile.txt";


// Initialize a variable to store the value read from the file
var lapNumber = 0;

try {
    // Create a File object representing the file
    var file = new File(filePath);

    // Check if the file exists
    if (file.exists) {
        // Open the file
        file.open("r");

        // Read the contents of the file
        var fileContent = file.readln();

        // Close the file
        file.close();

        // Parse the content as an integer
        lapNumber = parseInt(fileContent);
    } else {
        // Handle file not found
        alert("File not found: " + filePath);
    }
} catch (e) {
    // Handle any errors
    alert("Error reading file: " + e);
}

// Use the value read from the file
$.writeln("Lap Number: " + lapNumber);



var compName = "Name Badge"
//var nLaps = 11; // temp value - need to auto generate
var nLaps = lapNumber;


//-------------------------  Select Project --------------------------------
selectProject(compName);

//--------------------------  Clear existing Key Frames --------------------
clearKeyframes(compName)
//exit(); // Exit the script




//--------------------------- set First key frames -------------------------------
createFirstKeyframes(compName, callback);

//----------------------  Load json data for lap data  ---------------------------

//Find adjustment time of day
var adjustedTOD = 0; // default value
data = loadFile(1, callback);
adjustedTOD = data["Lap1"][0]["TimeOfDay"]; // Adjusted time of day from JSON data
adjustedTOD = adjustedTOD + 120;
for (var i = 1; i <= nLaps; i++){
        lapNum = i;

            //$.writeln("i in load json is " + i);
            jsonData = loadFile(lapNum, callback);
            loadJSON(jsonData, adjustedTOD, callback);
            callback();

}


//-------------------------  Create Lap Counter  --------------------------------
for (var i = 1; i <= nLaps; i++){

    $.writeln("lap counter line: " + i);
    create_lap_counter_layers(compName, i, callback);

}
