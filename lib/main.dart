import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera_platform_interface/camera_platform_interface.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:window_manager/window_manager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await windowManager.ensureInitialized();

  WindowOptions windowOptions = const WindowOptions(
    size: Size(400, 700),
    minimumSize: Size(350, 600),
    center: true,
    backgroundColor: Colors.transparent,
    skipTaskbar: false,
    titleBarStyle: TitleBarStyle.hidden, // Removes the clunky Windows top window frame
  );

  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.setAlwaysOnTop(true); // Puts the window on top of Google Meet/Zoom
    await windowManager.show();
    await windowManager.focus();
  });

  runApp(const SignSpeakApp());
}

class SignSpeakApp extends StatelessWidget {
  const SignSpeakApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SignSpeak AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(brightness: Brightness.dark, useMaterial3: true),
      home: const RoleSelectionPage(),
    );
  }
}

/// --- PAGE 1: USER ROLE SELECTION PANEL (WITH DROPDOWN) ---
class RoleSelectionPage extends StatefulWidget {
  const RoleSelectionPage({super.key});

  @override
  State<RoleSelectionPage> createState() => _RoleSelectionPageState();
}

class _RoleSelectionPageState extends State<RoleSelectionPage> {
  String _selectedRole = 'Deaf / Mute (Video to Text)';
  final List<String> _roles = [
    'Deaf / Mute (Video to Text)',
    'Normal Hearing (Audio to Text)'
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      body: SafeArea(
        child: Column(
          children: [
            const WindowDragHandle(),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "SignSpeak AI",
                      style: GoogleFonts.spaceGrotesk(
                        fontSize: 36,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFFFFD700),
                      ),
                    ),
                    Text(
                      "Select your profile execution mode below:",
                      style: GoogleFonts.inter(fontSize: 14, color: Colors.white54),
                    ),
                    const SizedBox(height: 32),
                    
                    // DROPDOWN SELECTION SYSTEM
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E1E1E),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _selectedRole,
                          isExpanded: true,
                          dropdownColor: const Color(0xFF1E1E1E),
                          items: _roles.map((String role) {
                            return DropdownMenuItem<String>(
                              value: role,
                              child: Text(role, style: GoogleFonts.inter(fontSize: 14)),
                            );
                          }).toList(),
                          onChanged: (String? newValue) {
                            if (newValue != null) {
                              setState(() {
                                _selectedRole = newValue;
                              });
                            }
                          },
                        ),
                      ),
                    ),
                    const SizedBox(height: 40),
                    
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFFFD700),
                        foregroundColor: Colors.black,
                        minimumSize: const Size(double.infinity, 54),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () {
                        if (_selectedRole.contains('Video to Text')) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const VideoToTextWorkspace()),
                          );
                        } else {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const AudioToTextWorkspace()),
                          );
                        }
                      },
                      child: Text(
                        "LAUNCH INTERFACE",
                        style: GoogleFonts.inter(fontWeight: FontWeight.bold, letterSpacing: 1.1),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// --- PIPELINE 1: DEAF/MUTE WORKSPACE (VIDEO TO TEXT) ---
class VideoToTextWorkspace extends StatefulWidget {
  const VideoToTextWorkspace({super.key});

  @override
  State<VideoToTextWorkspace> createState() => _VideoToTextWorkspaceState();
}

class _VideoToTextWorkspaceState extends State<VideoToTextWorkspace> {
  final CameraPlatform cameraPlatform = CameraPlatform.instance;
  int _textureId = -1;
  bool _isCameraInitialized = false;
  WebSocketChannel? _channel;
  Timer? _frameTimer;
  bool _isTranslating = false;
  String _translatedSubtitle = "READY TO STREAM FRAMES";

  @override
  void initState() {
    super.initState();
    _bootCamera();
  }

  Future<void> _bootCamera() async {
    try {
      final cameras = await cameraPlatform.availableCameras();
      if (cameras.isEmpty) return;
      _textureId = await cameraPlatform.createCamera(cameras.first, ResolutionPreset.medium, enableAudio: false);
      await cameraPlatform.initializeCamera(_textureId);
      if (mounted) setState(() => _isCameraInitialized = true);
    } catch (e) {
      print("Camera failed: $e");
    }
  }

  void _togglePipeline() {
    if (_isTranslating) {
      _frameTimer?.cancel();
      _channel?.sink.close();
      setState(() {
        _isTranslating = false;
        _translatedSubtitle = "STREAM PIPELINE STOPPED";
      });
    } else {
      _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:8000/ws/stream'));
      setState(() {
        _isTranslating = true;
        _translatedSubtitle = "STREAMING ACTIVE...";
      });

      _channel!.stream.listen(
        (msg) {
          if (mounted) setState(() => _translatedSubtitle = msg.toString());
        },
        onError: (err) => _togglePipeline(),
        onDone: () => _togglePipeline(),
      );

      _frameTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) async {
        if (_channel != null && _isCameraInitialized) {
          try {
            XFile file = await cameraPlatform.takePicture(_textureId);
            Uint8List bytes = await file.readAsBytes();
            _channel!.sink.add(bytes);
          } catch (e) {
            print("Frame drop: $e");
          }
        }
      });
    }
  }

  @override
  void dispose() {
    _frameTimer?.cancel();
    _channel?.sink.close();
    if (_textureId != -1) cameraPlatform.dispose(_textureId);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: Column(
          children: [
            const WindowDragHandle(),
            Expanded(
              child: Container(
                color: const Color(0xFF121212).withOpacity(0.95),
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Expanded(
                      flex: 4,
                      child: Container(
                        width: double.infinity,
                        clipBehavior: Clip.antiAlias,
                        decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white12)),
                        child: _isCameraInitialized ? Texture(textureId: _textureId) : const Center(child: CircularProgressIndicator(color: Color(0xFFFFD700))),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      flex: 2,
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: const Color(0xFF1E1E1E), borderRadius: BorderRadius.circular(16)),
                        child: Center(
                          child: Text(_translatedSubtitle, textAlign: TextAlign.center, style: GoogleFonts.spaceGrotesk(fontSize: 22, fontWeight: FontWeight.bold, color: const Color(0xFFFFD700))),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: _isTranslating ? Colors.redAccent : const Color(0xFF1F1F1F), minimumSize: const Size(double.infinity, 50)),
                      onPressed: _togglePipeline,
                      child: Text(_isTranslating ? "STOP PIPELINE STREAM" : "START TRANSLATION"),
                    )
                  ],
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}

/// --- PIPELINE 2: HEARING USER WORKSPACE (AUDIO TO TEXT) ---
class AudioToTextWorkspace extends StatefulWidget {
  const AudioToTextWorkspace({super.key});

  @override
  State<AudioToTextWorkspace> createState() => _AudioToTextWorkspaceState();
}

class _AudioToTextWorkspaceState extends State<AudioToTextWorkspace> {
  bool _isListening = false;
  String _spokenSpeechOutput = "SPEECH STANDBY - TAP START TO LISTEN";
  WebSocketChannel? _audioChannel;

  void _toggleAudioPipeline() {
    if (_isListening) {
      _audioChannel?.sink.close();
      _audioChannel = null;
      setState(() {
        _isListening = false;
        _spokenSpeechOutput = "SPEECH PIPELINE STOPPED";
      });
    } else {
      _audioChannel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:8000/ws/audio'));
      setState(() {
        _isListening = true;
        _spokenSpeechOutput = "LISTENING TO MICROPHONE AUDIO STREAM...";
      });

      _audioChannel!.stream.listen(
        (incomingText) {
          if (mounted) {
            setState(() {
              _spokenSpeechOutput = incomingText.toString();
            });
          }
        }, 
        onError: (err) => _toggleAudioPipeline(), // FIXED: Corrected error parameters
        onDone: () => _toggleAudioPipeline()
      );
    }
  }

  @override
  void dispose() {
    _audioChannel?.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: Column(
          children: [
            const WindowDragHandle(),
            Expanded(
              child: Container(
                color: const Color(0xFF121212).withOpacity(0.95),
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      "Audio-to-Text Caption Engine",
                      style: GoogleFonts.spaceGrotesk(fontSize: 22, fontWeight: FontWeight.bold, color: const Color(0xFFFFD700)),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "Captures spoken voices from Google Meet and prints text captions below",
                      textAlign: TextAlign.center,
                      style: GoogleFonts.inter(fontSize: 12, color: Colors.white54),
                    ),
                    const SizedBox(height: 32),
                    Expanded(
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E1E1E),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.white12, width: 1.5)
                        ),
                        child: Center(
                          child: Text(
                            _spokenSpeechOutput,
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(
                              fontSize: 18, 
                              fontWeight: FontWeight.w500, 
                              color: _isListening ? const Color(0xFFFFD700) : Colors.white38
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _isListening ? Colors.redAccent : const Color(0xFF1F1F1F),
                        foregroundColor: Colors.white,
                        minimumSize: const Size(double.infinity, 54),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: _toggleAudioPipeline,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(_isListening ? Icons.mic : Icons.mic_none, size: 18),
                          const SizedBox(width: 10),
                          Text(
                            _isListening ? "STOP AUDIO CAPTURE" : "START AUDIO LISTENING",
                            style: GoogleFonts.inter(fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    )
                  ],
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}

/// --- REUSABLE COMPONENT: TOP DRAG HANDLE BAR ---
class WindowDragHandle extends StatelessWidget {
  const WindowDragHandle({super.key});

  @override
  Widget build(BuildContext context) {
    return DragToMoveArea(
      child: Container(
        height: 38,
        color: const Color(0xFF1A1A1A),
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text("SignSpeak Workspace", style: GoogleFonts.inter(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
            IconButton(
              icon: const Icon(Icons.close, color: Colors.white54, size: 14),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
              onPressed: () => windowManager.close(),
            ),
          ],
        ),
      ),
    );
  }
}