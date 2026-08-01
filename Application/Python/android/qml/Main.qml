pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1280
    height: 800
    minimumWidth: 960
    minimumHeight: 600
    visible: true
    title: "Dee's Fighting Ships — Tablet Companion"
    color: "#eef1f4"

    property int activePage: 0
    property color navy: "#172331"
    property color navyLight: "#243548"
    property color gold: "#d6a84c"
    property color ink: "#17202a"
    property color muted: "#657384"
    property color panel: "#ffffff"
    property color border: "#d8dee6"
    property color danger: "#b53b45"
    property color success: "#2f7d5b"

    font.family: Qt.platform.os === "android" ? "sans-serif" : "Segoe UI"

    component DfsButton: Button {
        implicitHeight: 48
        leftPadding: 16
        rightPadding: 16
        font.pixelSize: 16
    }

    component SectionLabel: Label {
        font.pixelSize: 19
        font.weight: Font.DemiBold
        color: window.ink
    }

    component MutedLabel: Label {
        color: window.muted
        font.pixelSize: 14
        wrapMode: Text.WordWrap
    }

    component StatTile: Rectangle {
        id: statTile
        property string caption: ""
        property string value: "—"
        implicitWidth: 132
        implicitHeight: 76
        radius: 8
        color: "#f5f7f9"
        border.color: window.border

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 3
            Label {
                text: statTile.caption.toUpperCase()
                color: window.muted
                font.pixelSize: 11
                font.weight: Font.DemiBold
            }
            Label {
                text: statTile.value || "—"
                color: window.ink
                font.pixelSize: 21
                font.weight: Font.Bold
            }
        }
    }

    component TrackCard: Rectangle {
        id: trackCard
        property string caption: ""
        property var track: ({})
        property string unitId: ""
        property string trackName: ""
        visible: track.available === true
        implicitHeight: visible ? 112 : 0
        radius: 9
        color: "#f5f7f9"
        border.color: window.border

        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    text: trackCard.caption.toUpperCase()
                    color: window.muted
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                Label {
                    text: String(trackCard.track.current || 0) + " / " + String(trackCard.track.maximum || 0)
                    color: window.ink
                    font.pixelSize: 25
                    font.weight: Font.Bold
                }
                MutedLabel {
                    visible: (trackCard.track.threshold || 0) > 0
                    text: "Threshold " + String(trackCard.track.threshold || 0)
                }
            }
            DfsButton {
                text: "−1"
                onClicked: dfsMobile.adjustTrack(trackCard.unitId, trackCard.trackName, -1)
            }
            DfsButton {
                text: "+1"
                onClicked: dfsMobile.adjustTrack(trackCard.unitId, trackCard.trackName, 1)
            }
        }
    }

    header: ToolBar {
        height: 64
        background: Rectangle { color: window.navy }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            Label {
                text: "DFS"
                color: window.gold
                font.pixelSize: 26
                font.weight: Font.Black
            }
            ColumnLayout {
                spacing: 0
                Label {
                    text: "Dee's Fighting Ships"
                    color: "white"
                    font.pixelSize: 19
                    font.weight: Font.DemiBold
                }
                Label {
                    text: "Tablet Companion — Feasibility Build"
                    color: "#b8c5d3"
                    font.pixelSize: 12
                }
            }
            Item { Layout.fillWidth: true }
            Label {
                text: dfsMobile.message
                visible: text.length > 0
                color: "#d7e1ea"
                font.pixelSize: 13
                elide: Text.ElideRight
                Layout.maximumWidth: 420
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 154
            Layout.fillHeight: true
            color: window.navy

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                Repeater {
                    model: [
                        { label: "Ships", glyph: "▤" },
                        { label: "Fleet", glyph: "◈" },
                        { label: "Battle", glyph: "✦" },
                        { label: "Rules", glyph: "?" }
                    ]
                    delegate: Button {
                        id: navButton
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredHeight: 66
                        text: modelData.glyph + "  " + modelData.label
                        font.pixelSize: 17
                        font.weight: window.activePage === index ? Font.DemiBold : Font.Normal
                        onClicked: window.activePage = index
                        background: Rectangle {
                            radius: 8
                            color: window.activePage === navButton.index ? window.navyLight : "transparent"
                            border.color: window.activePage === navButton.index ? window.gold : "transparent"
                        }
                        contentItem: Label {
                            text: navButton.text
                            color: window.activePage === navButton.index ? "white" : "#c8d2dc"
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 10
                            font: navButton.font
                        }
                    }
                }
                Item { Layout.fillHeight: true }
                MutedLabel {
                    Layout.fillWidth: true
                    text: "Offline • Certified data"
                    color: "#9cabb9"
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: 11
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: window.activePage

            // SHIP VIEWER -----------------------------------------------------
            Item {
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Rectangle {
                        Layout.preferredWidth: 410
                        Layout.fillHeight: true
                        radius: 10
                        color: window.panel
                        border.color: window.border

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 10
                            SectionLabel { text: "Ship Viewer" }
                            MutedLabel { text: "Native profiles from the certified DFS database." }
                            RowLayout {
                                Layout.fillWidth: true
                                TextField {
                                    id: viewerSearch
                                    Layout.fillWidth: true
                                    implicitHeight: 48
                                    placeholderText: "Search name or class"
                                    onAccepted: dfsMobile.searchPlatforms(text, 0)
                                }
                                DfsButton {
                                    text: "Search"
                                    onClicked: dfsMobile.searchPlatforms(viewerSearch.text, 0)
                                }
                            }
                            Label {
                                text: String(dfsMobile.platforms.length) + " platforms"
                                color: window.muted
                            }
                            ListView {
                                id: platformList
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                spacing: 5
                                model: dfsMobile.platforms
                                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                delegate: ItemDelegate {
                                    id: platformDelegate
                                    required property var modelData
                                    width: platformList.width
                                    height: 76
                                    onClicked: dfsMobile.selectPlatform(modelData.shipId)
                                    background: Rectangle {
                                        radius: 7
                                        color: platformDelegate.down ? "#dce6ef" : (platformDelegate.hovered ? "#eef3f7" : "transparent")
                                    }
                                    contentItem: Column {
                                        spacing: 3
                                        Label {
                                            width: parent.width
                                            text: modelData.name
                                            color: window.ink
                                            font.pixelSize: 16
                                            font.weight: Font.DemiBold
                                            elide: Text.ElideRight
                                        }
                                        Label {
                                            width: parent.width
                                            text: modelData.faction + " • " + modelData.priorities
                                            color: window.muted
                                            font.pixelSize: 13
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 10
                        color: window.panel
                        border.color: window.border

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 10
                            Label {
                                text: dfsMobile.selectedPlatform.name || "Select a platform"
                                color: window.ink
                                font.pixelSize: 26
                                font.weight: Font.Bold
                            }
                            MutedLabel {
                                text: dfsMobile.selectedPlatform.name
                                    ? (dfsMobile.selectedPlatform.shipClass + " • " + dfsMobile.selectedPlatform.faction)
                                    : "Tap a ship on the left to open its native stat record."
                            }
                            ComboBox {
                                id: viewerProfile
                                Layout.fillWidth: true
                                implicitHeight: 48
                                visible: model.length > 0
                                model: dfsMobile.selectedPlatform.profiles || []
                                delegate: ItemDelegate {
                                    required property var modelData
                                    width: viewerProfile.width
                                    text: modelData.fleet + " — " + modelData.priority
                                }
                                contentItem: Label {
                                    leftPadding: 12
                                    verticalAlignment: Text.AlignVCenter
                                    text: {
                                        var values = dfsMobile.selectedPlatform.profiles || []
                                        if (viewerProfile.currentIndex < 0 || viewerProfile.currentIndex >= values.length)
                                            return ""
                                        var item = values[viewerProfile.currentIndex]
                                        return item.fleet + " — " + item.priority
                                    }
                                    color: window.ink
                                    elide: Text.ElideRight
                                }
                            }

                            Flickable {
                                id: profileFlick
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                contentWidth: width
                                contentHeight: profileColumn.implicitHeight
                                boundsBehavior: Flickable.StopAtBounds
                                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                                property var currentProfile: {
                                    var values = dfsMobile.selectedPlatform.profiles || []
                                    if (viewerProfile.currentIndex < 0 || viewerProfile.currentIndex >= values.length)
                                        return ({})
                                    return values[viewerProfile.currentIndex]
                                }

                                ColumnLayout {
                                    id: profileColumn
                                    width: profileFlick.width
                                    spacing: 12
                                    Flow {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        StatTile { caption: "Priority"; value: profileFlick.currentProfile.priority }
                                        StatTile { caption: "Initiative"; value: profileFlick.currentProfile.initiative }
                                        StatTile { caption: "Speed"; value: profileFlick.currentProfile.speed }
                                        StatTile { caption: "Turn"; value: profileFlick.currentProfile.turn }
                                        StatTile { caption: "Hull"; value: profileFlick.currentProfile.hull }
                                        StatTile { caption: "Damage"; value: profileFlick.currentProfile.damage }
                                        StatTile { caption: "Crew"; value: profileFlick.currentProfile.crew }
                                        StatTile { caption: "Troops"; value: profileFlick.currentProfile.troops }
                                    }

                                    SectionLabel { text: "Profile" }
                                    MutedLabel { Layout.fillWidth: true; text: "Craft: " + (profileFlick.currentProfile.craft || "None") }
                                    MutedLabel { Layout.fillWidth: true; text: "In service: " + (profileFlick.currentProfile.inService || "—") }
                                    Label {
                                        Layout.fillWidth: true
                                        text: "Traits: " + (profileFlick.currentProfile.traitsText || "None")
                                        color: window.ink
                                        font.pixelSize: 15
                                        wrapMode: Text.WordWrap
                                    }

                                    SectionLabel { text: "Weapons" }
                                    Repeater {
                                        model: profileFlick.currentProfile.weapons || []
                                        delegate: Rectangle {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            implicitHeight: weaponColumn.implicitHeight + 18
                                            radius: 7
                                            color: "#f6f8fa"
                                            border.color: window.border
                                            Column {
                                                id: weaponColumn
                                                anchors.left: parent.left
                                                anchors.right: parent.right
                                                anchors.top: parent.top
                                                anchors.margins: 9
                                                spacing: 3
                                                Label {
                                                    width: parent.width
                                                    text: modelData.arc + "  •  " + modelData.name
                                                    color: window.ink
                                                    font.pixelSize: 15
                                                    font.weight: Font.DemiBold
                                                    wrapMode: Text.WordWrap
                                                }
                                                MutedLabel {
                                                    width: parent.width
                                                    text: "Range " + modelData.range + "  •  AD " + modelData.attackDice
                                                        + (modelData.traits ? "  •  " + modelData.traits : "")
                                                }
                                            }
                                        }
                                    }

                                    SectionLabel {
                                        visible: (profileFlick.currentProfile.notes || []).length > 0
                                        text: "Notes"
                                    }
                                    Repeater {
                                        model: profileFlick.currentProfile.notes || []
                                        delegate: MutedLabel {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            text: "• " + modelData
                                        }
                                    }
                                    Item { Layout.preferredHeight: 12 }
                                }
                            }
                        }
                    }
                }
            }

            // FLEET BUILDER --------------------------------------------------
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 132
                        radius: 10
                        color: window.panel
                        border.color: window.border
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 10
                            ColumnLayout {
                                Layout.preferredWidth: 220
                                SectionLabel { text: "Fleet Builder" }
                                TextField {
                                    id: fleetName
                                    Layout.fillWidth: true
                                    implicitHeight: 46
                                    placeholderText: "Fleet name"
                                    text: "Tablet Test Fleet"
                                }
                            }
                            ColumnLayout {
                                Label { text: "Faction"; color: window.muted }
                                ComboBox {
                                    id: fleetFaction
                                    Layout.preferredWidth: 210
                                    implicitHeight: 46
                                    model: dfsMobile.factions
                                    textRole: "label"
                                    valueRole: "id"
                                    onActivated: dfsMobile.loadFleetLists(currentValue)
                                }
                            }
                            ColumnLayout {
                                Label { text: "Fleet / Era"; color: window.muted }
                                ComboBox {
                                    id: fleetList
                                    Layout.preferredWidth: 245
                                    implicitHeight: 46
                                    model: dfsMobile.fleetLists
                                    textRole: "label"
                                    valueRole: "id"
                                }
                            }
                            ColumnLayout {
                                Label { text: "Priority"; color: window.muted }
                                ComboBox {
                                    id: scenarioPriority
                                    Layout.preferredWidth: 135
                                    implicitHeight: 46
                                    model: ["Patrol", "Skirmish", "Raid", "Battle", "War", "Armageddon"]
                                    currentIndex: 2
                                }
                            }
                            ColumnLayout {
                                Label { text: "FAP"; color: window.muted }
                                SpinBox { id: fap; from: 1; to: 32; value: 1; implicitHeight: 46 }
                            }
                            ColumnLayout {
                                Label { text: "Year (0 = any)"; color: window.muted }
                                SpinBox { id: fleetYear; from: 0; to: 9999; value: 0; implicitHeight: 46 }
                            }
                            DfsButton {
                                text: dfsMobile.fleetState.active ? "New Fleet" : "Create Fleet"
                                enabled: fleetFaction.currentValue > 0 && fleetList.currentValue > 0
                                onClicked: dfsMobile.createFleet(
                                    fleetName.text,
                                    fleetFaction.currentValue || 0,
                                    fleetList.currentValue || 0,
                                    scenarioPriority.currentText,
                                    fap.value,
                                    fleetYear.value
                                )
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 12
                        Rectangle {
                            Layout.preferredWidth: 455
                            Layout.fillHeight: true
                            radius: 10
                            color: window.panel
                            border.color: window.border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 8
                                SectionLabel { text: "Available Platforms" }
                                TextField {
                                    id: fleetSearch
                                    Layout.fillWidth: true
                                    implicitHeight: 46
                                    placeholderText: "Search this fleet list"
                                    enabled: dfsMobile.fleetState.active === true
                                    onAccepted: dfsMobile.searchFleetProfiles(text)
                                }
                                ListView {
                                    id: availableList
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    spacing: 6
                                    model: dfsMobile.availableProfiles
                                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                    delegate: Rectangle {
                                        required property var modelData
                                        width: availableList.width
                                        height: modelData.reason ? 104 : 82
                                        radius: 8
                                        color: modelData.allowed ? "#f6f8fa" : "#f7eeee"
                                        border.color: modelData.allowed ? window.border : "#d7afb3"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 2
                                                Label {
                                                    Layout.fillWidth: true
                                                    text: modelData.name
                                                    color: window.ink
                                                    font.pixelSize: 16
                                                    font.weight: Font.DemiBold
                                                    elide: Text.ElideRight
                                                }
                                                MutedLabel {
                                                    Layout.fillWidth: true
                                                    text: modelData.priority + " • " + modelData.inService
                                                }
                                                Label {
                                                    Layout.fillWidth: true
                                                    visible: modelData.reason.length > 0
                                                    text: modelData.reason
                                                    color: window.danger
                                                    font.pixelSize: 11
                                                    elide: Text.ElideRight
                                                }
                                            }
                                            DfsButton {
                                                text: "Add"
                                                enabled: modelData.allowed
                                                onClicked: dfsMobile.addProfile(modelData.profileId)
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 10
                            color: window.panel
                            border.color: window.border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 8
                                RowLayout {
                                    Layout.fillWidth: true
                                    SectionLabel { text: dfsMobile.fleetState.name || "Roster" }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: dfsMobile.fleetState.isValid === false ? "INVALID" : "LEGAL"
                                        visible: dfsMobile.fleetState.active === true
                                        color: dfsMobile.fleetState.isValid === false ? window.danger : window.success
                                        font.pixelSize: 15
                                        font.weight: Font.Bold
                                    }
                                }
                                MutedLabel {
                                    Layout.fillWidth: true
                                    text: dfsMobile.fleetState.active
                                        ? ("Budget: " + dfsMobile.fleetState.budget + "  •  Selected: "
                                           + dfsMobile.fleetState.selected + "  •  " + dfsMobile.fleetState.remaining)
                                        : "Create a fleet above to begin."
                                }
                                ListView {
                                    id: rosterList
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    spacing: 6
                                    model: dfsMobile.fleetState.roster || []
                                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                    delegate: Rectangle {
                                        required property var modelData
                                        width: rosterList.width
                                        height: 72
                                        radius: 8
                                        color: "#f6f8fa"
                                        border.color: window.border
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                Label {
                                                    text: modelData.name + (modelData.quantity > 1 ? " ×" + modelData.quantity : "")
                                                    color: window.ink
                                                    font.pixelSize: 16
                                                    font.weight: Font.DemiBold
                                                }
                                                MutedLabel { text: modelData.priority + " • " + modelData.fleet }
                                            }
                                            DfsButton {
                                                text: "Remove"
                                                onClicked: dfsMobile.removeEntry(modelData.entryId)
                                            }
                                        }
                                    }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    visible: (dfsMobile.fleetState.validation || []).length > 0
                                    implicitHeight: validationColumn.implicitHeight + 20
                                    radius: 7
                                    color: "#fff5e8"
                                    border.color: "#e5c28d"
                                    ColumnLayout {
                                        id: validationColumn
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        Repeater {
                                            model: dfsMobile.fleetState.validation || []
                                            delegate: Label {
                                                required property var modelData
                                                Layout.fillWidth: true
                                                text: modelData.label + ": " + modelData.message
                                                color: modelData.severity === "error" ? window.danger : window.ink
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                    }
                                }
                                DfsButton {
                                    Layout.alignment: Qt.AlignRight
                                    text: "Start Tactical Game"
                                    enabled: (dfsMobile.fleetState.roster || []).length > 0
                                    onClicked: {
                                        dfsMobile.startBattle("")
                                        window.activePage = 2
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // TACTICAL ASSISTANT --------------------------------------------
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12
                    RowLayout {
                        Layout.fillWidth: true
                        SectionLabel {
                            text: dfsMobile.gameState.active ? dfsMobile.gameState.name : "Tactical Assistant"
                        }
                        MutedLabel {
                            text: dfsMobile.gameState.active
                                ? ("Turn " + dfsMobile.gameState.turn + " • " + dfsMobile.gameState.phase)
                                : "Build a fleet, then start a tactical game."
                        }
                        Item { Layout.fillWidth: true }
                        DfsButton {
                            text: "Start from Fleet"
                            visible: dfsMobile.gameState.active !== true
                            enabled: (dfsMobile.fleetState.roster || []).length > 0
                            onClicked: dfsMobile.startBattle("")
                        }
                        DfsButton {
                            text: "Next Turn"
                            visible: dfsMobile.gameState.active === true
                            onClicked: dfsMobile.advanceTurn()
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 12
                        Rectangle {
                            Layout.preferredWidth: 390
                            Layout.fillHeight: true
                            radius: 10
                            color: window.panel
                            border.color: window.border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                SectionLabel { text: "Units" }
                                ListView {
                                    id: unitList
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    spacing: 6
                                    model: dfsMobile.gameState.units || []
                                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                    delegate: ItemDelegate {
                                        required property var modelData
                                        width: unitList.width
                                        height: 78
                                        onClicked: dfsMobile.selectUnit(modelData.unitId)
                                        background: Rectangle {
                                            radius: 8
                                            color: modelData.destroyed ? "#f5e7e8" : "#f5f7f9"
                                            border.color: modelData.destroyed ? "#d6a9ad" : window.border
                                        }
                                        contentItem: Column {
                                            spacing: 3
                                            Label {
                                                width: parent.width
                                                text: modelData.name
                                                color: window.ink
                                                font.pixelSize: 16
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            Label {
                                                width: parent.width
                                                text: modelData.status + " • " + modelData.priority
                                                color: modelData.destroyed ? window.danger : window.muted
                                                font.pixelSize: 13
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 10
                            color: window.panel
                            border.color: window.border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                RowLayout {
                                    Layout.fillWidth: true
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label {
                                            text: dfsMobile.selectedUnit.name || "Select a unit"
                                            color: window.ink
                                            font.pixelSize: 25
                                            font.weight: Font.Bold
                                        }
                                        MutedLabel {
                                            text: dfsMobile.selectedUnit.unitId
                                                ? (dfsMobile.selectedUnit.platformName + " • " + dfsMobile.selectedUnit.status)
                                                : "Tap a unit to manage its live game state."
                                        }
                                    }
                                    DfsButton {
                                        visible: dfsMobile.selectedUnit.unitId !== undefined
                                            && dfsMobile.selectedUnit.unitId !== ""
                                        text: dfsMobile.selectedUnit.destroyed ? "Restore Unit" : "Mark Destroyed"
                                        onClicked: dfsMobile.setDestroyed(
                                            dfsMobile.selectedUnit.unitId,
                                            !dfsMobile.selectedUnit.destroyed
                                        )
                                    }
                                }

                                Flickable {
                                    id: tacticalFlick
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    contentWidth: width
                                    contentHeight: tacticalColumn.implicitHeight
                                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                                    ColumnLayout {
                                        id: tacticalColumn
                                        width: tacticalFlick.width
                                        spacing: 10
                                        RowLayout {
                                            Layout.fillWidth: true
                                            TrackCard {
                                                Layout.fillWidth: true
                                                caption: "Damage"
                                                track: dfsMobile.selectedUnit.damage || ({})
                                                unitId: dfsMobile.selectedUnit.unitId || ""
                                                trackName: "damage"
                                            }
                                            TrackCard {
                                                Layout.fillWidth: true
                                                caption: "Crew"
                                                track: dfsMobile.selectedUnit.crew || ({})
                                                unitId: dfsMobile.selectedUnit.unitId || ""
                                                trackName: "crew"
                                            }
                                            TrackCard {
                                                Layout.fillWidth: true
                                                caption: "Shields"
                                                track: dfsMobile.selectedUnit.shields || ({})
                                                unitId: dfsMobile.selectedUnit.unitId || ""
                                                trackName: "shields"
                                            }
                                        }
                                        Flow {
                                            Layout.fillWidth: true
                                            spacing: 8
                                            StatTile { caption: "Speed"; value: dfsMobile.selectedUnit.speed }
                                            StatTile { caption: "Turn"; value: dfsMobile.selectedUnit.turn }
                                            StatTile { caption: "Hull"; value: dfsMobile.selectedUnit.hull }
                                            StatTile { caption: "Troops"; value: dfsMobile.selectedUnit.troops }
                                        }
                                        SectionLabel { text: "Weapons" }
                                        Repeater {
                                            model: dfsMobile.selectedUnit.weapons || []
                                            delegate: Rectangle {
                                                required property var modelData
                                                Layout.fillWidth: true
                                                implicitHeight: 65
                                                radius: 7
                                                color: modelData.status === "Operational" ? "#f6f8fa" : "#f6ecec"
                                                border.color: window.border
                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.margins: 9
                                                    Label {
                                                        Layout.fillWidth: true
                                                        text: modelData.arc + " • " + modelData.name
                                                        color: window.ink
                                                        font.pixelSize: 15
                                                        font.weight: Font.DemiBold
                                                        elide: Text.ElideRight
                                                    }
                                                    MutedLabel {
                                                        text: "R " + modelData.range + " • AD " + modelData.attackDice
                                                    }
                                                }
                                            }
                                        }
                                        SectionLabel { text: "Traits" }
                                        Label {
                                            Layout.fillWidth: true
                                            text: {
                                                var values = dfsMobile.selectedUnit.traits || []
                                                var names = []
                                                for (var i = 0; i < values.length; ++i)
                                                    names.push(values[i].name)
                                                return names.length ? names.join(", ") : "None"
                                            }
                                            color: window.ink
                                            font.pixelSize: 15
                                            wrapMode: Text.WordWrap
                                        }
                                        Item { Layout.preferredHeight: 12 }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // RULES CODEX ----------------------------------------------------
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12
                    SectionLabel { text: "Rules Codex" }
                    MutedLabel { text: "Search the same rule text used by DFS desktop and Tactical Assistant." }
                    RowLayout {
                        Layout.fillWidth: true
                        TextField {
                            id: rulesSearch
                            Layout.fillWidth: true
                            implicitHeight: 50
                            placeholderText: "Try Adaptive Armour, Interceptors, Beam, or Special Action"
                            onAccepted: dfsMobile.searchRules(text)
                        }
                        DfsButton {
                            text: "Search Rules"
                            enabled: rulesSearch.text.trim().length > 0
                            onClicked: dfsMobile.searchRules(rulesSearch.text)
                        }
                    }
                    ListView {
                        id: rulesList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 10
                        model: dfsMobile.rules
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: Rectangle {
                            required property var modelData
                            width: rulesList.width
                            height: ruleColumn.implicitHeight + 26
                            radius: 10
                            color: window.panel
                            border.color: window.border
                            ColumnLayout {
                                id: ruleColumn
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 13
                                spacing: 6
                                RowLayout {
                                    Layout.fillWidth: true
                                    Label {
                                        text: modelData.title
                                        color: window.ink
                                        font.pixelSize: 20
                                        font.weight: Font.Bold
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: modelData.category
                                        color: window.gold
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: modelData.text
                                    color: window.ink
                                    font.pixelSize: 15
                                    wrapMode: Text.WordWrap
                                }
                                MutedLabel {
                                    Layout.fillWidth: true
                                    text: modelData.source
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: errorRow.implicitHeight + 20
        visible: dfsMobile.error.length > 0
        color: "#8f2f38"
        z: 100
        RowLayout {
            id: errorRow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: 12
            Label {
                Layout.fillWidth: true
                text: dfsMobile.error
                color: "white"
                font.pixelSize: 15
                wrapMode: Text.WordWrap
            }
            DfsButton { text: "Dismiss"; onClicked: dfsMobile.clearError() }
        }
    }

    Component.onCompleted: {
        if (dfsMobile.factions.length > 0) {
            dfsMobile.loadFleetLists(dfsMobile.factions[0].id)
        }
    }
}
