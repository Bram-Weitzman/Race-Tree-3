//-------------------------  Select Project & Composition --------------------------------
function selectProject(compName) {
    
    var project = app.project;
    if (!project) {
        $.writeln("No project found.");
        return null; // Return null if no project is found
    }

    // Loop through the compositions in the project
    
    for (var i = 1; i <= project.numItems; i++) {
        var item = project.item(i);
        if (item && item instanceof CompItem && item.name === compName) {
            // Return the composition if its name matches
            return item;
        }
    }

    // If no composition with the specified name is found, log and return null
    $.writeln("Composition '" + compName + "' not found.");
    return null;
}

//--------------------------  Clear existing Key Frames --------------------
function clearKeyframes(compName) {
    var comp = selectProject(compName);
    if (!comp) {
        $.writeln("Composition not found or is null.");
        return;
    }

    // Loop through all layers in the composition
    for (var i = 1; i <= comp.numLayers; i++) {
        var layer = comp.layer(i);
        // Check if the layer has the Transform property group
        if (layer.transform) {
            // Loop through properties under the Transform group
            var transformGroup = layer.transform;
            for (var j = 1; j <= transformGroup.numProperties; j++) {
                var prop = transformGroup.property(j);
                // Check if the property has any keyframes
                if (prop.numKeys > 0) {
                    // Remove all keyframes from the property
                    for (var k = prop.numKeys; k >= 1; k--) {
                        prop.removeKey(k);
                    }
                }
            }
        }
    }
    //alert("KeyFrames Cleared!")
        // Call the callback function to indicate completion
    if (typeof callback === "function") {
        callback();
    }
}

//------------------  Create first key frames -----------------------------------------
function createFirstKeyframes(compName, callback) {
    var comp = selectProject(compName);
    if (!comp) {
        $.writeln("Composition not found or is null.");
        return;
    }

        // Loop through all layers in the composition
        for (var i = 1; i <= comp.numLayers; i++) {
            var layer = comp.layer(i);
            //$.writeln("layerName: " + layer.name);
            if (/^[0-9]+$/.test(layer.name)) {
                // Check if the layer has the Transform property group
                //$.writeln("whaaaaaat");
                if (layer.transform) {
                    // Access the position property under the Transform group
                    var positionProp = layer.transform.position;
                    // Set a keyframe at time 0 with the current position
                    positionProp.setValueAtTime(0, positionProp.value);
                }
            }else{
                //$.writeln("LayerNameHasLetters" + layer.name);
            }
        }
    // Call the callback function if provided
    if (typeof callback === 'function') {
        callback();
    }
}

//------------------------  Load json data ----------------------------------------------
function loadJSON(jsonData, callback) {
    var loopCount = 1;
    for (var lap in jsonData) {
        $.writeln("Check 2");
        if (jsonData.hasOwnProperty(lap)) {
            //$.writeln("check 3");
            var lapData = jsonData[lap];
            for (var i = 0; i < lapData.length; i++) {
                //$.writeln("Check 4");
                loopCount++;
                //$.writeln("check 5");
                var driver = lapData[i];
                //$.writeln("lapData: " + JSON.stringify(lapData[i]));
                if (driver.hasOwnProperty("Assumed_Positions")) {
                    $.writeln("check 6");
                    var timeOfDay = driver.TimeOfDay;
                    var assumedPositions = driver.Assumed_Positions;
                    $.writeln("Check 7");
                    for (var position in assumedPositions) {
                        $.writeln("check 8");
                        
                        if (assumedPositions.hasOwnProperty(position)) {
                           
                            //$.writeln("TimeOfDay: " + timeOfDay);
                            $.writeln("Posistion: " + position + ": " + assumedPositions[position]);
                            layerName = assumedPositions[position];
                            
                            preKeyFrame(timeOfDay, assumedPositions[position], "Name Badge", position, callback);
                            createKeyframe(timeOfDay, assumedPositions[position], "Name Badge", position, callback);
                            //createLapKeyFrames(timeOfDay, lap, "Name Badge", callback);
                            $.writeln("Got to the middle of Load JSON");
                        }
                    }
                }
            }
        }
    }
}

//-----------------------  Create Key Frames ------------------------------

function createKeyframe(timeOfDay, layerName, comp, position, callback) {
    var activeComp = app.project.activeItem;

    if (!/^[0-9]+$/.test(layerName)) {
        $.writeln("⚠️ Skipping: LayerName has letters — " + layerName);
        return;
    }

    if (!activeComp || !(activeComp instanceof CompItem)) {
        $.writeln("❌ No active composition or it's not a CompItem.");
        return;
    }

    var layer = activeComp.layer(layerName);
    if (!layer) {
        $.writeln("❌ Layer not found: " + layerName);
        return;
    }

    var prop = layer.property("Transform").property("Position");
    if (!prop || typeof prop.setValueAtTime !== "function") {
        $.writeln("❌ Position property not available for: " + layerName);
        return;
    }

    var myPosition = parseInt(position.slice(1));
    var X, Y;

    if (myPosition % 2 === 0) {
        $.writeln("🔢 Even position: " + myPosition);
        X = 475;
        Y = (35 * myPosition) + 390;
    } else {
        $.writeln("🔢 Odd position: " + myPosition);
        X = 200;
        Y = (35 * myPosition) + 415;
    }

    prop.setValueAtTime(timeOfDay, [X, Y]);
    $.writeln("✅ Set keyframe for layer " + layerName + " at " + timeOfDay + "s to position [" + X + ", " + Y + "]");

    if (typeof callback === "function") {
        callback();
    }
}
