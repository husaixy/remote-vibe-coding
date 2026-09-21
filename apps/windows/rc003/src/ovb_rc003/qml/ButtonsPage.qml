import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import OvbRc003Settings 1.0

Item {
    id: root
    property var tokens
    readonly property real photoAspectRatio: 1030 / 508

    function openShortcutRecorder(buttonId, rowIndex, isMic, trigger) {
        shortcutRecorder.buttonId = buttonId
        shortcutRecorder.rowIndex = rowIndex
        shortcutRecorder.isMic = isMic
        shortcutRecorder.trigger = trigger || "single_click"
        shortcutRecorder.previewText = qsTr("请按下要映射的真实按键")
        shortcutRecorder.open()
    }

    Dialog {
        id: shortcutRecorder
        objectName: "shortcutRecorderDialog"
        modal: true
        anchors.centerIn: parent
        width: 440
        title: qsTr("录制自定义快捷键")
        standardButtons: Dialog.Cancel
        property string buttonId: ""
        property int rowIndex: -1
        property bool isMic: false
        property string trigger: "single_click"
        property string previewText: ""
        function commitShortcut(chord) {
            previewText = chord
            if (isMic)
                SettingsController.hotkeyText = chord
            else if (trigger === "single_click")
                ButtonMappingModel.setActionTextAt(rowIndex, chord)
            else
                ButtonMappingModel.setSecondaryActionTextAt(rowIndex, trigger, chord)
            close()
        }
        onOpened: { captureArea.forceActiveFocus(); SettingsController.startHotkeyCapture() }
        onClosed: SettingsController.stopHotkeyCapture()
        Connections {
            target: SettingsController
            function onHotkeyCaptured(chord) { if (shortcutRecorder.visible) shortcutRecorder.commitShortcut(chord) }
            function onHotkeyCaptureError(message) { if (shortcutRecorder.visible) shortcutRecorder.previewText = message }
        }
        contentItem: FocusScope {
            id: captureArea
            implicitHeight: 150
            focus: true
            ColumnLayout {
                anchors.fill: parent
                spacing: tokens.spacingMedium
                Label { Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; text: shortcutRecorder.previewText; font.pixelSize: tokens.fontSizeTitle; font.weight: Font.Medium; color: tokens.accent }
                Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; text: qsTr("请直接按下要映射的真实按键；左右修饰键会分别记录。录制期间不会执行该快捷键。"); color: tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
            }
        }
    }

    RowLayout {
        id: rc003MappingLayout
        objectName: "rc003MappingLayout"
        visible: SettingsController.isXiaomiRemoteDevice
        anchors.fill: parent
        anchors.leftMargin: 34
        anchors.rightMargin: 34
        anchors.topMargin: 26
        anchors.bottomMargin: 20
        spacing: 36

        ColumnLayout {
            Layout.preferredWidth: 260
            Layout.minimumWidth: 230
            Layout.fillHeight: true
            spacing: tokens.spacingSmall
            Rectangle {
                id: photoFrame
                Layout.preferredWidth: 230
                Layout.preferredHeight: 230 * root.photoAspectRatio
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                radius: tokens.cornerRadiusSmall
                color: tokens.surfaceSubtle
                border.color: tokens.border
                border.width: 1
                clip: true
                Image {
                    id: photoImage
                    objectName: "photoImage"
                    anchors.fill: parent
                    anchors.margins: 10
                    fillMode: Image.PreserveAspectFit
                    source: SettingsController.photoAvailable ? SettingsController.photoSource : ""
                    visible: SettingsController.photoAvailable
                    smooth: true
                    asynchronous: true
                }
                Label { anchors.centerIn: parent; width: parent.width - 24; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; visible: !SettingsController.photoAvailable; text: qsTr("实物图资源缺失"); color: tokens.textSecondary }
                Repeater {
                    model: ButtonMappingModel
                    delegate: Item {
                        id: hotspot
                        objectName: "photoHotspot_" + buttonId
                        required property string buttonId
                        required property string displayName
                        required property real hotspotX
                        required property real hotspotY
                        required property real hotspotWidth
                        required property real hotspotHeight
                        required property bool isSelected
                        required property bool isVoice
                        readonly property real paintedW: photoImage.paintedWidth
                        readonly property real paintedH: photoImage.paintedHeight
                        readonly property real offsetX: photoImage.x + (photoImage.width - paintedW) / 2
                        readonly property real offsetY: photoImage.y + (photoImage.height - paintedH) / 2
                        width: hotspotWidth * paintedW
                        height: hotspotHeight * paintedH
                        x: offsetX + hotspotX * paintedW - width / 2
                        y: offsetY + hotspotY * paintedH - height / 2
                        visible: SettingsController.photoAvailable
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: displayName
                        Rectangle {
                            anchors.fill: parent
                            radius: height / 2
                            color: hotspot.isSelected ? Qt.rgba(tokens.accent.r, tokens.accent.g, tokens.accent.b, 0.16) : (hoverHandler.hovered ? Qt.rgba(tokens.accent.r, tokens.accent.g, tokens.accent.b, 0.08) : "transparent")
                            border.width: hotspot.isSelected ? 2 : (hotspot.activeFocus ? 1 : 0)
                            border.color: hotspot.isVoice ? tokens.voiceAccent : tokens.accent
                        }
                        HoverHandler { id: hoverHandler }
                        TapHandler { onTapped: SettingsController.selectButton(hotspot.buttonId) }
                        Keys.onReturnPressed: SettingsController.selectButton(hotspot.buttonId)
                        Keys.onSpacePressed: SettingsController.selectButton(hotspot.buttonId)
                    }
                }
            }
            Label { Layout.alignment: Qt.AlignHCenter; text: qsTr("小米遥控器 2 Pro · RC003"); font.weight: Font.Medium; color: tokens.textPrimary }
            Button {
                id: detectRealKeyButton
                objectName: "detectRealKeyButton"
                Layout.preferredWidth: 230
                Layout.alignment: Qt.AlignHCenter
                text: SettingsController.keyDetectionActive ? qsTr("停止检测") : qsTr("检测真实按键")
                highlighted: SettingsController.keyDetectionActive
                onClicked: SettingsController.keyDetectionActive ? SettingsController.stopKeyDetection() : SettingsController.startKeyDetection()
                Accessible.name: qsTr("检测真实遥控器按键")
            }
            Label { Layout.preferredWidth: 230; Layout.alignment: Qt.AlignHCenter; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; text: SettingsController.keyDetectionText; color: SettingsController.keyDetectionActive ? tokens.accent : tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: tokens.spacingMedium
            Label { text: qsTr("按键映射"); font.pixelSize: tokens.fontSizePageTitle; font.weight: Font.Medium; color: tokens.textPrimary }
            Label { text: qsTr("点击遥控器上的按键，设置对应动作"); color: tokens.textSecondary; font.pixelSize: tokens.fontSizeBody }
            Rectangle { Layout.fillWidth: true; height: 1; color: tokens.border }
            Label { Layout.fillWidth: true; visible: text.length > 0; wrapMode: Text.WordWrap; text: SettingsController.errorMessage; color: tokens.errorColor; font.pixelSize: tokens.fontSizeSmall }
            Label { Layout.fillWidth: true; visible: text.length > 0 && SettingsController.errorMessage.length === 0; wrapMode: Text.WordWrap; text: SettingsController.statusMessage; color: tokens.successColor; font.pixelSize: tokens.fontSizeSmall }

            GridView {
                id: mappingList
                objectName: "mappingList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: ButtonMappingModel
                cellWidth: width
                cellHeight: height
                currentIndex: ButtonMappingModel.indexOfButton(SettingsController.selectedButtonId)
                highlightFollowsCurrentItem: true
                onCurrentIndexChanged: positionViewAtIndex(currentIndex, GridView.Contain)
                delegate: Item {
                    id: mappingRow
                    required property int index
                    required property string buttonId
                    required property string displayName
                    required property string hidUsage
                    required property string actionText
                    required property string doubleClickText
                    required property string longPressText
                    required property bool isMic
                    required property bool isSelected
                    width: mappingList.cellWidth
                    height: mappingList.cellHeight
                    onActionTextChanged: actionCombo.editText = actionText
                    onDoubleClickTextChanged: doubleActionCombo.editText = doubleClickText
                    onLongPressTextChanged: longActionCombo.editText = longPressText

                    ColumnLayout {
                        id: rowContent
                        anchors.fill: parent
                        spacing: tokens.spacingMedium
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: tokens.spacingSmall
                            Rectangle {
                                width: 42; height: 42; radius: 21; color: tokens.surface; border.color: tokens.border
                                Label { anchors.centerIn: parent; text: mappingRow.isMic ? qsTr("声") : qsTr("键"); font.weight: Font.Medium; color: tokens.textPrimary }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 0
                                Label { text: mappingRow.displayName; font.pixelSize: tokens.fontSizeTitle; font.weight: Font.Medium; color: tokens.textPrimary }
                                Label { text: mappingRow.hidUsage; color: tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
                            }
                            Rectangle {
                                visible: mappingRow.isSelected
                                implicitWidth: selectedLabel.implicitWidth + 18; implicitHeight: 28; radius: 14; color: tokens.accentSoft
                                Label { id: selectedLabel; anchors.centerIn: parent; text: qsTr("已选中"); color: tokens.accent; font.pixelSize: tokens.fontSizeSmall; font.weight: Font.Medium }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: mappingForm.implicitHeight + 28
                            radius: tokens.cornerRadiusLarge
                            color: tokens.surfaceSubtle
                            border.color: tokens.border
                            border.width: 1
                            ColumnLayout {
                                id: mappingForm
                                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 14
                                spacing: 0
                                RowLayout {
                                    Layout.fillWidth: true; Layout.preferredHeight: 58; spacing: tokens.spacingMedium
                                    Label { Layout.preferredWidth: 80; text: mappingRow.isMic ? qsTr("语音快捷键") : qsTr("单击"); font.weight: Font.Medium }
                                    ComboBox {
                                        id: actionCombo
                                        objectName: "actionCombo_" + mappingRow.buttonId
                                        visible: !mappingRow.isMic
                                        Layout.fillWidth: true
                                        editable: true
                                        model: SettingsController.presetActionOptions
                                        Accessible.name: mappingRow.displayName
                                        property bool _initialized: false
                                        Component.onCompleted: { editText = mappingRow.actionText; _initialized = true }
                                        onEditTextChanged: { if (_initialized) ButtonMappingModel.setActionTextAt(mappingRow.index, editText) }
                                        onAccepted: ButtonMappingModel.setActionTextAt(mappingRow.index, editText)
                                        onActivated: ButtonMappingModel.setActionTextAt(mappingRow.index, currentText)
                                    }
                                    TextField {
                                        id: voiceHotkeyField
                                        objectName: "voiceHotkeyField_" + mappingRow.buttonId
                                        visible: mappingRow.isMic
                                        Layout.fillWidth: true
                                        text: SettingsController.hotkeyText
                                        placeholderText: qsTr("免按住 ralt+space；长按 ralt")
                                        selectByMouse: true
                                        onEditingFinished: SettingsController.hotkeyText = text
                                        Accessible.name: qsTr("语音键组合键")
                                    }
                                    Button { objectName: "recordShortcut_" + mappingRow.buttonId; text: qsTr("录制"); onClicked: root.openShortcutRecorder(mappingRow.buttonId, mappingRow.index, mappingRow.isMic, "single_click") }
                                }
                                Rectangle { Layout.fillWidth: true; height: 1; color: tokens.border; visible: !mappingRow.isMic }
                                RowLayout {
                                    Layout.fillWidth: true; Layout.preferredHeight: 58; visible: !mappingRow.isMic; spacing: tokens.spacingMedium
                                    Label { Layout.preferredWidth: 80; text: qsTr("双击"); font.weight: Font.Medium }
                                    ComboBox {
                                        id: doubleActionCombo
                                        objectName: "doubleActionCombo_" + mappingRow.buttonId
                                        Layout.fillWidth: true
                                        editable: true
                                        model: SettingsController.presetActionOptions
                                        property bool _initialized: false
                                        Component.onCompleted: { editText = mappingRow.doubleClickText; _initialized = true }
                                        onEditTextChanged: { if (_initialized) ButtonMappingModel.setSecondaryActionTextAt(mappingRow.index, "double_click", editText) }
                                        onAccepted: ButtonMappingModel.setSecondaryActionTextAt(mappingRow.index, "double_click", editText)
                                        onActivated: ButtonMappingModel.setSecondaryActionTextAt(mappingRow.index, "double_click", currentText)
                                    }
                                    Button { objectName: "recordDoubleShortcut_" + mappingRow.buttonId; text: qsTr("录制"); onClicked: root.openShortcutRecorder(mappingRow.buttonId, mappingRow.index, false, "double_click") }
                                }
                                Rectangle { Layout.fillWidth: true; height: 1; color: tokens.border; visible: !mappingRow.isMic }
                                RowLayout {
                                    Layout.fillWidth: true; Layout.preferredHeight: 58; visible: !mappingRow.isMic; spacing: tokens.spacingMedium
                                    Label { Layout.preferredWidth: 80; text: qsTr("长按"); font.weight: Font.Medium }
                                    ComboBox {
                                        id: longActionCombo
                                        objectName: "longActionCombo_" + mappingRow.buttonId
                                        Layout.fillWidth: true
                                        editable: true
                                        model: SettingsController.presetActionOptions
                                        property bool _initialized: false
                                        Component.onCompleted: { editText = mappingRow.longPressText; _initialized = true }
                                        onEditTextChanged: { if (_initialized) ButtonMappingModel.setSecondaryActionTextAt(mappingRow.index, "long_press", editText) }
                                        onAccepted: ButtonMappingModel.setSecondaryActionTextAt(mappingRow.index, "long_press", editText)
                                        onActivated: ButtonMappingModel.setSecondaryActionTextAt(mappingRow.index, "long_press", currentText)
                                    }
                                    Button { objectName: "recordLongShortcut_" + mappingRow.buttonId; text: qsTr("录制"); onClicked: root.openShortcutRecorder(mappingRow.buttonId, mappingRow.index, false, "long_press") }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: codexHelp.implicitHeight + 28
                            radius: tokens.cornerRadiusLarge
                            color: tokens.accentSoft
                            border.color: Qt.rgba(tokens.accent.r, tokens.accent.g, tokens.accent.b, 0.32)
                            border.width: 1
                            ColumnLayout {
                                id: codexHelp
                                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 14
                                spacing: 5
                                Label { text: qsTr("首次使用：在 Codex 中绑定快捷键"); font.weight: Font.Medium; color: tokens.textPrimary }
                                Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: qsTr("聚焦主聊天：Ctrl+Alt+Shift+F12。Codex Micro 预设还会使用 F1–F11、P 和 Enter，均带 Ctrl+Alt+Shift；请按 README 表格绑定对应命令。"); color: tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
                                Label { text: qsTr("快捷键需要手动配置一次；本程序不会读取或修改 Codex 私有设置。"); color: tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
                            }
                        }
                        Item { Layout.fillHeight: true }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignRight
                spacing: tokens.spacingSmall
                Label { Layout.fillWidth: true; text: qsTr("选择实物按键后编辑；自定义组合键可直接输入或录制。"); color: tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
                Button { id: codexPresetButton; objectName: "codexPresetButton"; text: qsTr("应用 Codex 预设"); onClicked: SettingsController.applyCodexMicroPreset() }
                Button { text: qsTr("恢复默认"); onClicked: SettingsController.restoreDefaults() }
                Button { id: saveMappingButton; objectName: "saveMappingButton"; text: qsTr("保存映射"); highlighted: true; onClicked: SettingsController.saveSettings() }
            }
        }
    }

    RowLayout {
        id: djiControlLayout
        objectName: "djiControlLayout"
        visible: SettingsController.isDjiMic2Device
        anchors.fill: parent
        anchors.margins: 34
        spacing: 36
        Rectangle {
            Layout.preferredWidth: 260; Layout.fillHeight: true; radius: tokens.cornerRadiusLarge; color: tokens.surfaceSubtle; border.color: tokens.border
            ColumnLayout {
                anchors.centerIn: parent; spacing: tokens.spacingMedium
                Rectangle { Layout.alignment: Qt.AlignHCenter; width: 110; height: 250; radius: 12; color: tokens.background; border.color: tokens.border; Label { anchors.centerIn: parent; text: qsTr("DJI\nMIC 2"); horizontalAlignment: Text.AlignHCenter; font.weight: Font.Medium } }
                Label { Layout.alignment: Qt.AlignHCenter; text: qsTr("系统录音输入设备"); color: tokens.textSecondary }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: tokens.spacingMedium
            Label { text: qsTr("DJI Mic 2 设备控制"); font.pixelSize: tokens.fontSizePageTitle; font.weight: Font.Medium }
            Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: qsTr("当前可自定义映射：0。只有在 Windows 捕获到实体键独立输入事件后，才会开放映射。"); color: tokens.textSecondary }
            Rectangle { Layout.fillWidth: true; height: 1; color: tokens.border }
            Repeater {
                model: SettingsController.djiControlRows
                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: djiRow.implicitHeight + 24; radius: tokens.cornerRadiusSmall; color: tokens.surfaceSubtle; border.color: tokens.border
                    RowLayout {
                        id: djiRow; anchors.fill: parent; anchors.margins: 12; spacing: tokens.spacingMedium
                        Label { Layout.preferredWidth: 72; text: modelData.name; font.weight: Font.Medium }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: modelData.behavior }
                            Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: modelData.mapping; color: tokens.textSecondary; font.pixelSize: tokens.fontSizeSmall }
                        }
                        Label { text: qsTr("硬件内置"); color: tokens.disabledText; font.pixelSize: tokens.fontSizeSmall }
                    }
                }
            }
            Item { Layout.fillHeight: true }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                Button { text: qsTr("重新检测麦克风"); onClicked: SettingsController.refreshDjiMicStatus() }
                Button { text: qsTr("打开 Windows 声音输入设置"); highlighted: true; onClicked: SettingsController.openSoundSettings() }
            }
        }
    }
}
