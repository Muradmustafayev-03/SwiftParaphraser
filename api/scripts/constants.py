BUILT_IN_TYPES = ['CVarArg', 'RangeReplaceableCollection', 'Character', 'SignedInteger', 'Comparable', 'RandomAccessCollection', 'ExpressibleByUnicodeScalarLiteral', 'ClosedRange', 'BidirectionalCollection', 'AnyHashable', 'SIMD16', 'ExpressibleByFloatLiteral', 'OpaquePointer', 'SIMD8Storage', 'LosslessStringConvertible', 'AutoreleasingUnsafeMutablePointer', 'CustomStringConvertible', 'ExpressibleByStringLiteral', 'CustomReflectable', 'Numeric', 'Tuple', 'MemoryLayout', 'ExpressibleByExtendedGraphemeClusterLiteral', 'FixedWidthInteger', 'Array', 'Range', 'ExpressibleByStringInterpolation', 'SIMD3', 'UInt', 'BinaryInteger', 'Void', 'SIMD4', 'MutableCollection', 'FloatingPoint', 'Float16', 'CustomDebugStringConvertible', 'Any', 'ExpressibleByBooleanLiteral', 'ExpressibleByNilLiteral', 'Hashable', 'SIMD4Storage', 'Float', 'UnsafeRawPointer', 'ExpressibleByArrayLiteral', 'UnsafePointer', 'Collection', 'RawRepresentable', 'SIMD16Storage', 'UnsafeMutableRawPointer', 'Encodable', 'AnyObject', 'Error', 'BinaryFloatingPoint', 'StaticString', 'AnyClass', 'SIMD8', 'Double', 'Equatable', 'ExpressibleByTupleLiteral', 'ExpressibleByIntegerLiteral', 'Decodable', 'Int', 'Bool', 'Self', 'ExpressibleByDictionaryLiteral', 'StringProtocol', 'String', 'UnsafeMutablePointer', 'KeyPath', 'UnsignedInteger', 'Set', 'SignedNumeric', 'Dictionary', 'SIMD2Storage', 'SIMD', 'Mirror', 'Strideable', 'IntegerArithmetic', 'Never', 'Optional', 'Boolean', 'IteratorProtocol', 'SIMD2', 'ObjectIdentifier', 'Sequence', 'Float80']

SYSTEM_FRAMEWORK_PREFIXES = [
    "UI",   # UIKit
    "NS",   # Foundation
    "CG",   # Core Graphics
    "MK",   # MapKit
    "WK",   # WatchKit
    "SCN",  # SceneKit
    "AV",   # AVFoundation
    "CN",   # Contacts
    "CK",   # CloudKit
    "MP",   # MediaPlayer
    "MF",   # MessageUI
    "CL",   # Core Location
    "SK",   # StoreKit
    "EK",   # EventKit
    "MTL",  # Metal
    "GK",   # GameKit
    "AR",   # ARKit
    "PDF",  # PDFKit
    "VN",   # Vision
    "SCN",  # SceneKit
    "PK",  # PassKit
    "AS",  # AuthenticationServices
    "CM",  # CoreMotion
    "HMC",  # HomeKit
    "WC",  # WatchConnectivity
    "HM",  # HealthKit
    "UN",  # UserNotifications
    "LA",  # LocalAuthentication
    "VN",  # Vision
    "WK",  # WatchKit
    "WC",  # WatchConnectivity
    "MP",  # MediaPlayer
    "MTK",  # MetalKit
    "VN",  # Vision
    "HK",  # HealthKit
    "UN",  # UserNotifications
]

ABBREVIATIONS = {
    "VC": "ViewController",
    "VM": "ViewModel",
    "API": "ApplicationProgrammingInterface",
    "HTTP": "HyperTextTransferProtocol",
    "URL": "UniformResourceLocator",
    "JSON": "JavaScriptObjectNotation",
    "ID": "Identifier",
    "HTML": "HyperTextMarkupLanguage",
    "UI": "UserInterface",
    "SDK": "SoftwareDevelopmentKit",
    "DB": "Database",
    "GUI": "GraphicalUserInterface",
    "XML": "ExtensibleMarkupLanguage",
    "CPU": "CentralProcessingUnit",
    "RAM": "RandomAccessMemory",
    "GPU": "GraphicsProcessingUnit",
    "IDE": "IntegratedDevelopmentEnvironment",
    "NS": "NextStep",
    "RGBA": "RedGreenBlueAlpha",
    "TCP": "TransmissionControlProtocol",
    "UDP": "UserDatagramProtocol",
    "ASCII": "AmericanStandardCodeForInformationInterchange",
    "HTTPS": "HyperTextTransferProtocolSecure",
    "LAN": "LocalAreaNetwork",
    "WLAN": "WirelessLocalAreaNetwork",
    "CSS": "CascadingStyleSheets",
    "MVC": "ModelViewController",
    "MVVM": "ModelViewViewModel",
    "VIPER": "ViewInteractorPresenterEntityRouter",
    "RxSwift": "ReactiveSwift",
    "CSV": "CommaSeparatedValues",
    "IB": "InterfaceBuilder",
    "XIB": "XMLInterfaceBuilder",
    "FPS": "FramesPerSecond",
    "SSL": "SecureSocketsLayer",
    "TLS": "TransportLayerSecurity",
    "OOP": "ObjectOrientedProgramming",
    "JWT": "JSONWebToken",
    "ORM": "ObjectRelationalMapping",
    "CLI": "CommandLineInterface",
    "QA": "QualityAssurance",
    "UX": "UserExperience",
    "REST": "RepresentationalStateTransfer",
    "TV": "TableView",
    "BG": "Background",
    "FG": "Foreground",
    "CIDR": "ClasslessInter-DomainRouting",
    "DNS": "DomainNameSystem",
    "FTP": "FileTransferProtocol",
    "SSH": "SecureShell",
    "VPN": "VirtualPrivateNetwork",
    "WAN": "WideAreaNetwork",
    "GCD": "GrandCentralDispatch",
    "NST": "NextStepTechnology",
    "XMLRPC": "XMLRemoteProcedureCall",
    "JSONRPC": "JSONRemoteProcedureCall",
    "SQL": "StructuredQueryLanguage",
    "CRUD": "CreateReadUpdateDelete",
    "CI": "ContinuousIntegration",
    "CD": "ContinuousDelivery",
    "VCS": "VersionControlSystem",
    "SCM": "SourceCodeManagement",
    "iOS": "iPhoneOperatingSystem",
    "macOS": "MacintoshOperatingSystem",
    "OSX": "OperatingSystemX",
}


ADJECTIVES = ['My', 'New', 'Alternative', 'Custom', 'Awesome', 'Cool', 'Nice',
              'Different', 'Unique', 'Special', 'Advanced', 'Modern', 'Simple', 'Basic',
              'Swift', 'Fancy', 'Other', 'Another', 'Top', 'Variant', 'Adapted', 'Customized',
              'Personalized', 'Personal', 'Private', 'Public', 'Open', 'Closed', 'Internal',
              'External', 'Global', 'Local', 'Static', 'Dynamic', 'Abstract', 'Final', 'Alt']


VERBS = ['Do', 'Make', 'Create', 'Build', 'Generate', 'Construct', 'Compose', 'Form', 'Develop',
         'Get', 'Fetch', 'Obtain', 'Acquire', 'Receive', 'Return', 'Provide', 'Give', 'Add']


ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
