// Minimal, flat visual tokens shared by every settings page.
// Instantiated exactly once in main.qml and passed down to each page as a
// `tokens` property - deliberately NOT a pragma Singleton, so this stays a
// plain, implicitly-directory-imported QML type with no module/qmldir
// registration to keep correct under a frozen PyInstaller build.
import QtQuick

QtObject {
    id: tokens

    property color background: "#FFFFFF"
    property color surface: "#F8FAFC"
    property color surfaceSubtle: "#FBFCFE"
    property color textPrimary: "#18202B"
    property color textSecondary: "#667085"
    property color disabledText: "#98A2B3"
    property color accent: "#1677E8"
    property color accentSoft: "#EFF6FF"
    property color accentText: "#FFFFFF"
    property color border: "#E1E7EF"
    property color fieldBackground: "#FFFFFF"
    property color buttonBackground: "#FFFFFF"
    property color buttonText: textPrimary

    // Semantic colors: only ever used for a real state (a real save error,
    // a real save/launch success, the fixed identity of the mic hotspot) -
    // never decorative (XRBM-030 Design read: "错误/成功只用于真实状态").
    property color voiceAccent: "#F2914A"
    property color successColor: "#22875A"
    property color errorColor: "#C43D4B"

    property int cornerRadiusSmall: 6
    property int cornerRadiusLarge: 8

    property int spacingTiny: 4
    property int spacingSmall: 8
    property int spacingMedium: 12
    property int spacingLarge: 24

    property int fontSizeSmall: 12
    property int fontSizeBody: 14
    property int fontSizeTitle: 18
    property int fontSizePageTitle: 26
    property string fontFamily: "Microsoft YaHei UI"
}
