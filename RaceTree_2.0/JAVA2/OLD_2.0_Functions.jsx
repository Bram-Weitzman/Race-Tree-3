// 2.0_Functions.jsx

//------------------  Create Lap Counter Layers  -------------------------------->

function create_lap_counter_layers(compName, lapNumber, callback) {
    $.writeln("compName:" + compName);
    $.writeln("lapNumber: " + lapNumber);
    var comp = selectProject(compName);
    $.writeln("here2");

    var existingLayer = null;
    for (var i = 1; i <= comp.layers.length; i++) {
        var curLayer = comp.layers[i];
        if (curLayer && curLayer.name === "Lap " + lapNumber) {
            existingLayer = curLayer;
            var opacityProp = curLayer.property("Transform").property("Opacity");
            opacityProp.setValueAtTime(0, 0);
            break;
        }
    }

    if (!existingLayer) {
        var textLayer = comp.layers.addText("LAP   " + lapNumber);
        textLayer.name = "Lap " + lapNumber;
        textLayer.position.setValue([200, 315]);
        textLayer.outPoint = comp.duration;

        var textProperty = textLayer.property("ADBE Text Properties").property("ADBE Text Document");
        var textDoc = textProperty.value;
        textDoc.fontSize = 60;
        textDoc.fillColor = [1, 1, 1];
        textDoc.font = "Xolonium";
        textDoc.applyFill = true;

        textProperty.setValue(textDoc);
        textLayer.opacity.setValue(0);
        textLayer.opacity.setValueAtTime(0, 0);

        if (typeof callback === 'function') {
            callback(textLayer);
        }
    } else {
        $.writeln("Lap Number Layer Already Exists!");
        if (typeof callback === 'function') {
            callback(existingLayer);
        }
    }
}

//------------------------ Load JSON File Data ----------------------------------->

function loadFile(lapNum, callback) {
    var lapFile = new File("F:/RaceTree_2.0/Laps/Lap_" + lapNum + ".json");
    if (!lapFile.exists) {
        $.writeln("❌ Lap file not found: Lap_" + lapNum + ".json");
        return null;
    }

    lapFile.open("r");
    var lapData = lapFile.read();
    lapFile.close();

    var jsonData = JSON.parse(lapData);

    if (typeof callback === "function") {
        callback();
    }

    return jsonData;
}

//------------------------ Load JSON and Animate ----------------------------------->

function loadJSON(jsonData, callback) {
    var loopCount = 1;
    $.writeln("🔄 Entering loadJSON loop");
    for (var lap in jsonData) {
        $.writeln("🔁 Looping lap key: " + lap);
        if (jsonData.hasOwnProperty(lap)) {
            $.writeln("✅ Lap has own property: " + lap);
            var lapData = jsonData[lap];
            for (var i = 0; i < lapData.length; i++) {
                $.writeln("➡️ Looping driver index: " + i);
                loopCount++;
                var driver = lapData[i];
                $.writeln("🔎 Checking driver at index " + i + ": " + JSON.stringify(driver));
                if ("Assumed_Positions" in driver || "assumed_positions" in driver || "assumedPositions" in driver) {
                    $.writeln("📌 Driver has Assumed_Positions");
                    var timeOfDay = driver.TimeOfDay;
                    var assumedPositions = driver.Assumed_Positions || driver.assumed_positions || driver.assumedPositions;

                    if (!assumedPositions || typeof assumedPositions !== "object") {
                        $.writeln("❌ assumedPositions is invalid: " + assumedPositions);
                        $.writeln("Driver object: " + JSON.stringify(driver));
                        return;
                    }

                    for (var position in assumedPositions) {
                        $.writeln("🔁 Scanning position: " + position);
                        var value = assumedPositions[position];
                        try {
                            var valueStr = (typeof value === "object") ? JSON.stringify(value) : value;
                            $.writeln("🔍 assumedPositions[" + position + "] = " + valueStr);
                        } catch (e) {
                            $.writeln("⚠️ Could not stringify assumedPositions[" + position + "]: " + e.toString());
                        }

                        if (assumedPositions.hasOwnProperty(position)) {
                            $.writeln("✅ Position has own property: " + position);
                            var layerName = (typeof value === "object" && value.name) ? value.name : value;
                            $.writeln("📍 Calling preKeyFrame for " + layerName + " at " + timeOfDay);
                            preKeyFrame(timeOfDay, layerName, "Name Badge", position, callback);
                            $.writeln("📍 Calling createKeyframe for " + layerName + " at " + timeOfDay);
                            createKeyframe(timeOfDay, layerName, "Name Badge", position, callback);
                        }
                    }
                } else {
                    $.writeln("⚠️ Driver missing Assumed_Positions");
                }
            }
        } else {
            $.writeln("⚠️ Skipping invalid lap key");
        }
    }
}
