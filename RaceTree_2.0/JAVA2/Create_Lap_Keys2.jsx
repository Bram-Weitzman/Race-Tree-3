//#include AE_KeyFrame_Functions2.jsx
//------------------------ Load JSON File Data -----------------------------------------

function loadFile2(lapNum, Callback){
    var lapFile = new File("F:/RaceTree_2.0/Laps/Lap_" + lapNum + ".json");
    lapFile.open("r");
    var lapData = lapFile.read();

    lapFile.close();  
    $.writeln("Load File -- Complete: " + lapFile.fsName);  
    var jsonData = JSON.parse(lapData);

        // Call the callback function to indicate completion
    if (typeof callback === "function") {
        callback();
    }
    return jsonData;
}
//------------------------  Load json data 2 ----------------------------------------------

function loadJSON22(jsonData, adjustedTOD, callback) {
    var lapNumber;
    var firstTimeOfDay;
    

    
    for (var lap in jsonData) {
        if (jsonData.hasOwnProperty(lap)) {
            lapNumber = lap;
            
            firstTimeOfDay = jsonData[lap][0]["TimeOfDay"];
            $.writeln("lapNumber: " + lapNumber + " adjustedTOD: " + adjustedTOD);

            break;
        }
    }
    $.writeln("Lap-Number: " + lapNumber);

    if (lapNumber && firstTimeOfDay) {
        $.writeln("LapNumber " + lapNumber + " TOD " + firstTimeOfDay);
        createLapKeyFrames2(firstTimeOfDay, adjustedTOD, lapNumber, "Name Badge", callback);
        
    } else {
        $.writeln("Lap number or first time of day not found in JSON data.");
        // Handle the case where lapNumber or firstTimeOfDay is not found
        // This could happen if the jsonData object is empty or malformed
    }
}
//-------------------------  Lap Counter Function ---------------------------------------

function createLapKeyFrames2(timeOfDay, adjustedTOD, lap, comp, callback) {
   
    //TODD = timeOfDay - adjustedTOD + 120; // Adjusted time of day from JSON data
    $.writeln("createLapKeyFrames2() Lap: " + lap + " TimeOfDay: " + timeOfDay);

    // Access the active composition
    var activeComp = app.project.activeItem;
    if (activeComp && activeComp instanceof CompItem) {

        // Split & re-write "LapX" to "Lap X"

        var parts = lap.match(/([a-zA-Z]+)([0-9]+)/); // Split the string into alphabetic and numeric parts
        //var layerName = parts[1] + " " + parts[2]; // Concatenate the parts with a space in between
        var previousLayerName = parts[1] + " " + parts[2]; // Concatenate the parts with a space in between
        var layerName2 = parseInt(parts[2]) + 1;
        var layerName = parts[1] + " " + layerName2.toString();
        timeOfDay2 = timeOfDay - adjustedTOD + 120; // plus duration of 1st lap
        $.writeln("Lappppp: " + lap);
        $.writeln("TOD: " + timeOfDay2 + "  Curr lap  " + layerName);
        $.writeln("TOD: " + timeOfDay2 + "  prev lap  " + previousLayerName);

        // Find the layer in the composition
        var layer = activeComp.layer(layerName);
        var layer2 = activeComp.layer(previousLayerName);
        $.writeln ("Layer: type:" + typeof layer);

        //$.writeln("Layer2: " + layer2);

        if (previousLayerName === "Lap 1") {
            $.writeln("Lap 1 - set keyframe for opacity.");
            
            var timeInSeconds = timeOfDay2; // Convert time to seconds
            var prop = layer.property("Transform").property("Opacity");
            // Set keyframe and new position
            prop.setValueAtTime(timeInSeconds, [100]);
        }

        if (layer && layer2) {
            // Create a keyframe at the specified time
            var timeInSeconds = timeOfDay2; // Convert time to seconds
            var prop = layer.property("Transform").property("Opacity");
            var prop2 = layer2.property("Transform").property("Opacity");

            // Set Pre-Keyframe just before
            prop.setValueAtTime(timeInSeconds - 0.2, [0]);
            $.writeln(layer.name + " - set Prekeyframe for opacity at: " + (timeInSeconds - 0.2) + " seconds.");
       
            // Set keyframe and new position
            prop.setValueAtTime(timeInSeconds, [100]);
            $.writeln(layer.name + " - set keyframe for opacity at: " + timeInSeconds + " seconds.");

             // Set Pre-Keyframe just before on previous lap
            prop2.setValueAtTime(timeInSeconds - 0.2, [100]);
            $.writeln(layer2.name + " - set Prekeyframe for opacity at: " + (timeInSeconds - 0.2) + " seconds.");       
            // Set keyframe and new position
            prop2.setValueAtTime(timeInSeconds, [0]);
            $.writeln(layer2.name + " - set keyframe for opacity at: " + timeInSeconds + " seconds.");

            // Call the callback function to indicate completion
            if (typeof callback === "function") {
                callback();
            }
        } 
    } else {
        $.writeln("Active composition not found or is not a CompItem.");
    }
}

//----------------------  Load json data for lap number  ---------------------------
    //---------- Find adjustment time of day --------------
    
    var adjustedTOD = 0; // default value
    data = loadFile2(1, callback);// Lap 1 Only
    adjustedTOD = data["Lap1"][0]["TimeOfDay"];
    $.writeln("Adjusted Time of Day: " + adjustedTOD); // Adjusted time of day from JSON data

for (var i = 1; i <= nLaps; i++){

        lapNum = i;
        $.writeln("i in load json is " + i);
        jsonData = loadFile2(lapNum, callback);
        
        loadJSON22(jsonData, adjustedTOD, callback);
        callback();
    //}
}
